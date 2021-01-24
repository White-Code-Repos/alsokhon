from odoo import fields, models, api, _


class GoldFixingPositionWizard(models.TransientModel):
    _name = 'gold.fixing.position.wizard'
    _description = 'Gold Fixing Position Wizard'

    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')

    def action_confirm(self):
        account_moves = self.env['account.move'].search([('type_of_action', '=', 'fixed'),
                                                         ('journal_id.gold', '=', True),
                                                         ])
        # ('date', '>=', self.date_from),
        # ('date', '<=', self.date_to)

        account_move_lines = self.env['account.move.line'].search([('move_id', 'in', account_moves.ids),
                                                                   ('account_id.gold', '=', True),
                                                                   ('account_id.current_position', '=', True)]).sorted(
            lambda r: r.date)
        gold_position = self.env['gold.position'].sudo().search([])
        gold_capital = gold_position.gold_capital
        current_position = gold_position.current_position
        capital_difference = gold_position.capital_difference

        quantity_balance, amount_balance, values, all_values = 0, 0, 0, 0
        if len(account_move_lines) > 0:
            self.env['gold.fixing.position.report'].search([]).unlink()

        for rec in account_move_lines:
            bills = self.env['account.move'].search([
                ('name', '=', rec.ref.split()[0])])
            # ('date', '>=', self.date_from),
            #  ('date', '<=', self.date_to),
            pickings = self.env['stock.picking'].search([
                ('name', '=', rec.ref.split()[0])])
            # ('scheduled_date', '>=', self.date_from),
            #  ('scheduled_date', '<=', self.date_to),
            vals = {
                'date': rec.move_id.date,
                'name': rec.move_id.name,
                'quantity_in': rec.debit if rec.debit != 0.0 else 0.0,
                'quantity_out': rec.credit if rec.credit != 0.0 else 0.0,
                'rate_kilo': 0,
                'rate_gram': 0,
                'value': values,
                'quantity_balance': quantity_balance,
                'amount_balance': amount_balance,
                'amount_average': 0,
                'gold_capital': gold_capital,
                'current_position': current_position,
                'capital_difference': capital_difference,
            }

            quantity_balance += vals['quantity_in'] if vals['quantity_in'] != 0 else -1 * vals['quantity_out']

            # WH
            for pic in pickings:
                related_purchase_orders = self.env['purchase.order'].search([('name', '=', pic.origin)]).sorted(
                    lambda r: r.date_approve.date())

                related_sale_orders = self.env['sale.order'].search([('name', '=', pic.origin)]).sorted(
                    lambda r: r.date_order.date())

                related_pos_orders = self.env['pos.order']

                if 'POS' in pic.origin:
                    related_pos_orders = self.env['pos.order'].search([('name', '=', pic.origin.split()[2]),
                                                                       ('session_id', '=',
                                                                        self.env['pos.session'].search([('name', '=',
                                                                                                         pic.origin.split()[
                                                                                                             0])]).id)]).sorted(
                        lambda r: r.date_order.date())

                for pol in related_pos_orders:
                    vals['quantity_balance'] = quantity_balance

                    for s in pol.lines.filtered(lambda x: x.product_id.gold == True):
                        vals['rate_gram'] = s.gold_rate
                        vals['value'] = (s.gold_rate * vals['quantity_in']) if vals['quantity_in'] != 0 else (
                                s.gold_rate * vals['quantity_out'])
                    vals['rate_kilo'] = vals['rate_gram'] * 1000
                    all_values += vals['value']
                    values = (vals['rate_gram'] * vals['quantity_in']) if vals['quantity_in'] != 0 else (
                            vals['rate_gram'] * vals['quantity_out'])
                    vals['amount_balance'] = all_values if all_values != 0 else values
                    vals['amount_average'] = vals['amount_balance'] / vals['quantity_balance']

                for sal in related_sale_orders:
                    vals['rate_kilo'] = sal.gold_rate
                    vals['quantity_balance'] = quantity_balance

                    for s in sal.order_line.filtered(lambda x: x.product_id.gold == True):
                        vals['rate_gram'] = s.gold_rate
                        vals['value'] = (s.gold_rate * vals['quantity_in']) if vals['quantity_in'] != 0 else (
                                s.gold_rate * vals['quantity_out'])

                    all_values += vals['value']
                    values = (vals['rate_gram'] * vals['quantity_in']) if vals['quantity_in'] != 0 else (
                            vals['rate_gram'] * vals['quantity_out'])
                    vals['amount_balance'] = all_values if all_values != 0 else values
                    vals['amount_average'] = vals['amount_balance'] / vals['quantity_balance']

                for purs in related_purchase_orders:
                    vals['rate_kilo'] = purs.gold_rate
                    vals['quantity_balance'] = quantity_balance

                    for p in purs.order_line.filtered(lambda x: x.product_id.gold == True):
                        vals['rate_gram'] = p.gold_rate
                    values = (vals['rate_gram'] * vals['quantity_in']) if vals['quantity_in'] != 0 else (
                            vals['rate_gram'] * vals['quantity_out'])
                    all_values += values
                    vals['value'] = values
                    vals['amount_balance'] = all_values if all_values != 0 else values
                    vals['amount_average'] = vals['amount_balance'] / vals['quantity_balance']

            # Bills
            for line in bills:
                related_purchase_order = self.env['purchase.order'].search([('name', '=', line.invoice_origin)]).sorted(
                    lambda r: r.date_approve.date())

                for pur in related_purchase_order:
                    vals['rate_kilo'] = pur.gold_rate
                    vals['quantity_balance'] = quantity_balance

                    for n in pur.order_line.filtered(lambda x: x.product_id.gold == True):
                        vals['rate_gram'] = n.gold_rate

                    values = (vals['rate_gram'] * vals['quantity_in']) if vals['quantity_in'] != 0 else (
                            vals['rate_gram'] * vals['quantity_out'])
                    all_values = all_values + values
                    vals['value'] = values
                    vals['amount_balance'] = all_values if all_values != 0 else values
                    vals['amount_average'] = vals['amount_balance'] / vals['quantity_balance']

            self.env['gold.fixing.position.report'].create(vals)

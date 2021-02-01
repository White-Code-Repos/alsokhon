from odoo import api, fields, models, _


class GoldFixingPosition(models.TransientModel):
    _name = 'gold.fixing.position'
    _description = 'Gold Fixing Position'

    # date_from = fields.Date(string='Date From')
    # date_to = fields.Date(string='Date To')

    def print_gold_fixing_report(self):
        action = self.env.ref('gold_position.view_gold_position_action').read()[0]
        return action
        # data = {}
        # lines = []
        # account_moves = self.env['account.move'].search([('type_of_action', '=', 'fixed'),
        #                                                  ('journal_id.gold', '=', True),
        #                                                  ('date', '>=', self.date_from),
        #                                                  ('date', '<=', self.date_to)])
        #
        # account_move_lines = self.env['account.move.line'].search([('move_id', 'in', account_moves.ids),
        #                                                            ('account_id.gold', '=', True),
        #                                                            ('account_id.current_position', '=', True)]).sorted(
        #     lambda r: r.date)
        # gold_position = self.env['gold.position'].sudo().search([])
        # gold_capital = gold_position.gold_capital
        # current_position = gold_position.current_position
        # capital_difference = gold_position.capital_difference
        #
        # i = 0
        # for rec in account_move_lines:
        #     bills = self.env['account.move'].search([('date', '>=', self.date_from),
        #                                              ('date', '<=', self.date_to),
        #                                              ('name', '=', rec.ref.split()[0])])
        #     pickings = self.env['stock.picking'].search([('scheduled_date', '>=', self.date_from),
        #                                                  ('scheduled_date', '<=', self.date_to),
        #                                                  ('name', '=', rec.ref.split()[0])])
        #     lines.append({
        #         'date': rec.move_id.date,
        #         'name': rec.move_id.name,
        #         'in': rec.debit if rec.debit != 0.0 else 0.0,
        #         'out': rec.credit if rec.credit != 0.0 else 0.0,
        #         'rate_kilo': 0,
        #         'rate_gram': 0,
        #     })
        #
        #     # WH
        #     for pic in pickings:
        #         related_purchase_orders = self.env['purchase.order'].search([('name', '=', pic.origin)]).sorted(
        #             lambda r: r.date_approve.date())
        #
        #         related_sale_orders = self.env['sale.order'].search([('name', '=', pic.origin)]).sorted(
        #             lambda r: r.date_order.date())
        #
        #         for sal in related_sale_orders:
        #             lines[i]['rate_kilo'] = sal.gold_rate
        #             for s in sal.order_line:
        #                 lines[i]['rate_gram'] = s.gold_rate
        #
        #         for purs in related_purchase_orders:
        #             lines[i]['rate_kilo'] = purs.gold_rate
        #             for p in purs.order_line:
        #                 lines[i]['rate_gram'] = p.gold_rate
        #         i += 1
        #
        #     # Bills
        #     for line in bills:
        #         related_purchase_order = self.env['purchase.order'].search([('name', '=', line.invoice_origin)]).sorted(
        #             lambda r: r.date_approve.date())
        #
        #         for pur in related_purchase_order:
        #             lines[i]['rate_kilo'] = pur.gold_rate
        #             for n in pur.order_line:
        #                 lines[i]['rate_gram'] = n.gold_rate
        #         i += 1
        #
        # data['move_lines'] = lines
        # data['date_from'] = self.date_from
        # data['date_to'] = self.date_to
        # data['gold_capital'] = gold_capital
        # data['current_position'] = current_position
        # data['capital_difference'] = capital_difference
        # return self.env.ref('gold_position.report_gold_journal_entry_qweb').report_action(self, data=data)


class ProjectReport(models.AbstractModel):
    _name = 'report.gold_position.report_account_gold_journal_entry'

    @api.model
    def _get_report_values(self, docids, data=None):
        report_obj = self.env['ir.actions.report']
        report = report_obj._get_report_from_name('gold_position.report_account_gold_journal_entry')
        move_lines = data.get('move_lines')
        date_from = data.get('date_from')
        date_to = data.get('date_to')
        gold_capital = data.get('gold_capital')
        current_position = data.get('current_position')
        capital_difference = data.get('capital_difference')

        return {
            'doc_ids': self._ids,
            'doc_model': report.model,
            'docs': self,
            'move_lines': move_lines,
            'date_from': date_from,
            'date_to': date_to,
            'gold_capital': gold_capital,
            'current_position': current_position,
            'capital_difference': capital_difference
        }
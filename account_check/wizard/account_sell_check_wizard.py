from odoo import fields, models, api, _


class AccountSellCheckWizard(models.TransientModel):
    _name = 'account.sell.check.wizard'
    _description = 'Account Sell Check Wizard'

    journal_id = fields.Many2one(
        comodel_name='account.journal',
        string='Journal',
        domain="[('company_id','=',company_id),('type', 'in', ['cash', 'bank'])]")

    date = fields.Date(
        default=fields.Date.context_today,
        required=True,
    )

    amount = fields.Float(string='Amount')

    write_off_account_id = fields.Many2one(comodel_name='account.account', string='Write-off Account')
    analytic_account_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    less_amount = fields.Boolean()

    check_id = fields.Many2one(comodel_name='account.check')

    @api.onchange('amount')
    def onchange_amount(self):
        check = self.env['account.check'].search([('id', '=', self.check_id.id)])
        if self.amount < check.amount:
            self.less_amount = True

    @api.model
    def validate_sell_check(self, check):
        debit_line_diff_vals = {}
        if not check.journal_id.default_debit_account_id:
            raise Warning(
                _('You must selected default debit account on this check Journal.'))

        if check.type == 'third_check':
            if check.state != 'handed':
                raise Warning(
                    _('The selected checks must be in Handed state.'))

        type = 'selled'
        credit_account = check.journal_id.holding_check_account_id
        debit_account = self.journal_id.default_debit_account_id
        name = _('Check "%s" Sold') % (check.name)

        debit_line_vals = {
            'name': name,
            'account_id': debit_account.id,
            'debit': check.amount if not self.less_amount else self.amount,
            'amount_currency': check.amount_currency,
            'partner_id': check.partner_id and check.partner_id.id or False
        }
        credit_line_vals = {
            'name': name,
            'account_id': credit_account.id,
            'credit': check.amount,
            'amount_currency': check.amount_currency,
            'partner_id': check.partner_id and check.partner_id.id or False
        }

        lines = [(0, False, debit_line_vals), (0, False, credit_line_vals)]

        if self.less_amount and self.write_off_account_id:
            amount = check.amount - self.amount
            debit_line_diff_vals = {
                'name': name,
                'account_id': self.write_off_account_id.id,
                'debit': amount,
                'amount_currency': check.amount_currency,
                'analytic_account_id': self.analytic_account_id.id,
                'partner_id': check.partner_id and check.partner_id.id or False
            }
            lines += [(0, False, debit_line_diff_vals)]

        move_vals = {
            'name': name,
            'journal_id': check.journal_id.id,
            'date': self.date,
            'ref': name,
            'move_check_id': check.id,
            'partner_id': check.partner_id.id,
            'line_ids': lines
        }
        return {
            'type': type,
            'move_vals': move_vals,
        }

    def action_confirm(self):
        for check in self.env['account.check'].browse(self._context.get('active_ids', [])):

            # validate check and get move vals
            vals = self.validate_sell_check(check)
            type = vals.get('type', {})
            move_vals = vals.get('move_vals')
            move = self.env['account.move'].with_context({}).create(move_vals)
            move.post()
            check.write({'state': type})

            # add operation with move ref
            check._add_operation(type, move, partner=check.partner_id, date=self.date)
        return True

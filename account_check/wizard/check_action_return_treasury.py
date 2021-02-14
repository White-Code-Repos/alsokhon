# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import Warning


class AccountCheckActionTreasury(models.TransientModel):
    _name = 'check.return.treasury'

    date = fields.Date(
        'Date', required=True, default=fields.Date.context_today
    )

    def action_confirm(self):
        for check in self.env['account.check'].browse(
                self._context.get('active_ids', [])):
            if check.type == 'third_check':
                if check.state != 'inbank':
                    raise Warning(
                        _('The selected checks must be in inbank state.'))

                # Filling data of move vals and lines
                credit_account = check.journal_id.under_collection_check_account_id
                debit_account = check.journal_id.holding_check_account_id
                sequence = self.env['ir.sequence'].next_by_code('account_check_action')
                name = _('Check "%s" returned %s') % (check.name, sequence)
            else:
                raise Warning(_('You can not inbank an Issue Check.'))

            debit_line_vals = {
                'name': name,
                'account_id': debit_account.id,
                'debit': check.amount,
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
            move_vals = {
                'name': name,
                'journal_id': check.journal_id.id,
                'date': check.issue_date,
                'ref': name,
                'partner_id': check.partner_id.id,
                'move_check_id': check.id,
                'line_ids': [
                    (0, False, debit_line_vals),
                    (0, False, credit_line_vals)]
            }

            # validate check and get move vals
            type = 'holding'
            move = self.env['account.move'].with_context({}).create(move_vals)
            move.post()
            check.write({'state': type})

            # add operation with move ref
            check._add_operation(type, move, partner=check.partner_id, date=self.date)
        return True

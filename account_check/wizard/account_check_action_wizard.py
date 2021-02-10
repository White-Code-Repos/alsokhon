# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class account_check_action_wizard(models.TransientModel):
    _name = 'account.check.action.wizard'
    _description = 'Account Check Action Wizard'

    date = fields.Date(
        default=fields.Date.context_today,
        required=True,
    )
    action_type = fields.Char(
        'Action type passed on the context',
        required=True,
    )

    def action_confirm(self):
        self.ensure_one()
        if self.action_type not in ['claim', 'bank_debit', 'bank_credit', 'reject']:
            raise ValidationError(_(
                'Action %s not supported on checks') % self.action_type)
        check = self.env['account.check'].browse(
            self._context.get('active_id'))
        return getattr(
            check.with_context(action_date=self.date), self.action_type)()

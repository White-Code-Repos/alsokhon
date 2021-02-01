# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.model
    def get_receivable_account(self):
        asset_type = self.env.ref('account.data_account_type_receivable')
        if asset_type:
            return [('user_type_id', '=', asset_type.id), ('gold', '=', True)]
        return []

    gold_account_receivable_id = fields.Many2one(
        'account.account',
        domain=get_receivable_account, string='Account Receivable - Gold')

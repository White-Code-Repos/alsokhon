# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class ProductCategory(models.Model):
    _inherit = 'product.category'

    @api.model
    def get_account_assets_type(self):
        asset_type = self.env.ref('account.data_account_type_direct_costs')
        if asset_type:
            return [('user_type_id', '=', asset_type.id), ('gold', '=', True)]
        return []

    gold_sale_journal = fields.Many2one(
        'account.journal', domain=[('gold', '=', True)],
        string='Gold Sale Journal')
    gold_stock_output_account = fields.Many2one('account.account',
                                               domain=get_account_assets_type,
                                               string='Stock Output Account - Gold')

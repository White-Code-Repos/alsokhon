# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    gold = fields.Boolean(string='Is Gold')

    def _compute_weight_uom_name(self):
        for template in self:
            if template.gold:
                template.weight_uom_name = template.uom_po_id and \
                                           template.uom_po_id.display_name or \
                                           template.uom_id and \
                                           template.uom_id.display_name or 'g'
            else:
                template.weight_uom_name = self._get_weight_uom_name_from_ir_config_parameter()

    @api.model
    def create(self, vals):
        res = super(ProductTemplate, self).create(vals)
        if res.gold and (not res.attribute_line_ids) and res.weight <= 0.0:
            raise ValidationError('Product weight must be greater than zero.')
        return res

    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)
        for rec in self:
            if (vals.get('gold', False) or rec.gold) and (
                    not rec.attribute_line_ids) and (
                    vals.get('weight') and vals.get('weight') <= 0.0 or
                    rec.weight <= 0.0):
                raise ValidationError(
                    'Product weight must be greater than zero.')
        return res


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.model
    def create(self, vals):
        res = super(ProductProduct, self).create(vals)
        if res.gold and res.weight <= 0.0:
            raise ValidationError('Product weight must be greater than zero.')
        return res

    def write(self, vals):
        res = super(ProductProduct, self).write(vals)
        for rec in self:
            if (vals.get('gold', False) or rec.gold) and (
                    vals.get('weight') and vals.get('weight') <= 0.0 or
                    rec.weight <= 0.0):
                raise ValidationError(
                    'Product weight must be greater than zero.')
        return res


class ProductCategory(models.Model):
    _inherit = 'product.category'

    @api.model
    def get_account_assets_type(self):
        asset_type = self.env.ref('account.data_account_type_current_assets')
        if asset_type:
            return [('user_type_id', '=', asset_type.id), ('gold', '=', True)]
        return []

    gold_journal = fields.Many2one(
        'account.journal', domain=[('gold', '=', True)],
        string='Gold Journal')
    gold_on_hand_account = fields.Many2one('account.account',
                                           domain=get_account_assets_type,
                                           string='Stock In Hand - Gold')


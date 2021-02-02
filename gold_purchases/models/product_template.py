# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class MakingCharges(models.Model):
    _name = 'making.charges'
    _description = 'Making Charges'

    name = fields.Char('Name')
    making_charge = fields.Float('Charges')


class ProductTemplate(models.Model):
    _inherit = "product.template"

    gold = fields.Boolean(string='Gold')
    origin = fields.Many2one('res.country', string='Origin')
    is_making_charges = fields.Boolean('Gold Making Charges')
    scrap = fields.Boolean(string="Scrap")
    making_charge_id = fields.Many2one('product.product', 'Making Charges product')
    hide_gold_making = fields.Boolean(compute="_compute_hide_gold_making")
    @api.onchange('is_making_charges','gold','assembly')
    def _compute_hide_gold_making(self):
        for this in self:
            this.hide_gold_making = True
            if this.assembly:
                this.hide_gold_making = False
            else:
                if this.is_making_charges:
                    this.hide_gold_making = True
                if not this.gold:
                    this.hide_gold_making = True
                else:
                    this.hide_gold_making = False
    hide_diamond_making = fields.Boolean(compute="_compute_hide_diamond_making")
    @api.onchange('is_making_charges','diamond','assembly')
    def _compute_hide_diamond_making(self):
        for this in self:
            this.hide_diamond_making = True
            if this.assembly:
                this.hide_diamond_making = False
            else:
                if this.is_diamond_making_charges:
                    this.hide_diamond_making = True
                if not this.diamond:
                    this.hide_diamond_making = True
                else:
                    this.hide_diamond_making = False

    # @api.onchange('type')
    # def onchange_type_gold(self):
    #     if self.type != 'product':
    #         self.gold = False
    #     if self.type != 'service':
    #         self.is_making_charges = False
    #         self.making_charge_id = False
    #     if self.type == 'consu':
    #         self.gold = False
    #         self.is_making_charges = False
    #         self.making_charge_id = False

    # @api.onchange('gold')
    # def onchange_gold(self):
    #     if self.gold:
    #         self.is_making_charges = False

    # @api.onchange('is_making_charges')
    # def onchange_is_making_charges(self):
    #     if self.is_making_charges:
    #         self.gold = False

    def _compute_weight_uom_name(self):
        for template in self:
            if template.gold:
                template.weight_uom_name = template.uom_po_id and \
                                           template.uom_po_id.display_name or \
                                           template.uom_id and \
                                           template.uom_id.display_name or 'g'
            else:
                template.weight_uom_name = self._get_weight_uom_name_from_ir_config_parameter()


class ProductProduct(models.Model):
    _inherit = 'product.product'

    # @api.onchange('type')
    # def onchange_type_gold(self):
    #     if self.type != 'product':
    #         self.gold = False
    #     if self.type != 'service':
    #         self.is_making_charges = False
    #         self.making_charge_id = False
    #     if self.type == 'consu':
    #         self.gold = False
    #         self.is_making_charges = False
    #         self.making_charge_id = False

    # @api.onchange('gold')
    # def onchange_gold(self):
    #     if self.gold:
    #         self.is_making_charges = False

    # @api.onchange('is_making_charges')
    # def onchange_is_making_charges(self):
    #     if self.is_making_charges:
    #         self.gold = False


class ProductCategory(models.Model):
    _inherit = 'product.category'

    @api.model
    def get_account_assets_type(self):
        asset_type = self.env.ref('account.data_account_type_current_assets')
        if asset_type:
            return [('user_type_id', '=', asset_type.id), ('gold', '=', True)]
        return []

    @api.model
    def get_account_gold_type(self):
        return [('gold', '=', True)]


    gold_journal = fields.Many2one(
        'account.journal', domain=[('gold', '=', True)],
        string='Gold Journal')
    gold_purchase_journal = fields.Many2one(
        'account.journal', domain=[('gold', '=', True)],
        string='Gold purchase Journal')
    gold_on_hand_account = fields.Many2one('account.account',
                                           domain=get_account_assets_type,
                                           string='Stock In Hand - Gold')
    gold_stock_input_account = fields.Many2one('account.account',
                                               domain=get_account_assets_type,
                                               string='Stock Input Account - Gold')
    gold_expense_account = fields.Many2one('account.account',
                                           domain=get_account_gold_type,
                                           string='Expense Account - Gold')

    gold_fixing_account = fields.Many2one('account.account',
                                            domain="get_account_fixing_type",
                                            string="Fixing Account - Gold")
    @api.model
    def get_account_fixing_type(self):
        asset_type = self.env.ref('account.data_account_type_current_assets')
        if asset_type:
            return [('user_type_id', '=', asset_type.id), ('gold', '=', True)]
        return []

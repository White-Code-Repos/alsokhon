from odoo import api, fields, models
from odoo.addons.purchase.models.purchase import PurchaseOrder as Purchase


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    def _default_order_type(self):
        return self.env['purchase.order.type'].search([], limit=1)

    order_type = fields.Many2one(comodel_name='purchase.order.type',
                                 readonly=False,
                                 states=Purchase.READONLY_STATES,
                                 string='Type',
                                 ondelete='restrict',
                                 default=_default_order_type)
    is_fixed = fields.Boolean(string='Fixed', compute='get_is_fixed')
    is_unfixed = fields.Boolean(string='unFixed', compute='get_is_unfixed')
    gold = fields.Boolean(string='gold', compute='get_is_gold')
    diamond = fields.Boolean(string='stone', compute='get_is_diamond')
    assembly = fields.Boolean(string='assembly', compute='get_is_assembly')

    @api.depends('order_type')
    def get_is_assembly(self):
        for rec in self:
            rec.assembly = rec.order_type and rec.order_type.assembly and True or False

    @api.depends('order_type')
    def get_is_fixed(self):
        for rec in self:
            rec.is_fixed = rec.order_type and rec.order_type.is_fixed and True or False

    @api.depends('order_type')
    def get_is_unfixed(self):
        for rec in self:
            rec.is_unfixed = rec.order_type and rec.order_type.is_unfixed and True or False

    @api.depends('order_type')
    def get_is_diamond(self):
        for rec in self:
            rec.diamond = rec.order_type and rec.order_type.diamond and True or False

    @api.depends('order_type')
    def get_is_gold(self):
        for rec in self:
            rec.gold = rec.order_type and rec.order_type.gold and True or False

    @api.onchange('partner_id')
    def onchange_partner_id(self):
        super().onchange_partner_id()
        purchase_type = (self.partner_id.purchase_type or
                         self.partner_id.commercial_partner_id.purchase_type)
        if purchase_type:
            self.order_type = purchase_type

    @api.onchange('order_type')
    def onchange_order_type(self):
        for order in self:
            if order.order_type.payment_term_id:
                order.payment_term_id = order.order_type.payment_term_id.id
            if order.order_type.incoterm_id:
                order.incoterm_id = order.order_type.incoterm_id.id

    @api.model
    def create(self, vals):
        if vals.get('name', '/') == '/' and vals.get('order_type'):
            purchase_type = self.env['purchase.order.type'].browse(
                vals['order_type'])
            if purchase_type.sequence_id:
                vals['name'] = purchase_type.sequence_id.next_by_id()
        return super().create(vals)

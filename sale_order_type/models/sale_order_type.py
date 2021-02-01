from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class SaleOrderType(models.Model):
    _name = 'sale.order.type'
    _description = 'Type of sale order'
    _order = 'sequence'

    @api.model
    def _get_domain_sequence_id(self):
        seq_type = self.env.ref('sale.seq_sale_order')
        return [('code', '=', seq_type.code)]

    @api.model
    def _default_sequence_id(self):
        seq_type = self.env.ref('sale.seq_sale_order')
        return seq_type.id

    name = fields.Char(required=True)
    active = fields.Boolean(default=True)
    description = fields.Text(string='Description', translate=True)
    sequence_id = fields.Many2one(
        comodel_name='ir.sequence', string='Entry Sequence', copy=False,
        domain=_get_domain_sequence_id, default=_default_sequence_id,
        required=True)
    payment_term_id = fields.Many2one(
        comodel_name='account.payment.term', string='Payment Terms')
    incoterm_id = fields.Many2one(
        comodel_name='account.incoterms', string='Incoterm')
    sequence = fields.Integer(default=10)
    is_fixed = fields.Boolean('Is Fixed')
    is_unfixed = fields.Boolean('Is Unfixed')
    gold = fields.Boolean('Gold')
    diamond = fields.Boolean('Diamond')
    assembly = fields.Boolean('Assembly')
    stock_picking_type_id = fields.Many2one(
        comodel_name='stock.picking.type', string='picking type')


    @api.constrains('stock_picking_type_id')
    def _check_stock_picking_type_id(self):
        for check in self:
            if not check.stock_picking_type_id.default_location_src_id or not  check.stock_picking_type_id.default_location_dest_id:
                raise ValidationError(_('please fill source and destination locations for picking type.'))

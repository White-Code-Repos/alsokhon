from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sale_type = fields.Many2one(
        comodel_name='sale.order.type', string='Sale Order Type')

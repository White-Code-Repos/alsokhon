# -*- coding: utf-8 -*-

from odoo import fields, models,tools,api
import logging

class order_note(models.Model):
    _name = 'order.note'

    name = fields.Char('Note')
    pos_config_id = fields.Many2one("pos.config")

class pos_config(models.Model):
    _inherit = 'pos.config'

    allow_order_note = fields.Boolean('Allow order note',default=True)
    allow_line_note = fields.Boolean('Allow Line note',default=True)
    shortcut_note = fields.Many2many("order.note","pos_shortcut_config_id","product_id","shortcut_id","Shortcut Note")

class ProductProduct(models.Model):
    _inherit = "product.product"

    shortcut_note = fields.Many2many("order.note","pos_shortcut_product_id","product_id","shortcut_id","Shortcut Note")

class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model
    def _order_fields(self, ui_order):
        res = super(PosOrder, self)._order_fields(ui_order)
        res['note'] = ui_order['note']
        return res

class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    extra_note = fields.Char('Note')

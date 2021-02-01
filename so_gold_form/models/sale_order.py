# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    gold_rate = fields.Float(string='Gold Rate', digits=(12, 12))

    @api.onchange('currency_id', 'date_order', 'order_type')
    def get_gold_rate(self):
        if self.date_order and self.currency_id and self.currency_id.is_gold \
                and self.order_type and self.order_type.gold or self.order_type.assembly:
            rates = self.env['gold.rates'].search([
                ('currency_id', '=', self.currency_id.id),
                ('name', '=', self.date_order.date()),
                ('company_id', 'in', [False, self.company_id and
                                      self.company_id.id or False])
            ], limit=1, order='name desc, id desc')
            ozs = self.env.ref('uom.product_uom_oz')
            if rates and ozs:
                self.gold_rate = (1.000/rates[0].rate)*ozs.factor
                self.gold_rate = self.gold_rate + self.currency_id.premium
            else:
                self.gold_rate = 0.00
        else:
            self.gold_rate = 0.00

# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
# from datetime import timedelta, time
# from odoo import api, fields, models
# from odoo.tools.float_utils import float_round


# class ProductProduct(models.Model):
#     _inherit = 'product.product'
#
#     qty_available_validate = fields.Float(compute='_compute_qty_available_validate', string='Qty Available')
#
#     def _compute_qty_available_validate(self):
#         r = {}
#         self.qty_available_validate = 0
#         if not self.user_has_groups('sales_team.group_sale_salesman'):
#             return r
#         date_from = fields.Datetime.to_string(fields.datetime.combine(fields.datetime.now() - timedelta(days=365),
#                                                                       time.min))
#
#         # done_states = self.env['sale.report']._get_done_states()
#
#         domain = [
#             ('state', 'in', ['draft','sent','sale']),
#             ('product_id', 'in', self.ids),
#             ('date', '>=', date_from),
#         ]
#         print("_compute_qty_available_validate")
#         print(self)
#         print(domain)
#         for group in self.env['sale.report'].read_group(domain, ['product_id', 'product_uom_qty'], ['product_id']):
#             r[group['product_id'][0]] = group['product_uom_qty']
#         print(r)
#         for product in self:
#             if not product.id:
#                 product.qty_available_validate = 0.0
#                 continue
#             product.qty_available_validate = float_round(r.get(product.id, 0), precision_rounding=product.uom_id.rounding)
#         return r

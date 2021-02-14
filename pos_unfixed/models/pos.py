# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
import logging
import datetime
_logger = logging.getLogger(__name__)


class pos_config(models.Model):
    _inherit = 'pos.config'
#
    session_type = fields.Selection([('sale', 'Whole Sale'),('retail', 'Retail')],default='retail',string='Session Type')
#     lot_expire_days = fields.Integer('Product Lot expire days.', default=1)
#     pos_lot_receipt = fields.Boolean('Print lot Number on receipt',default=1)
#
# class stock_production_lot(models.Model):
#     _inherit = "stock.production.lot"
#
#     gold_rate = fields.Float(string='Gold Rate', digits=(16, 3), compute="_compute_gold_rate")
#
#     def _compute_gold_rate(self):
#         for this in self:
#             if this.currency_id and this.currency_id.is_gold :
#                 rates = this.env['gold.rates'].search([
#                     ('currency_id', '=', this.currency_id.id),
#                     ('name', '=', this.create_date.date()),
#                     ('company_id', 'in', [False, this.company_id and
#                                           this.company_id.id or False])
#                 ], limit=1, order='name desc, id desc')
#                 ozs = this.env.ref('uom.product_uom_oz')
#                 if rates and ozs:
#                     gold_rate = (1.000/rates[0].rate)*ozs.factor
#                     gold_rate = gold_rate + this.currency_id.premium
#                     this.gold_rate = gold_rate / 1000.000000000000
#
#                 else:
#                     this.gold_rate = 0.00
#             else:
#                 this.gold_rate = 0.00
#
#
#     total_qty = fields.Float("Total Qty", compute="_computeTotalQty")
#     purity_id = fields.Many2one('gold.purity', compute="_compute_purity_id")
#
#     def _compute_purity_id(self):
#         for this in self:
#             stock_move_line = this.env['stock.move.line'].search([('lot_id','=',this.id)])
#             if stock_move_line:
#                 if stock_move_line.picking_id:
#                     if stock_move_line.picking_id.group_id:
#                         group_id= stock_move_line.picking_id.group_id[0]
#                         if group_id.name:
#                             if 'P0' in group_id.name:
#                                 purchase_order = this.env['purchase.order'].search([('name','=',group_id.name)])
#                                 if purchase_order and len(purchase_order) == 1:
#                                     for line in purchase_order.order_line:
#                                         if line.product_id == this.product_id:
#                                             this.purity_id = line.purity_id.id
#             if not this.purity_id:
#                 this.purity_id = False
#     # @api.multi
#     def _computeTotalQty(self):
#         pos_config = self.env['pos.config'].search([], limit=1)
#         pos_location_id = self.env['stock.location'].search([('id','=',pos_config.picking_type_id.default_location_src_id.id)])
#         for record in self:
#             move_line = self.env['stock.move.line'].search([('lot_id','=',record.id)])
#             record.total_qty = 0.0
#             for rec in move_line:
#                 #if rec.location_dest_id.usage in ['internal', 'transit']:
#                 #    record.total_qty += rec.qty_done
#                 #else:
#                 #    record.total_qty -= rec.qty_done
#                 if rec.location_dest_id == pos_location_id:
#                     record.total_qty += rec.qty_done
#                 elif rec.location_id == pos_location_id:
#                     record.total_qty -= rec.qty_done
#                 else:
#                     continue
#
#
class PosOrder(models.Model):
    _inherit = "pos.order"

    order_type = fields.Selection([('sale', "Whole Sale"),('retail', "Retail")], string='Order Type', default='retail')

    @api.model
    def _order_fields(self, ui_order):
        order_fields = super(PosOrder, self)._order_fields(ui_order)
        print("order_fields")
        print(order_fields)
        order_fields['order_type'] = ui_order.get('order_type', False)
        return order_fields

#
#     def set_pack_operation_lot(self, picking=None):
#         """Set Serial/Lot number in pack operations to mark the pack operation done."""
#
#         StockProductionLot = self.env['stock.production.lot']
#         PosPackOperationLot = self.env['pos.pack.operation.lot']
#         has_wrong_lots = False
#         for order in self:
#             for move in (picking or self.picking_id).move_lines:
#                 picking_type = (picking or self.picking_id).picking_type_id
#                 lots_necessary = True
#                 if picking_type:
#                     lots_necessary = picking_type and picking_type.use_existing_lots
#                 qty = 0
#                 qty_done = 0
#                 pack_lots = []
#                 pos_pack_lots = PosPackOperationLot.search([('order_id', '=', order.id), ('product_id', '=', move.product_id.id)])
#                 pack_lot_names = [pos_pack.lot_name for pos_pack in pos_pack_lots]
#                 if pack_lot_names and lots_necessary:
#                     for lot_name in list(set(pack_lot_names)):
#                         stock_production_lot = StockProductionLot.search([('name', '=', lot_name), ('product_id', '=', move.product_id.id)])
#                         if stock_production_lot:
#                             if stock_production_lot.product_id.tracking == 'lot':
#                                 tt = 0
#                                 for ll in pack_lot_names:
#                                     if ll == lot_name:
#                                         tt += 1
#
#                                 # if a lot nr is set through the frontend it will refer to the full quantity
#                                 qty = tt
#                             else: # serial numbers
#                                 qty = 1.0
#                             qty_done += qty
#                             pack_lots.append({'lot_id': stock_production_lot.id, 'qty': qty})
#                         else:
#                             has_wrong_lots = True
#                 elif move.product_id.tracking == 'none' or not lots_necessary:
#                     qty_done = move.product_uom_qty
#                 else:
#                     has_wrong_lots = True
#                 for pack_lot in pack_lots:
#                     lot_id, qty = pack_lot['lot_id'], pack_lot['qty']
#                     self.env['stock.move.line'].create({
#                         'move_id': move.id,
#                         'product_id': move.product_id.id,
#                         'product_uom_id': move.product_uom.id,
#                         'qty_done': qty,
#                         'location_id': move.location_id.id,
#                         'location_dest_id': move.location_dest_id.id,
#                         'lot_id': lot_id,
#                     })
#                 if not pack_lots:
#                     move.quantity_done = qty_done
#         return has_wrong_lots
#
#     def _action_create_invoice_line(self, line=False, invoice_id=False):
#         result = super(PosOrder, self)._action_create_invoice_line(line, invoice_id)
#         for pro_lot in line.pack_lot_ids:
#             pro_lot.account_move_line_id = result.id
#         return result
#
# class AccountInvoiceLine(models.Model):
#     _inherit = 'account.move.line'
#
#     pack_lot_ids = fields.One2many('pos.pack.operation.lot', 'account_move_line_id', string='Lot/serial Number')
#
#
# class PosOrderLineLot(models.Model):
#     _inherit = "pos.pack.operation.lot"
#
#     account_move_line_id = fields.Many2one('account.move.line')

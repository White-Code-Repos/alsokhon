# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
import logging
import datetime
_logger = logging.getLogger(__name__)


# class pos_order_line(models.Model):
#     _inherit = 'pos.order.line'
#     gross_weight = fields.Float('Gross Wt', digits=(16, 3))
#     purity_id = fields.Many2one('gold.purity', 'Purity')
#     pure_weight = fields.Float('Pure Weight', digits=(16, 3))
#     make_value = fields.Monetary('Make Value Per G', digits=(16, 3))
#     gold_rate = fields.Float('Gold Rate/G', digits=(16, 3))
#
#     def _order_line_fields(self, line, session_id=None):
#         if line[2].get('pack_lot_ids'):
#             lot_name = line[2].get('pack_lot_ids')[0][2]['lot_name']
#             if lot_name:
#                 lot = self.env['stock.production.lot'].search([('name','=',lot_name)])
#                 if lot:
#                     line[2]['gross_weight'] = lot.gross_weight
#                     line[2]['purity_id'] = lot.purity_id.id
#                     line[2]['pure_weight'] = lot.pure_weight
#                     line[2]['make_value'] = lot.selling_making_charge
#                     line[2]['gold_rate'] = lot.gold_rate
#         if line and 'name' not in line[2]:
#             session = self.env['pos.session'].browse(session_id).exists() if session_id else None
#             if session and session.config_id.sequence_line_id:
#                 # set name based on the sequence specified on the config
#                 line[2]['name'] = session.config_id.sequence_line_id._next()
#             else:
#                 # fallback on any pos.order.line sequence
#                 line[2]['name'] = self.env['ir.sequence'].next_by_code('pos.order.line')
#
#         if line and 'tax_ids' not in line[2]:
#             product = self.env['product.product'].browse(line[2]['product_id'])
#             line[2]['tax_ids'] = [(6, 0, [x.id for x in product.taxes_id])]
#         # Clean up fields sent by the JS
#         line = [
#             line[0], line[1], {k: v for k, v in line[2].items() if k in self.env['pos.order.line']._fields}
#         ]
#         return line
#
#
# class pos_config(models.Model):
#     _inherit = 'pos.config'
#
#     allow_pos_lot = fields.Boolean('Allow POS Lot', default=True)
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

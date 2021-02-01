# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
import logging
import datetime
from datetime import timedelta
from functools import partial

import psycopg2
import pytz

from odoo.tools import float_is_zero
from odoo.exceptions import UserError
from odoo.http import request
from odoo.osv.expression import AND
import base64

_logger = logging.getLogger(__name__)


class pos_order_line(models.Model):
    _inherit = 'pos.order.line'
    gross_weight = fields.Float('Gross Wt', digits=(16, 3))
    purity_id = fields.Many2one('gold.purity', 'Purity')
    pure_weight = fields.Float('Pure Weight', digits=(16, 3))
    make_value = fields.Monetary('Make Value Per G', digits=(16, 3))
    gold_rate = fields.Float('Gold Rate/G', digits=(16, 3))

    def _order_line_fields(self, line, session_id=None):
        if line[2].get('pack_lot_ids'):
            lot_name = line[2].get('pack_lot_ids')[0][2]['lot_name']
            if lot_name:

                lot = self.env['stock.production.lot'].search([('name','=',lot_name),('product_id','=',line[2]['product_id'])])
                session = self.env['pos.session'].browse(session_id).exists() if session_id else None
                rate = session.config_id.gold_rate if session else 0
                if lot:
                    line[2]['gross_weight'] = lot.gross_weight
                    line[2]['purity_id'] = lot.purity_id.id
                    line[2]['pure_weight'] = lot.pure_weight
                    line[2]['make_value'] = lot.selling_making_charge
                    line[2]['gold_rate'] = rate
                    line[2]['carat'] = lot.carat
        if line and 'name' not in line[2]:
            session = self.env['pos.session'].browse(session_id).exists() if session_id else None
            if session and session.config_id.sequence_line_id:
                # set name based on the sequence specified on the config
                line[2]['name'] = session.config_id.sequence_line_id._next()
            else:
                # fallback on any pos.order.line sequence
                line[2]['name'] = self.env['ir.sequence'].next_by_code('pos.order.line')

        if line and 'tax_ids' not in line[2]:
            product = self.env['product.product'].browse(line[2]['product_id'])
            line[2]['tax_ids'] = [(6, 0, [x.id for x in product.taxes_id])]
        # Clean up fields sent by the JS
        line = [
            line[0], line[1], {k: v for k, v in line[2].items() if k in self.env['pos.order.line']._fields}
        ]
        return line


class pos_config(models.Model):
    _inherit = 'pos.config'

    allow_pos_lot = fields.Boolean('Allow POS Lot', default=True)
    lot_expire_days = fields.Integer('Product Lot expire days.', default=1)
    pos_lot_receipt = fields.Boolean('Print lot Number on receipt',default=1)
    gold_rate = fields.Float(string='Gold Rate', digits=(16, 3), compute="_compute_gold_rate")

    def _compute_gold_rate(self):
        for this in self:
            if this.currency_id and this.currency_id.is_gold :
                rates = this.env['gold.rates'].search([
                    ('currency_id', '=', this.currency_id.id),
                    ('name', '=', datetime.date.today()),
                    ('company_id', 'in', [False, this.company_id and
                                          this.company_id.id or False])
                ], limit=1, order='name desc, id desc')
                ozs = this.env.ref('uom.product_uom_oz')
                if rates and ozs:
                    gold_rate = (1.000/rates[0].rate)*ozs.factor
                    gold_rate = gold_rate + this.currency_id.premium
                    this.gold_rate = gold_rate / 1000.000000000000

                else:
                    this.gold_rate = 0.00
            else:
                this.gold_rate = 0.00


class stock_production_lot(models.Model):
    _inherit = "stock.production.lot"

    gold_rate = fields.Float(string='Gold Rate', digits=(16, 3), compute="_compute_gold_rate")
    from_pos = fields.Integer(string='From Pos')

    def _compute_gold_rate(self):
        for this in self:
            if this.currency_id and this.currency_id.is_gold :
                rates = this.env['gold.rates'].search([
                    ('currency_id', '=', this.currency_id.id),
                    ('name', '=', this.create_date.date()),
                    ('company_id', 'in', [False, this.company_id and
                                          this.company_id.id or False])
                ], limit=1, order='name desc, id desc')
                ozs = this.env.ref('uom.product_uom_oz')
                if rates and ozs:
                    gold_rate = (1.000/rates[0].rate)*ozs.factor
                    gold_rate = gold_rate + this.currency_id.premium
                    this.gold_rate = gold_rate / 1000.000000000000

                else:
                    this.gold_rate = 0.00
            else:
                this.gold_rate = 0.00

    @api.model_create_multi
    def create(self, vals_list):
        self._check_create()
        # print("vals_list")
        # print(vals_list[0])
        # dic.get("C")
        # print('from_pos' in vals_list[0])
        # print(vals_list[0].get("from_pos"))
        if len(vals_list) > 0:
            if not vals_list[0].get("from_pos",0):
                vals_list[0]['from_pos'] = 0
        data = super(stock_production_lot, self).create(vals_list)
        # print("data")
        # print(data)
        # print(data and vals_list[0].get("from_pos"))
        if len(vals_list) > 0:
            if data and vals_list[0].get("from_pos"):
                self._compute_purity_id()
        return data


    total_qty = fields.Float("Total Qty", compute="_computeTotalQty")
    # @api.multi
    def _computeTotalQty(self):
        pos_config = self.env['pos.config'].search([], limit=1)
        pos_location_id = self.env['stock.location'].search([('id','=',pos_config.picking_type_id.default_location_src_id.id)])
        for record in self:
            # print("record")
            # print(record)
            move_line = self.env['stock.move.line'].search([('lot_id','=',record.id)])
            record.total_qty = 0.0
            for rec in move_line:
                #if rec.location_dest_id.usage in ['internal', 'transit']:
                #    record.total_qty += rec.qty_done
                #else:
                #    record.total_qty -= rec.qty_done
                if rec.location_dest_id == pos_location_id:
                    record.total_qty += rec.qty_done
                    # record.gross_weight -= rec.qty_done
                elif rec.location_id == pos_location_id:
                    record.total_qty -= rec.qty_done
                    # record.gross_weight -= rec.qty_done
                else:
                    continue


class PosOrder(models.Model):
    _inherit = "pos.order"

    def set_pack_operation_lot(self, picking=None):
        """Set Serial/Lot number in pack operations to mark the pack operation done."""

        StockProductionLot = self.env['stock.production.lot']
        PosPackOperationLot = self.env['pos.pack.operation.lot']
        has_wrong_lots = False
        for order in self:
            for move in (picking or self.picking_id).move_lines:
                picking_type = (picking or self.picking_id).picking_type_id
                lots_necessary = True
                if picking_type:
                    lots_necessary = picking_type and picking_type.use_existing_lots
                qty = 0
                qty_done = 0
                pack_lots = []
                pos_pack_lots = PosPackOperationLot.search([('order_id', '=', order.id), ('product_id', '=', move.product_id.id)])
                pack_lot_names = [pos_pack.lot_name for pos_pack in pos_pack_lots]

                if pack_lot_names and lots_necessary:
                    for lot_name in list(set(pack_lot_names)):
                        stock_production_lot = StockProductionLot.search([('name', '=', lot_name), ('product_id', '=', move.product_id.id)])
                        if stock_production_lot:
                            if stock_production_lot.product_id.tracking == 'lot':
                                # tt = 0
                                # for ll in pack_lot_names:
                                #     if ll == lot_name:
                                #         tt += 1

                                # if a lot nr is set through the frontend it will refer to the full quantity
                                qty = move.product_uom_qty
                                # qty = tt
                            else: # serial numbers
                                qty = 1.0
                            qty_done += qty
                            pack_lots.append({'lot_id': stock_production_lot.id, 'qty': qty})
                        else:
                            has_wrong_lots = True
                elif move.product_id.tracking == 'none' or not lots_necessary:
                    qty_done = move.product_uom_qty
                else:
                    has_wrong_lots = True
                for pack_lot in pack_lots:
                    lot_id, qty = pack_lot['lot_id'], pack_lot['qty']
                    self.env['stock.move.line'].create({
                        'move_id': move.id,
                        'product_id': move.product_id.id,
                        'product_uom_id': move.product_uom.id,
                        'qty_done': qty,
                        'location_id': move.location_id.id,
                        'location_dest_id': move.location_dest_id.id,
                        'lot_id': lot_id,
                    })

                if not pack_lots:
                    move.quantity_done = qty_done
        return has_wrong_lots

    def _action_create_invoice_line(self, line=False, invoice_id=False):
        result = super(PosOrder, self)._action_create_invoice_line(line, invoice_id)
        for pro_lot in line.pack_lot_ids:
            pro_lot.account_move_line_id = result.id
        return result

    def create_picking(self):
        """Create a picking for each order and validate it."""
        Picking = self.env['stock.picking']
        # If no email is set on the user, the picking creation and validation will fail be cause of
        # the 'Unable to log message, please configure the sender's email address.' error.
        # We disable the tracking in this case.
        if not self.env.user.partner_id.email:
            Picking = Picking.with_context(tracking_disable=True)
        Move = self.env['stock.move']
        StockWarehouse = self.env['stock.warehouse']
        for order in self:
            if not order.lines.filtered(lambda l: l.product_id.type in ['product', 'consu']):
                continue
            address = order.partner_id.address_get(['delivery']) or {}
            picking_type = order.picking_type_id
            return_pick_type = order.picking_type_id.return_picking_type_id or order.picking_type_id
            order_picking = Picking
            return_picking = Picking
            moves = Move
            location_id = picking_type.default_location_src_id.id
            if order.partner_id:
                destination_id = order.partner_id.property_stock_customer.id
            else:
                if (not picking_type) or (not picking_type.default_location_dest_id):
                    customerloc, supplierloc = StockWarehouse._get_partner_locations()
                    destination_id = customerloc.id
                else:
                    destination_id = picking_type.default_location_dest_id.id

            if picking_type:
                message = _("This transfer has been created from the point of sale session: <a href=# data-oe-model=pos.order data-oe-id=%d>%s</a>") % (order.id, order.name)
                picking_vals = {
                    'origin': '%s - %s' % (order.session_id.name, order.name),
                    'partner_id': address.get('delivery', False),
                    'user_id': False,
                    'date_done': order.date_order,
                    'picking_type_id': picking_type.id,
                    'company_id': order.company_id.id,
                    'move_type': 'direct',
                    'note': order.note or "",
                    'location_id': location_id,
                    'location_dest_id': destination_id,
                }
                pos_qty = any([x.qty > 0 for x in order.lines if x.product_id.type in ['product', 'consu']])
                if pos_qty:
                    order_picking = Picking.create(picking_vals.copy())
                    if self.env.user.partner_id.email:
                        order_picking.message_post(body=message)
                    else:
                        order_picking.sudo().message_post(body=message)
                neg_qty = any([x.qty < 0 for x in order.lines if x.product_id.type in ['product', 'consu']])
                # print("neg_qty")
                # print(neg_qty)
                if neg_qty:
                    return_vals = picking_vals.copy()
                    return_vals.update({
                        'location_id': destination_id,
                        'location_dest_id': return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
                        'picking_type_id': return_pick_type.id
                    })
                    # print({
                    #     'location_id': destination_id,
                    #     'location_dest_id': return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
                    #     'picking_type_id': return_pick_type.id
                    # })
                    return_picking = Picking.create(return_vals)
                    if self.env.user.partner_id.email:
                        return_picking.message_post(body=message)
                    else:
                        return_picking.sudo().message_post(body=message)


            for line in order.lines.filtered(lambda l: l.product_id.type in ['product', 'consu'] and not float_is_zero(l.qty, precision_rounding=l.product_id.uom_id.rounding)):
                if line.pack_lot_ids:


                    for lots in line.pack_lot_ids:

                        lot_id = lots
                        # print(lot_id)
                        # print(line.lot_id.gross_weight , line.product_uom_qty)


                        lot = self.env['stock.production.lot'].search([('name','=',lot_id.lot_name),('product_id','=',lot_id.product_id.id)])
                        gross_weight = lot.gross_weight
                        pure_weight = lot.pure_weight
                        carat = lot.carat
                        # print("BJKBJH")
                        # print(lot)
                        # print(line.qty)
# # 97.0 1.0 97.0
#                         print(lot.carat,line.qty,lot.total_qty)
                        if line.product_id.categ_id.is_scrap:
                            lot.gross_weight -= line.qty
                        elif line.product_id.categ_id.is_diamond:
                            if lot.total_qty==1:
                                lot.carat-=0
                            else:
                                # print("jkhj")
                                lot.carat-=line.qty
                        else:
                            lot.gross_weight -= line.qty * lot.gross_weight
                        # print("(((((lot.carat)))))")
                        # print({
                        #     'name': line.name,
                        #     'product_uom': line.product_id.uom_id.id,
                        #     'picking_id': order_picking.id if line.qty >= 0 else return_picking.id,
                        #     'picking_type_id': picking_type.id if line.qty >= 0 else return_pick_type.id,
                        #     'product_id': line.product_id.id,#   item_category_id sub_category_id selling_karat_id selling_making_charge
                        #     'gross_weight':gross_weight if (gross_weight-lot.gross_weight)==0 else gross_weight-lot.gross_weight,
                        #     'pure_weight':pure_weight if (pure_weight-lot.pure_weight)==0 else pure_weight-lot.pure_weight,
                        #     'carat': carat-lot.carat,
                        #     'purity': line.purity_id.scrap_purity,
                        #     'selling_making_charge': line.make_value,
                        #     'lot_id': lot.id,
                        #     'product_uom_qty': abs(line.qty),
                        #     'state': 'draft',
                        #     'location_id': location_id if line.qty >= 0 else destination_id,
                        #     'location_dest_id': destination_id if line.qty >= 0 else return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
                        # })

                        moves |= Move.create({
                            'name': line.name,
                            'product_uom': line.product_id.uom_id.id,
                            'picking_id': order_picking.id if line.qty >= 0 else return_picking.id,
                            'picking_type_id': picking_type.id if line.qty >= 0 else return_pick_type.id,
                            'product_id': line.product_id.id,#   item_category_id sub_category_id selling_karat_id selling_making_charge
                            'gross_weight':gross_weight if (gross_weight-lot.gross_weight)==0 else gross_weight-lot.gross_weight,
                            'pure_weight':pure_weight if (pure_weight-lot.pure_weight)==0 else pure_weight-lot.pure_weight,
                            'carat': carat-lot.carat,
                            'purity': line.purity_id.scrap_purity,
                            'selling_making_charge': line.make_value,
                            'lot_id': lot.id,
                            'product_uom_qty': abs(line.qty),
                            'state': 'draft',
                            'location_id': location_id if line.qty >= 0 else destination_id,
                            'location_dest_id': destination_id if line.qty >= 0 else return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
                        })
                        # print(moves)
                        # print(moves.move_line_ids)
                        # for value in moves.move_line_ids:
                        #     print(value)
                        #     print(value.name)
                        #     print(value.lot_id)
                        # return False
                        # print(moves)
                else:
                    moves |= Move.create({
                        'name': line.name,
                        'product_uom': line.product_id.uom_id.id,
                        'picking_id': order_picking.id if line.qty >= 0 else return_picking.id,
                        'picking_type_id': picking_type.id if line.qty >= 0 else return_pick_type.id,
                        'product_id': line.product_id.id,#   item_category_id sub_category_id selling_karat_id selling_making_charge
                        'gross_weight': line.gross_weight,
                        'pure_weight': line.pure_weight,
                        'purity': line.purity_id.id,
                        'selling_making_charge': line.make_value,
                        # 'lot_id': lot_id,
                        'product_uom_qty': abs(line.qty),
                        'state': 'draft',
                        'location_id': location_id if line.qty >= 0 else destination_id,
                        'location_dest_id': destination_id if line.qty >= 0 else return_pick_type != picking_type and return_pick_type.default_location_dest_id.id or location_id,
                    })


            # prefer associating the regular order picking, not the return
            order.write({'picking_id': order_picking.id or return_picking.id})
            # print("order_picking,return_picking")
            # print(order_picking,return_picking)

            if return_picking:
                order._force_picking_done(return_picking)
            if order_picking:
                order._force_picking_done(order_picking)

            # when the pos.config has no picking_type_id set only the moves will be created
            if moves and not return_picking and not order_picking:
                moves._action_assign()
                moves.filtered(lambda m: m.product_id.tracking == 'none')._action_done()

        return True

class AccountInvoiceLine(models.Model):
    _inherit = 'account.move.line'

    pack_lot_ids = fields.One2many('pos.pack.operation.lot', 'account_move_line_id', string='Lot/serial Number')


class PosOrderLineLot(models.Model):
    _inherit = "pos.pack.operation.lot"

    account_move_line_id = fields.Many2one('account.move.line')

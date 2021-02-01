# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError

class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'
    scrap_state_read = fields.Boolean(compute="_compute_scrap_state_read")
    @api.onchange('product_id')
    def _compute_scrap_state_read(self):
        for this in self:
            if this.product_id and this.product_id.categ_id.is_scrap:
                this.scrap_state_read = True
            elif this.product_id and not this.product_id.categ_id.is_scrap:
                this.scrap_state_read = False
    is_full_paid = fields.Boolean()
    paid_gross = fields.Float( digits=(16, 3))
    paid_pure = fields.Float( digits=(16, 3))
    @api.onchange('paid_gross')
    def onchange_paid_gross(self):
        # print("<<<<<<>>>>>>>>>")
        # print("<<<<<<>>>>>>>>>")
        # print("<<<<<<>>>>>>>>>")
        # print("<<<<<<>>>>>>>>>")
        # print("<<<<<<>>>>>>>>>")
        # print("<<<<<<>>>>>>>>>")
        for rec in self:
            rec.write({'paid_pure': rec.paid_gross  *  (rec.purity / 1000)})





    incoming_flag = fields.Boolean(compute="_compute_incoming_flag")
    def _compute_incoming_flag(self):
        for this in self:
            if this.product_qty <= 0:
                this.incoming_flag = False
            else:
                sml = self.env['stock.move.line'].search([('lot_id','=',this.id)])
                if sml:
                    for line in sml:
                        if line.move_id.picking_id.picking_type_id.code == 'incoming':
                            this.incoming_flag = True
                        else:
                            this.incoming_flag = False
                else:
                    this.incoming_flag = False

class stockGoldMove(models.TransientModel):
    _name = 'stock.move.gold'
    _description = 'Generate move for all selected moves'

    move_ids = fields.Many2many('stock.production.lot', 'production_lot_stock_rel', 'stock_gold_id', 'production_lot_id',  'moves', readonly=False)
    pure_weight = fields.Float('Pure Weight', digits=(16, 3))
    pure_remainning = fields.Float('Pure Remainning',compute="get_pure_weight_remain", digits=(16, 3))

    @api.depends('move_ids')
    def get_pure_weight_remain(self):
        pure_in_form = 0.00
        active_ids = self._context.get('active_ids') or self._context.get('active_id')
        account_move = self.env['account.move'].browse(active_ids)
        for rec in self.move_ids:
            pure_in_form = pure_in_form + rec.paid_pure
        self.pure_remainning = self.pure_weight - account_move.pure_wt_value_paid - pure_in_form


    def compute_sheet(self):
        [data] = self.read()
        if not data['move_ids']:
            raise UserError(_("You must select move(s) to generate payment(s)."))

        active_id = self.env.context.get('active_id')

        if active_id:
            account_move = self.env['account.move'].search([('id' ,'=', active_id)])
            purchase_order = self.env['purchase.order'].search([('name','=' ,account_move.invoice_origin)])

        # pure = 0.00
        # gross_weight = 0.00
        # purity = 0.00
        move_lines = []
        move_line_ids_without_package = []
        for move in self.env['stock.production.lot'].browse(data['move_ids']):
            paid_pure = move.paid_pure
            paid_gross = move.paid_gross
            gross_weight =  move.gross_weight
            purity = move.purity
            product_id = move.product_id
            remain = move.gross_weight - move.paid_gross
            if  move.paid_gross > move.gross_weight:
                raise UserError(_("paid gross grater than gross weight "))
            if  move.paid_pure > move.pure_weight:
                raise UserError(_("paid pure grater than pure weight "))
            move_lines.append((0, 0, {
                    'name': "unfixed move",
                    'location_id': purchase_order.order_type.stock_picking_type_id.default_location_src_id.id,
                    'location_dest_id': purchase_order.order_type.stock_picking_type_id.default_location_dest_id.id,
                    'product_id': product_id.id,
                    'product_uom': product_id.uom_id.id,
                    'picking_type_id':  purchase_order.order_type.stock_picking_type_id.id,
                    'product_uom_qty': paid_gross,
                    # 'gold_rate' : rate ,
                    'pure_weight': paid_pure,
                    'gross_weight': paid_gross ,
                    'purity': purity,
                    'lot_id':move.id}))
            move_line_ids_without_package.append((0, 0, {
                    'location_id': purchase_order.order_type.stock_picking_type_id.default_location_src_id.id,
                    'location_dest_id': purchase_order.order_type.stock_picking_type_id.default_location_dest_id.id,
                    'product_id': product_id.id,
                    'product_uom_id': product_id.uom_id.id,
                    'product_uom_qty': paid_gross,
                    # 'gold_rate' : rate ,
                    'pure_weight': paid_pure,
                    'gross_weight': paid_gross ,
                    'purity': purity,
                    'lot_id': move.id}))

            # move.write({'gross_weight': move.gross_weight -  move.paid_gross})
            move.write({'pure_weight': move.pure_weight -  move.paid_pure})
            move.write({'paid_gross': 0.00 ,'paid_pure' : 0.00})
            # move.write({'paid_gross': 0.00 ,'paid_pure' : 0.00})
            # if move.gross_weight <= 0.00 or move.pure_weight <= 0.00:
                # move.write({'is_full_paid': True})
        account_move.write({'pure_wt_value': account_move.pure_wt_value - paid_pure })
        # pure_money = account_move.pure_wt_value * account_move.gold_rate_value
        # account_move.write({'make_value_move': account_move.make_value_move - pure_money })

        if account_move.pure_wt_value <= 0.00 and account_move.make_value_move <= 0.00:
            account_move.write({'invoice_payment_state': "paid"})

        if not purchase_order.order_type.stock_picking_type_id :
            raise UserError(_("fill picking type field in po purhcase type"))
        rate = 0.00
        for line in purchase_order.order_line:
            if line.gold_rate > 0.00:
                rate = line.gold_rate

        if paid_pure > 0.00:
            if remain >= 0:
                picking = self.env['stock.picking'].create({
                        'location_id': purchase_order.order_type.stock_picking_type_id.default_location_src_id.id,
                        'location_dest_id': purchase_order.order_type.stock_picking_type_id.default_location_dest_id.id,
                        'picking_type_id': purchase_order.order_type.stock_picking_type_id.id,
                        'bill_unfixed': account_move.id,
                        'immediate_transfer': False,
                        'move_lines': move_lines,
                        # 'move_line_ids_without_package':move_line_ids_without_package,
                        })
                picking.action_confirm()
                picking.action_assign()
                for this in picking:
                    for this_lot_line in this.move_line_ids_without_package:
                        this_lot_line.lot_id = this_lot_line.move_id.lot_id.id
                if account_move.unfixed_stock_picking_two and not account_move.unfixed_stock_picking_three:
                    account_move.write({'unfixed_stock_picking_three': picking.id})
                if account_move.unfixed_stock_picking and not account_move.unfixed_stock_picking_two and not account_move.unfixed_stock_picking_three:
                    account_move.write({'unfixed_stock_picking_two': picking.id})
                if not account_move.unfixed_stock_picking and not account_move.unfixed_stock_picking_two and not account_move.unfixed_stock_picking_three:
                    account_move.write({'unfixed_stock_picking': picking.id})
                return picking.button_validate()
            elif remain < 0:
                raise UserError(_("Sorry please review your inputs , you are trying to deliver quant more than you have "))
            # else:
            #     Move = self.env['stock.move'].create({
            #                     'name': "unfixed move",
            #                     'location_id': purchase_order.order_type.stock_picking_type_id.default_location_src_id.id,
            #                     'location_dest_id': purchase_order.order_type.stock_picking_type_id.default_location_dest_id.id,
            #                     'product_id': product_id.id,
            #                     'product_uom': product_id.uom_id.id,
            #                     'picking_type_id':  purchase_order.order_type.stock_picking_type_id.id,
            #
            #                     'product_uom_qty': 0,
            #
            #                     'gold_rate' : rate ,
            #                     'pure_weight': pure,
            #                     'gross_weight': gross_weight ,
            #                     'purity': purity,})


            #account_move.write({'unfixed_stock_picking' : picking.id})
        return {'type': 'ir.actions.act_window_close'}

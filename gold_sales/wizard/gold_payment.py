# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError

# class stockGoldLine(models.TransientModel):
#     _name = 'stock.line.gold.sale'
#
#     product_id = fields.Many2one('product.product')
#     purity_id = fields.Many2one('gold.purity')
#     purity = fields.Float()
#     lot_id = fields.Many2one('stock.production.lot')
#     @api.onchange('lot_id')
#     def retrive_lot(self):
#         if self.lot_id:
#             self.purity_id = self.lot_id.purity_id.id
#             self.purity = self.lot_id.purity_id.scrap_purity
#     gross_weight = fields.Float(digits=(16, 3))
#     pure_weight = fields.Float(digits=(16, 3))

class stockGoldMove(models.TransientModel):
    _name = 'stock.move.gold.sale'
    _description = 'Generate move for all selected moves'

    move_ids = fields.Many2many('stock.production.lot', 'production_lot_stock_sale_rel', 'stock_gold_id', 'production_lot_id',  'moves', readonly=False)
    location_id = fields.Many2one('stock.location', required=True)
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
            sale_order = self.env['sale.order'].search([('name','=' ,account_move.invoice_origin)])
        # lot = self.env['stock.production.lot']
        # if self.lot_state == 'new':
        #     lot = self.env['stock.production.lot'].create({
        #     'name':self.lot_name,
        #     'product_id':self.product_id.id,
        #     'product_qty':1,
        #     'product_uom_id':self.product_id.uom_id.id,
        #     'gross_weight':self.gross_weight,
        #     'purity':self.purity_id.purity,
        #     'purity_id':self.purity_id.id,
        #     'pure_weight':self.pure_weight,
        #     })
        # else:
        #     lot = self.lot_id
        move_lines = []
        # move_lines.append((0, 0, {
        #         'name': "unfixed move",
        #         'location_id': sale_order.order_type.stock_picking_type_id.default_location_src_id.id,
        #         'location_dest_id': sale_order.order_type.stock_picking_type_id.default_location_dest_id.id,
        #         'product_id': self.product_id.id,
        #         'product_uom': self.product_id.uom_id.id,
        #         'picking_type_id':  sale_order.order_type.stock_picking_type_id.id,
        #         'product_uom_qty': self.gross_weight,
        #         'pure_weight': self.pure_weight,
        #         'gross_weight': self.gross_weight ,
        #         'purity': self.purity_id.scrap_purity,
        #         'lot_id':lot.id}))
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
                    'location_id': sale_order.order_type.stock_picking_type_id.default_location_src_id.id,
                    'location_dest_id': self.location_id.id,
                    'product_id': product_id.id,
                    'product_uom': product_id.uom_id.id,
                    'picking_type_id':  sale_order.order_type.stock_picking_type_id.id,
                    'product_uom_qty': paid_gross,
                    # 'gold_rate' : rate ,
                    'pure_weight': paid_pure,
                    'gross_weight': paid_gross ,
                    'purity': purity,
                    'lot_id':move.id}))
            # move_line_ids_without_package.append((0, 0, {
            #         'location_id': sale_order.order_type.stock_picking_type_id.default_location_src_id.id,
            #         'location_dest_id': sale_order.order_type.stock_picking_type_id.default_location_dest_id.id,
            #         'product_id': product_id.id,
            #         'product_uom_id': product_id.uom_id.id,
            #         'product_uom_qty': paid_gross,
            #         # 'gold_rate' : rate ,
            #         'pure_weight': paid_pure,
            #         'gross_weight': paid_gross ,
            #         'purity': purity,
            #         'lot_id': move.id}))

            # move.write({'gross_weight': move.gross_weight -  move.paid_gross})
            move.write({'pure_weight': move.pure_weight -  move.paid_pure})
            move.write({'paid_gross': 0.00 ,'paid_pure' : 0.00})
            # move.write({'paid_gross': 0.00 ,'paid_pure' : 0.00})
            # if move.gross_weight <= 0.00 or move.pure_weight <= 0.00:
                # move.write({'is_full_paid': True})
        # account_move.write({'pure_wt_value': account_move.pure_wt_value - self.pure_weight })
        account_move.write({'pure_wt_value': account_move.pure_wt_value - paid_pure })

        if account_move.pure_wt_value <= 0.00 and account_move.make_value_move <= 0.00:
            account_move.write({'invoice_payment_state': "paid"})
        if not sale_order.order_type.stock_picking_type_id :
            raise UserError(_("fill picking type field in so sale type"))
        rate = 0.00
        for line in sale_order.order_line:
            if line.gold_rate > 0.00:
                rate = line.gold_rate
        if paid_pure > 0.00:
            if remain >= 0:
                picking = self.env['stock.picking'].create({
                        'location_id': sale_order.order_type.stock_picking_type_id.default_location_src_id.id,
                        'location_dest_id': self.location_id.id,
                        'picking_type_id': sale_order.order_type.stock_picking_type_id.id,
                        'invoice_unfixed': account_move.id,
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
            #                     'location_id': sale_order.order_type.stock_picking_type_id.default_location_src_id.id,
            #                     'location_dest_id': sale_order.order_type.stock_picking_type_id.default_location_dest_id.id,
            #                     'product_id': product_id.id,
            #                     'product_uom': product_id.uom_id.id,
            #                     'picking_type_id':  sale_order.order_type.stock_picking_type_id.id,
            #
            #                     'product_uom_qty': 0,
            #
            #                     'gold_rate' : rate ,
            #                     'pure_weight': pure,
            #                     'gross_weight': gross_weight ,
            #                     'purity': purity,})


            #account_move.write({'unfixed_stock_picking' : picking.id})
        return {'type': 'ir.actions.act_window_close'}
        # if self.pure_weight > 0.00:
        #     picking = self.env['stock.picking'].create({
        #             'location_id': sale_order.order_type.stock_picking_type_id.default_location_src_id.id,
        #             'location_dest_id': sale_order.order_type.stock_picking_type_id.default_location_dest_id.id,
        #             'picking_type_id': sale_order.order_type.stock_picking_type_id.id,
        #             'invoice_unfixed': account_move.id,
        #             'immediate_transfer': False,
        #             'move_lines': move_lines,
        #             })
        #     picking.action_confirm()
        #     picking.action_assign()
        #     for this in picking:
        #         for this_lot_line in this.move_line_ids_without_package:
        #             this_lot_line.lot_id = this_lot_line.move_id.lot_id.id
        #     if account_move.unfixed_stock_picking_two and not account_move.unfixed_stock_picking_three:
        #         account_move.write({'unfixed_stock_picking_three': picking.id})
        #     if account_move.unfixed_stock_picking and not account_move.unfixed_stock_picking_two and not account_move.unfixed_stock_picking_three:
        #         account_move.write({'unfixed_stock_picking_two': picking.id})
        #     if not account_move.unfixed_stock_picking and not account_move.unfixed_stock_picking_two and not account_move.unfixed_stock_picking_three:
        #         account_move.write({'unfixed_stock_picking': picking.id})
        #     return picking.button_validate()
        # return {'type': 'ir.actions.act_window_close'}

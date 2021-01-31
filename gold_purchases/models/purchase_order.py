# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import date , timedelta , datetime
from odoo.exceptions import ValidationError,UserError
import logging
_logger = logging.getLogger(__name__)





class assemblyDescriptionGold(models.Model):
    """docstring for assemblyDescriptionGold."""
    _name = 'assembly.description.gold'

    product_id = fields.Many2one('product.product')
    quantity = fields.Float(digits=(16,3))
    gross_weight = fields.Float(digits=(16,3))
    pure_weight = fields.Float(digits=(16,3))
    purity_id = fields.Many2one('gold.purity')
    @api.onchange('purity_id')
    def get_values_gold(self):
        if self.purity_id:
            if self.product_id.scrap:
                self.purity = self.scrap_purity
                self.pure_weight = self.gross_weight * (self.purity / 1000)
            elif self.product_id.gold and not self.product_id.scrap:
                self.purity = self.purity
                self.pure_weight = self.gross_weight * (self.purity / 1000)

    our_stock = fields.Boolean(default=False)
    purity = fields.Float(digits=(16,3))
    polish_rhodium = fields.Float('Polish & Rhodium',digits=(16,3))
    purchase_id_gold = fields.Many2one('purchase.order')

class assemblyDescriptionDiamond(models.Model):
    """docstring for assemblyDescriptionDiamond."""
    _name = 'assembly.description.diamond'

    def unlink(self):
        if self.our_stock:
            raise ValidationError(_('You can not remove a line you already processed'))
        else:
            return super(assemblyDescriptionDiamond, self).unlink()

    product_id = fields.Many2one('product.product')
    carat = fields.Float(digits=(16,3))
    carat_price = fields.Float(digits=(16,3))
    stones_value = fields.Float(digits=(16,3))
    @api.onchange('carat_price')
    def calc_stones_value(self):
        self.stones_value = self.carat * self.carat_price
    stones_quantity = fields.Float(digits=(16,3))
    stone_setting_rate = fields.Float(digits=(16,3))
    stone_setting_value = fields.Float(digits=(16,3))
    @api.onchange('stone_setting_rate')
    def cacl__stone_setting_value(self):
        self.stone_setting_value = self.stone_setting_rate * self.stones_quantity
    our_stock = fields.Boolean(default=False)
    purchase_id_diamond = fields.Many2one('purchase.order')

class assemblyBackGold(models.Model):
    """docstring for assemblyBackGold."""
    _name = 'assembly.back.component.gold'
    purchase_back_gold_id = fields.Many2one('purchase.order')
    product_id = fields.Many2one('product.product')
    # lot_state = fields.Selection([('exist','Existing Lot'),('new','New Lot')])
    # lot_id = fields.Many2one('stock.production.lot')
    # lot_name = fields.Char()
    gold_rate = fields.Float(digits=(16,3),compute="_compute_rate")
    gross_weight = fields.Float(digits=(16,3))
    purity_id = fields.Many2one('gold.purity')
    purity = fields.Float(digits=(16,3))
    pure_weight = fields.Float(digits=(16,3), compute="_compute_pure_weight")
    total_value = fields.Float(digits=(16,3), compute="_compute_total_vale")

    def _compute_rate(self):
        for this in self:
            this.gold_rate = this.purchase_back_gold_id.gold_rate/1000
    @api.onchange('gross_weight','purity_id')
    def _compute_pure_weight(self):
        for this in self:
            if this.purity_id:
                this.purity = this.purity_id.scrap_purity
            this.pure_weight = this.gross_weight * (this.purity / 1000)

    # @api.onchange('lot_id')
    # def getvalues(self):
    #     if self.product_id and self.lot_id:
    #         self.gross_weight = self.lot_id.gross_weight
    #         self.purity_id = self.lot_id.purity_id.id
    #         self.purity = self.lot_id.purity
    #         self.pure_weight = self.lot_id.pure_weight
    def _compute_total_vale(self):
        for this in self:
            this.total_value = this.gross_weight * this.gold_rate

class assemblyBackDiamond(models.Model):
    """docstring for assemblyBackDiamond."""
    _name = 'assembly.back.component.diamond'
    purchase_back_diamond_id = fields.Many2one('purchase.order')
    product_id = fields.Many2one('product.product')
    # lot_state = fields.Selection([('exist','Existing Lot'),('new','New Lot')])
    # lot_id = fields.Many2one('stock.production.lot')
    # lot_name = fields.Char()
    carat = fields.Float(digits=(16,3))
    carat_cost = fields.Float(digits=(16,3))
    total_cost = fields.Float(compute="_compute_total_vale")

    # @api.onchange('lot_id')
    # def getvalues(self):
    #     if self.product_id and self.lot_id:
    #         self.carat = self.lot_id.carat
    @api.onchange('carat','carat_cost')
    def _compute_total_vale(self):
        for this in self:
            this.total_cost = this.carat * this.carat_cost


class assemblyComponentsGold(models.Model):
    """Assembly Details."""
    _name = 'assembly.component.gold'

    product_id = fields.Many2one('product.product')
    location_id = fields.Many2one('stock.location', required=True)
    lot_id = fields.Many2one('stock.production.lot')
    product_uom_qty = fields.Float(digits=(16,3))
    gross_weight = fields.Float(digits=(16,3))
    pure_weight = fields.Float(digits=(16,3))
    purity = fields.Float(digits=(16,3))
    purchase_gold_id = fields.Many2one('purchase.order')

    @api.onchange('gross_weight','purity')
    def compute_purity_pure(self):
            self.pure_weight = self.gross_weight * (self.purity / 1000)
    @api.onchange('lot_id')
    def getvalues(self):
        if self.product_id and self.lot_id:
            self.product_uom_qty = self.lot_id.product_qty
            self.gross_weight = self.lot_id.gross_weight
            self.purity = self.lot_id.purity
            self.pure_weight = self.lot_id.pure_weight

class assemblyComponentsDiamond(models.Model):
    """Assembly Details."""
    _name = 'assembly.component.diamond'

    product_id = fields.Many2one('product.product')
    location_id = fields.Many2one('stock.location', required=True)
    lot_id = fields.Many2one('stock.production.lot')
    stones_quantity = fields.Float(digits=(16,3), string="Stones")
    carat = fields.Float(digits=(16,3), string="Carat")
    stones_quantity_ret = fields.Float(default=0.0, digits=(16,3), string="Returned Stones")
    carat_ret = fields.Float(default=0.0, digits=(16,3), string="Returned Carat")
    final_net_stones_quantity = fields.Float(digits=(16,3), compute="_compute_final_net")
    final_net_carat = fields.Float(digits=(16,3), compute="_compute_final_net")
    purchase_diamond_id = fields.Many2one('purchase.order')

    def _compute_final_net(self):
        for this in self:
            this.final_net_stones_quantity = this.stones_quantity - this.stones_quantity_ret
            this.final_net_carat = this.carat - this.carat_ret

    # @api.onchange('lot_id')
    # def getvalues(self):
    #     if self.product_id and self.lot_id:
    #         self.carat = self.lot_id.carat

class assemblyComponentsMix(models.Model):
    """Assembly Details."""
    _name = 'assembly.component.mix'

    product_id = fields.Many2one('product.product')
    location_id = fields.Many2one('stock.location', required=True)
    lot_id = fields.Many2one('stock.production.lot')
    quantity = fields.Float(digits=(16,3), default=1)
    purchase_mix_id = fields.Many2one('purchase.order')

class assemblyComponentsDiamond(models.Model):
    """Assembly Details."""
    _name = 'assembly.back.component.mix'

    product_id = fields.Many2one('product.product')
    location_id = fields.Many2one('stock.location', required=True)
    purchase_back_mix_id = fields.Many2one('purchase.order')


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'
    state = fields.Selection([
        ('draft', 'RFQ'),
        ('processing', 'In Progress'),
        ('receive','Received'),
        ('review','Reviewing'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)
    # state = fields.Selection(selection_add=[])
    def process(self):
        self.state = 'processing'
        need_location = False
        for line in self.assembly_gold_ids:
            if not line.location_id:
                need_location = True
        for line in self.assembly_diamond_ids:
            if not line.location_id:
                need_location = True
        if need_location:
            raise (_('Please fill the location at the component lines'))
        diamond_move_lines = []
        scrap_move_lines = []
        gold_move_lines = []
        mix_move_lines = []
        gold_components = self.assembly_gold_ids.filtered(lambda x: x.product_id and
                                                       x.product_id.gold and
                                                       x.product_id.categ_id and
                                                       x.product_id.categ_id.is_gold)
        scrap_components = self.assembly_gold_ids.filtered(lambda x: x.product_id and
                                                       x.product_id.gold and
                                                       x.product_id.categ_id and
                                                       x.product_id.categ_id.is_scrap)
        diamond_components = self.assembly_diamond_ids
        mix_components = self.assembly_mix_ids

        internal_locations = self.env['stock.location'].search([('usage','=','internal')])
        for location in internal_locations:
            location_gold_components = gold_components.filtered(lambda x: x.location_id == location)
            location_scrap_components = scrap_components.filtered(lambda x: x.location_id == location)
            location_diamond_components = diamond_components.filtered(lambda x: x.location_id == location)
            location_mix_components = mix_components.filtered(lambda x: x.location_id == location)
            if len(location_gold_components) > 0:
                sale_type = ""
                if self.order_type.is_fixed:
                    sale_type = 'fixed'
                elif self.order_type.is_unfixed:
                    sale_type = 'unfixed'
                for line in location_gold_components:
                    gold_move_lines.append((0, 0, {
                            'name': "assembly move",
                            'location_id': location.id,
                            'location_dest_id': self.order_type.assembly_picking_type_id.default_location_dest_id.id,
                            'product_id': line.product_id.id,
                            'product_uom': line.product_id.uom_id.id,
                            'picking_type_id':  self.order_type.assembly_picking_type_id.id,
                            'product_uom_qty': line.product_uom_qty,
                            'gross_weight' : line.gross_weight ,
                            'pure_weight': line.pure_weight,
                            'purity': line.purity,
                            'lot_id':line.lot_id.id,
                            'gold_rate':line.purchase_gold_id.gold_rate / 1000,
                            'origin': location.name + ' - Assembly Gold Transfer'
                            }))
                picking = self.env['stock.picking'].create({
                            'partner_id': self.partner_id.id,
                            'location_id': location.id,
                            'location_dest_id': self.order_type.assembly_picking_type_id.default_location_dest_id.id,
                            'picking_type_id':  self.order_type.assembly_picking_type_id.id,
                            'immediate_transfer': False,
                            'move_lines': gold_move_lines,
                            'sale_type':sale_type,
                            'origin': location.name + ' - Assembly Gold Transfer'
                        })
                picking.action_confirm()
                picking.action_assign()
                for this in picking:
                    for this_lot_line in this.move_line_ids_without_package:
                        this_lot_line.lot_id = this_lot_line.move_id.lot_id.id
                picking.assembly_purchase_id = self.id
            if len(location_scrap_components) > 0:
                sale_type = ""
                if self.order_type.is_fixed:
                    sale_type = 'fixed'
                elif self.order_type.is_unfixed:
                    sale_type = 'unfixed'
                for line in location_scrap_components:
                    scrap_move_lines.append((0, 0, {
                            'name': "assembly move",
                            'location_id': location.id,
                            'location_dest_id': self.order_type.assembly_picking_type_id.default_location_dest_id.id,
                            'product_id': line.product_id.id,
                            'product_uom': line.product_id.uom_id.id,
                            'picking_type_id':  self.order_type.assembly_picking_type_id.id,
                            'product_uom_qty': line.gross_weight,
                            'gross_weight' : line.gross_weight ,
                            'pure_weight': line.pure_weight,
                            'purity': line.purity,
                            'lot_id':line.lot_id.id,
                            'gold_rate':line.purchase_gold_id.gold_rate / 1000,
                            'origin': location.name + ' - Assembly Scrap Transfer'
                            }))
                picking = self.env['stock.picking'].create({
                            'partner_id': self.partner_id.id,
                            'location_id': location.id,
                            'location_dest_id': self.order_type.assembly_picking_type_id.default_location_dest_id.id,
                            'picking_type_id':  self.order_type.assembly_picking_type_id.id,
                            'immediate_transfer': False,
                            'move_lines': scrap_move_lines,
                            'sale_type':sale_type,
                            'origin': location.name + ' - Assembly Scrap Transfer'
                        })
                picking.action_confirm()
                picking.action_assign()
                for this in picking:
                    for this_lot_line in this.move_line_ids_without_package:
                        this_lot_line.lot_id = this_lot_line.move_id.lot_id.id
                picking.assembly_purchase_id = self.id
            if len(location_diamond_components) > 0:
                for line in location_diamond_components:
                    diamond_move_lines.append((0, 0, {
                            'name': "assembly move",
                            'location_id': location.id,
                            'location_dest_id': self.order_type.assembly_picking_type_id.default_location_dest_id.id,
                            'product_id': line.product_id.id,
                            'product_uom': line.product_id.uom_id.id,
                            'picking_type_id':  self.order_type.assembly_picking_type_id.id,
                            'carat':line.carat,
                            'product_uom_qty': line.carat,
                            'lot_id':line.lot_id.id,
                            'origin': location.name + ' - Assembly Stone Transfer',
                            }))
                picking = self.env['stock.picking'].create({
                            'partner_id': self.partner_id.id,
                            'location_id': location.id,
                            'location_dest_id': self.order_type.assembly_picking_type_id.default_location_dest_id.id,
                            'picking_type_id':  self.order_type.assembly_picking_type_id.id,
                            'immediate_transfer': False,
                            'move_lines': diamond_move_lines,
                            'origin': location.name + ' - Assembly Stone Transfer'
                        })
                picking.action_confirm()
                picking.action_assign()
                for this in picking:
                    for this_lot_line in this.move_line_ids_without_package:
                        this_lot_line.lot_id = this_lot_line.move_id.lot_id.id
                picking.assembly_purchase_id = self.id

            if len(location_mix_components) > 0:
                for line in location_mix_components:
                    mix_move_lines.append((0, 0, {
                            'name': "assembly move",
                            'location_id': location.id,
                            'location_dest_id': self.order_type.assembly_picking_type_id.default_location_dest_id.id,
                            'product_id': line.product_id.id,
                            'product_uom': line.product_id.uom_id.id,
                            'picking_type_id':  self.order_type.assembly_picking_type_id.id,
                            'product_uom_qty': line.quantity,
                            'lot_id':line.lot_id.id,
                            'origin': location.name + ' - Assembly Mix Transfer',
                            }))
                picking = self.env['stock.picking'].create({
                            'partner_id': self.partner_id.id,
                            'location_id': location.id,
                            'location_dest_id': self.order_type.assembly_picking_type_id.default_location_dest_id.id,
                            'picking_type_id':  self.order_type.assembly_picking_type_id.id,
                            'immediate_transfer': False,
                            'move_lines': mix_move_lines,
                            'origin': location.name + ' - Assembly Mix Transfer'
                        })
                picking.action_confirm()
                picking.action_assign()
                for this in picking:
                    for this_lot_line in this.move_line_ids_without_package:
                        this_lot_line.lot_id = this_lot_line.move_id.lot_id.id
                picking.assembly_purchase_id = self.id
        stone_description_lines = []
        for line in self.assembly_diamond_ids:
            stone_description_lines.append((0,0,{
            'product_id':line.product_id.id,
            'stones_quantity':line.final_net_stones_quantity,
            'carat':line.final_net_carat,
            'our_stock':True
            }))
        gold_description_lines = []
        for line in self.assembly_gold_ids:
            gold_description_lines.append((0,0,{
            'product_id':line.product_id.id,
            'our_stock':True
            }))
        self.write({'assembly_description_gold':[(5)]})
        self.write({'assembly_description_gold':gold_description_lines})
        self.write({'assembly_description_diamond':[(5)]})
        self.write({'assembly_description_diamond':stone_description_lines})
    assembly_back_gold_ids = fields.One2many('assembly.back.component.gold','purchase_back_gold_id')
    assembly_back_diamond_ids = fields.One2many('assembly.back.component.diamond','purchase_back_diamond_id')
    assembly_back_mix_ids = fields.One2many('assembly.back.component.mix','purchase_back_mix_id')

    def return_component(self):
        diamond_move_lines = []
        scrap_move_lines = []
        gold_move_lines = []
        gold_components = self.assembly_back_gold_ids.filtered(lambda x: x.product_id and
                                                       x.product_id.gold and
                                                       x.product_id.categ_id and
                                                       x.product_id.categ_id.is_gold)
        scrap_components = self.assembly_back_gold_ids.filtered(lambda x: x.product_id and
                                                       x.product_id.gold and
                                                       x.product_id.categ_id and
                                                       x.product_id.categ_id.is_scrap)
        diamond_components = self.assembly_diamond_ids
        if len(gold_components) > 0:
            sale_type = ""
            if self.order_type.is_fixed:
                sale_type = 'fixed'
            elif self.order_type.is_unfixed:
                sale_type = 'unfixed'
            for line in gold_components:
                # lot = self.env['stock.production.lot']
                # if line.lot_state == 'new':
                #     lot = self.env['stock.production.lot'].create({
                #     'name':line.lot_name,
                #     'product_id':line.product_id.id,
                #     'product_qty':1,
                #     'product_uom_id':line.product_id.uom_id.id,
                #     'gross_weight':line.gross_weight,
                #     'purity':line.purity_id.purity,
                #     'purity_id':line.purity_id.id,
                #     'pure_weight':line.pure_weight,
                #     })
                # else:
                #     lot = line.lot_id
                gold_move_lines.append((0, 0, {
                        'name': "assembly move",
                        'location_id': self.order_type.assembly_picking_type_id_back.default_location_src_id.id,
                        'location_dest_id': self.order_type.assembly_picking_type_id_back.default_location_dest_id.id,
                        'product_id': line.product_id.id,
                        'product_uom': line.product_id.uom_id.id,
                        'picking_type_id':  self.order_type.assembly_picking_type_id_back.id,
                        'product_uom_qty': 1,
                        'gross_weight' : line.gross_weight ,
                        'pure_weight': line.pure_weight,
                        'purity': line.purity,
                        # 'lot_id':lot.id,
                        'gold_rate':line.purchase_back_gold_id.gold_rate / 1000,
                        'origin': self.order_type.assembly_picking_type_id_back.default_location_dest_id.name + ' - Receive - Assembly Gold Transfer'
                        }))
            picking = self.env['stock.picking'].create({
                        'partner_id': self.partner_id.id,
                        'location_id': self.order_type.assembly_picking_type_id_back.default_location_src_id.id,
                        'location_dest_id': self.order_type.assembly_picking_type_id_back.default_location_dest_id.id,
                        'picking_type_id':  self.order_type.assembly_picking_type_id_back.id,
                        'immediate_transfer': False,
                        'move_lines': gold_move_lines,
                        'sale_type':sale_type,
                        'origin': self.order_type.assembly_picking_type_id_back.default_location_dest_id.name + ' - Receive - Assembly Gold Transfer'
                    })
            picking.action_confirm()
            picking.action_assign()
            # for this in picking:
            #     for this_lot_line in this.move_line_ids_without_package:
            #         this_lot_line.lot_id = this_lot_line.move_id.lot_id.id
            picking.assembly_purchase_id = self.id
        if len(scrap_components) > 0:
            sale_type = ""
            if self.order_type.is_fixed:
                sale_type = 'fixed'
            elif self.order_type.is_unfixed:
                sale_type = 'unfixed'
            for line in scrap_components:
                # lot = self.env['stock.production.lot']
                # if line.lot_state == 'new':
                #     lot = self.env['stock.production.lot'].create({
                #     'name':line.lot_name,
                #     'product_id':line.product_id.id,
                #     'product_qty':line.gross_weight,
                #     'product_uom_id':line.product_id.uom_id.id,
                #     'gross_weight':line.gross_weight,
                #     'purity':line.purity_id.purity,
                #     'purity_id':line.purity_id.id,
                #     'pure_weight':line.pure_weight,
                #     })
                # else:
                #     lot = line.lot_id
                scrap_move_lines.append((0, 0, {
                        'name': "assembly move",
                        'location_id': self.order_type.assembly_picking_type_id_back.default_location_src_id.id,
                        'location_dest_id': self.order_type.assembly_picking_type_id_back.default_location_dest_id.id,
                        'product_id': line.product_id.id,
                        'product_uom': line.product_id.uom_id.id,
                        'picking_type_id':  self.order_type.assembly_picking_type_id_back.id,
                        'product_uom_qty': line.gross_weight,
                        'gross_weight' : line.gross_weight ,
                        'pure_weight': line.pure_weight,
                        'purity': line.purity,
                        # 'lot_id':lot.id,
                        'gold_rate':line.purchase_back_gold_id.gold_rate / 1000,
                        'origin': self.order_type.assembly_picking_type_id_back.default_location_dest_id.name + ' - Receive - Assembly Scrap Transfer'
                        }))
            picking = self.env['stock.picking'].create({
                        'partner_id': self.partner_id.id,
                        'location_id': self.order_type.assembly_picking_type_id_back.default_location_src_id.id,
                        'location_dest_id': self.order_type.assembly_picking_type_id_back.default_location_dest_id.id,
                        'picking_type_id':  self.order_type.assembly_picking_type_id_back.id,
                        'immediate_transfer': False,
                        'move_lines': scrap_move_lines,
                        'sale_type':sale_type,
                        'origin': self.order_type.assembly_picking_type_id_back.default_location_dest_id.name + ' - Receive - Assembly Scrap Transfer'
                    })
            picking.action_confirm()
            picking.action_assign()
            # for this in picking:
            #     for this_lot_line in this.move_line_ids_without_package:
            #         this_lot_line.lot_id = this_lot_line.move_id.lot_id.id
            picking.assembly_purchase_id = self.id
        if len(diamond_components) > 0:
            for line in diamond_components:
                # lot = self.env['stock.production.lot']
                # if line.lot_state == 'new':
                #     lot = self.env['stock.production.lot'].create({
                #     'name':line.lot_name,
                #     'product_id':line.product_id.id,
                #     'product_qty':line.carat,
                #     'product_uom_id':line.product_id.uom_id.id,
                #     'carat':line.carat
                #     })
                # else:
                #     lot = line.lot_id
                if line.stones_quantity_ret > 0.0 and line.carat_ret > 0.0:
                    diamond_move_lines.append((0, 0, {
                            'name': "assembly move",
                            'location_id': self.order_type.assembly_picking_type_id_back.default_location_src_id.id,
                            'location_dest_id': self.order_type.assembly_picking_type_id_back.default_location_dest_id.id,
                            'product_id': line.product_id.id,
                            'product_uom': line.product_id.uom_id.id,
                            'picking_type_id':  self.order_type.assembly_picking_type_id_back.id,
                            'carat':line.carat,
                            'product_uom_qty': line.carat,
                            # 'lot_id':lot.id,
                            'origin': self.order_type.assembly_picking_type_id_back.default_location_dest_id.name + ' - Receive - Assembly Stone Transfer',
                            }))
            if len(diamond_move_lines) > 0:
                picking = self.env['stock.picking'].create({
                            'partner_id': self.partner_id.id,
                            'location_id': self.order_type.assembly_picking_type_id_back.default_location_src_id.id,
                            'location_dest_id': self.order_type.assembly_picking_type_id_back.default_location_dest_id.id,
                            'picking_type_id':  self.order_type.assembly_picking_type_id_back.id,
                            'immediate_transfer': False,
                            'move_lines': diamond_move_lines,
                            'origin': self.order_type.assembly_picking_type_id_back.default_location_dest_id.name + ' - Receive - Assembly Stone Transfer'
                        })
                picking.action_confirm()
                picking.action_assign()
                # for this in picking:
                #     for this_lot_line in this.move_line_ids_without_package:
                #         this_lot_line.lot_id = this_lot_line.move_id.lot_id.id
                picking.assembly_purchase_id = self.id
        stone_description_lines = []
        for line in self.assembly_diamond_ids:
            stone_description_lines.append((0,0,{
            'product_id':line.product_id.id,
            'stones_quantity':line.final_net_stones_quantity,
            'carat':line.final_net_carat,
            'our_stock':True
            }))
        gold_description_lines = []
        for line in self.assembly_gold_ids:
            gold_description_lines.append((0,0,{
            'product_id':line.product_id.id,
            'our_stock':True
            }))
        self.write({'assembly_description_gold':[(5)]})
        self.write({'assembly_description_gold':gold_description_lines})
        self.write({'assembly_description_diamond':[(5)]})
        self.write({'assembly_description_diamond':stone_description_lines})
        self.state = 'receive'

    def review_assembly(self):
        stone_description_lines = []
        for line in self.assembly_diamond_ids:
            stone_description_lines.append((0,0,{
            'product_id':line.product_id.id,
            'stones_quantity':line.final_net_stones_quantity,
            'carat':line.final_net_carat,
            'carat_price':line.product_id.standard_price,
            'stones_value':line.product_id.standard_price * line.final_net_carat,
            'our_stock':True
            }))
            _logger.info(line.product_id.id)
            _logger.info(line.product_id.name)
        gold_description_lines = []
        for line in self.assembly_gold_ids:
            gold_description_lines.append((0,0,{
            'product_id':line.product_id.id,
            'our_stock':True
            }))
            _logger.info(line.product_id.id)
            _logger.info(line.product_id.name)
        self.write({'assembly_description_gold':[(5)]})
        self.write({'assembly_description_gold':gold_description_lines})
        self.write({'assembly_description_diamond':[(5)]})
        self.write({'assembly_description_diamond':stone_description_lines})
        self.state = 'review'

    def finish_processing(self):
        self.state = 'draft'
        self.ready = True
        total_stones_price = 0.0
        total_stones_labor = 0.0
        total_r_p = 0.0
        # total_make = 0.0
        total_gross = 0.0
        for line in self.assembly_description_diamond:
            total_stones_labor += line.stone_setting_value
            if line.our_stock:
                total_stones_price += line.stones_value
        for line in self.assembly_description_gold:
            total_gross += line.gross_weight
            # total_make += line.make_rate
            total_r_p += line.polish_rhodium
        pol = self.env['purchase.order.line'].search([('order_id','=',self.id)])
        if pol:
            pol[0].write({'d_make_value':total_stones_labor})
            pol[0].write({'polish_rhodium':total_r_p})
            pol[0].write({'price_unit':total_stones_price})
            pol[0].write({'gross_wt':total_gross})
            pol[0].write({'purity_id':self.assembly_description_gold[0].purity_id.id})
        return self.button_confirm()

    ready = fields.Boolean(default=False)
    assembly_description_gold = fields.One2many('assembly.description.gold','purchase_id_gold')
    assembly_description_diamond = fields.One2many('assembly.description.diamond','purchase_id_diamond')
    def action_view_assembly_operations(self):
        """ This function returns an action that display existing picking orders of given purchase order ids. When only one found, show the picking immediately.
        """
        action = self.env.ref('stock.action_picking_tree_all')
        result = action.read()[0]
        # override the context to get rid of the default filtering on operation type
        result['context'] = {'default_partner_id': self.partner_id.id, 'default_picking_type_id': self.order_type.assembly_picking_type_id.id}
        pick_ids = self.env['stock.picking'].search([('assembly_purchase_id','=',self.id)])
        # choose the view_mode accordingly
        if not pick_ids or len(pick_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % (pick_ids.ids)
        elif len(pick_ids) == 1:
            res = self.env.ref('stock.view_picking_form', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state,view) for state,view in result['views'] if view != 'form']
            else:
                result['views'] = form_view
            result['res_id'] = pick_ids.id
        return result
    assembly_operations_count = fields.Float(digits=(16,3), compute="_compute_assembly_operations_count")
    def _compute_assembly_operations_count(self):
        for this in self:
            this.assembly_operations_count = self.env['stock.picking'].search_count([('assembly_purchase_id','=',self.id)])
    assembly_gold_ids = fields.One2many('assembly.component.gold','purchase_gold_id')
    assembly_diamond_ids = fields.One2many('assembly.component.diamond','purchase_diamond_id')
    assembly_mix_ids = fields.One2many('assembly.component.mix','purchase_mix_id')
    assembly_no_giving = fields.Boolean(compute="_compute_assembly_state")
    assembly_give_gold = fields.Boolean(compute="_compute_assembly_state")
    assembly_give_diamond = fields.Boolean(compute="_compute_assembly_state")
    def _compute_assembly_state(self):
        for this in self:
            this.assembly_give_gold = False
            this.assembly_give_diamond = False
            this.assembly_no_giving = False
            if len(this.assembly_gold_ids) > 0:
                this.assembly_give_gold = True
            if len(this.assembly_diamond_ids) > 0:
                this.assembly_give_diamond = True
            if len(this.assembly_gold_ids) == 0 and len(this.assembly_diamond_ids) == 0:
                this.assembly_no_giving = True

    def button_cancel(self):
        res = super(PurchaseOrder, self).button_cancel()
        component_pickings = self.env['stock.picking'].search([('assembly_purchase_id','=',self.id)])
        for picking in component_pickings:
            picking.action_cancel()
        return res
    # def button_confirm(self):
    #     res = super(PurchaseOrder,self).button_confirm()
    #     need_location = False
    #     for line in self.assembly_gold_ids:
    #         if not line.location_id:
    #             need_location = True
    #     for line in self.assembly_diamond_ids:
    #         if not line.location_id:
    #             need_location = True
    #     if need_location:
    #         raise (_('Please fill the location at the component lines'))
    #     diamond_move_lines = []
    #     scrap_move_lines = []
    #     gold_move_lines = []
    #     gold_components = self.assembly_gold_ids.filtered(lambda x: x.product_id and
    #                                                    x.product_id.gold and
    #                                                    x.product_id.categ_id and
    #                                                    x.product_id.categ_id.is_gold)
    #     scrap_components = self.assembly_gold_ids.filtered(lambda x: x.product_id and
    #                                                    x.product_id.gold and
    #                                                    x.product_id.categ_id and
    #                                                    x.product_id.categ_id.is_scrap)
    #     diamond_components = self.assembly_diamond_ids
    #
    #     internal_locations = self.env['stock.location'].search([('usage','=','internal')])
    #     for location in internal_locations:
    #         location_gold_components = gold_components.filtered(lambda x: x.location_id == location)
    #         location_scrap_components = scrap_components.filtered(lambda x: x.location_id == location)
    #         location_diamond_components = diamond_components.filtered(lambda x: x.location_id == location)
    #         if len(location_gold_components) > 0:
    #             sale_type = ""
    #             if self.order_type.is_fixed:
    #                 sale_type = 'fixed'
    #             elif self.order_type.is_unfixed:
    #                 sale_type = 'unfixed'
    #             for line in location_gold_components:
    #                 gold_move_lines.append((0, 0, {
    #                         'name': "assembly move",
    #                         'location_id': location.id,
    #                         'location_dest_id': self.order_type.assembly_picking_type_id.default_location_dest_id.id,
    #                         'product_id': line.product_id.id,
    #                         'product_uom': line.product_id.uom_id.id,
    #                         'picking_type_id':  line.purchase_gold_id.order_type.assembly_picking_type_id.id,
    #                         'product_uom_qty': line.product_uom_qty,
    #                         'gross_weight' : line.gross_weight ,
    #                         'pure_weight': line.pure_weight,
    #                         'purity': line.purity,
    #                         'lot_id':line.lot_id.id,
    #                         'origin': location.name + ' - Assembly Gold Transfer'
    #                         }))
    #             picking = self.env['stock.picking'].create({
    #                         'partner_id': self.partner_id.id,
    #                         'location_id': location.id,
    #                         'location_dest_id': self.order_type.assembly_picking_type_id.default_location_dest_id.id,
    #                         'picking_type_id':  self.order_type.assembly_picking_type_id.id,
    #                         'immediate_transfer': False,
    #                         'move_lines': gold_move_lines,
    #                         'sale_type':sale_type,
    #                         'origin': location.name + ' - Assembly Gold Transfer'
    #                     })
    #             picking.action_confirm()
    #             picking.action_assign()
    #             for this in picking:
    #                 for this_lot_line in this.move_line_ids_without_package:
    #                     this_lot_line.lot_id = this_lot_line.move_id.lot_id.id
    #             picking.assembly_purchase_id = self.id
    #         if len(location_scrap_components) > 0:
    #             sale_type = ""
    #             if self.order_type.is_fixed:
    #                 sale_type = 'fixed'
    #             elif self.order_type.is_unfixed:
    #                 sale_type = 'unfixed'
    #             for line in scrap_move_lines:
    #                 scrap_move_lines.append((0, 0, {
    #                         'name': "assembly move",
    #                         'location_id': location.id,
    #                         'location_dest_id': self.order_type.assembly_picking_type_id.default_location_dest_id.id,
    #                         'product_id': line.product_id.id,
    #                         'product_uom': line.product_id.uom_id.id,
    #                         'picking_type_id':  line.purchase_gold_id.order_type.assembly_picking_type_id.id,
    #                         'product_uom_qty': line.gross_weight,
    #                         'gross_weight' : line.gross_weight ,
    #                         'pure_weight': line.pure_weight,
    #                         'purity': line.purity,
    #                         'lot_id':line.lot_id.id,
    #                         'origin': location.name + ' - Assembly Scrap Transfer'
    #                         }))
    #             picking = self.env['stock.picking'].create({
    #                         'partner_id': self.partner_id.id,
    #                         'location_id': location.id,
    #                         'location_dest_id': self.order_type.assembly_picking_type_id.default_location_dest_id.id,
    #                         'picking_type_id':  self.order_type.assembly_picking_type_id.id,
    #                         'immediate_transfer': False,
    #                         'move_lines': scrap_move_lines,
    #                         'sale_type':sale_type,
    #                         'origin': location.name + ' - Assembly Scrap Transfer'
    #                     })
    #             picking.action_confirm()
    #             picking.action_assign()
    #             for this in picking:
    #                 for this_lot_line in this.move_line_ids_without_package:
    #                     this_lot_line.lot_id = this_lot_line.move_id.lot_id.id
    #             picking.assembly_purchase_id = self.id
    #         if len(location_diamond_components) > 0:
    #             for line in location_diamond_components:
    #                 diamond_move_lines.append((0, 0, {
    #                         'name': "assembly move",
    #                         'location_id': location.id,
    #                         'location_dest_id': self.order_type.assembly_picking_type_id.default_location_dest_id.id,
    #                         'product_id': line.product_id.id,
    #                         'product_uom': line.product_id.uom_id.id,
    #                         'picking_type_id':  line.purchase_diamond_id.order_type.assembly_picking_type_id.id,
    #                         'carat':line.carat,
    #                         'product_uom_qty': line.carat,
    #                         'lot_id':line.lot_id.id,
    #                         'origin': location.name + ' - Assembly Diamond Transfer',
    #                         }))
    #             picking = self.env['stock.picking'].create({
    #                         'partner_id': self.partner_id.id,
    #                         'location_id': location.id,
    #                         'location_dest_id': self.order_type.assembly_picking_type_id.default_location_dest_id.id,
    #                         'picking_type_id':  self.order_type.assembly_picking_type_id.id,
    #                         'immediate_transfer': False,
    #                         'move_lines': diamond_move_lines,
    #                         'origin': location.name + ' - Assembly Diamond Transfer'
    #                     })
    #             picking.action_confirm()
    #             picking.action_assign()
    #             for this in picking:
    #                 for this_lot_line in this.move_line_ids_without_package:
    #                     this_lot_line.lot_id = this_lot_line.move_id.lot_id.id
    #             picking.assembly_purchase_id = self.id
    #     return res

    @api.model
    def create(self, values):
        res = super(PurchaseOrder, self).create(values)
        total_make_rate = 0
        total_qty = 0
        product_charge_gold_list = []
        product_charge_diamond_list = []
        for line in res.order_line:
            if line.product_id and line.product_id.categ_id.is_gold:
                product_charge_gold_list.append(line.product_id.making_charge_id.id)
            elif line.product_id and line.product_id.categ_id.is_diamond:
                product_charge_diamond_list.append(line.product_id.making_charge_diamond_id.id)
            else:
                product_charge_gold_list.append(line.product_id.making_charge_id.id)
                product_charge_diamond_list.append(line.product_id.making_charge_diamond_id.id)

        print(product_charge_gold_list)
        print(product_charge_diamond_list)
        done_gold_product = []
        total_charge_gold = []
        for line in product_charge_gold_list:
            if line in done_gold_product:
                continue
            products_for_this_make = self.env['product.product'].search([('making_charge_id','=',line)])
            order_lines_in_this_order = self.env['purchase.order.line'].search([('order_id','=',res.id),('product_id','in',products_for_this_make.ids)])
            for sol in order_lines_in_this_order:
                total_charge_gold.append((sol.make_value,sol.product_id.making_charge_id.id))
            done_gold_product.append(line)

        done_diamond_product = []
        total_charge_diamond = []
        for line in product_charge_diamond_list:
            if line in done_diamond_product:
                continue
            products_for_this_make = self.env['product.product'].search([('making_charge_diamond_id','=',line)])
            order_lines_in_this_order = self.env['purchase.order.line'].search([('order_id','=',res.id),('product_id','in',products_for_this_make.ids)])
            for sol in order_lines_in_this_order:
                total_charge_diamond.append((sol.d_make_value,sol.product_id.making_charge_diamond_id.id))
            done_diamond_product.append(line)

        apply_gold_charge = []
        apply_diamond_charge = []
        gold_charge = False
        diamond_charge = False

        for tup in total_charge_gold:
            if tup[0] > 0.00:
                gold_charge = True
                apply_gold_charge.append(tup)

        for tup in total_charge_diamond:
            if tup[0] > 0.00:
                diamond_charge = True
                apply_diamond_charge.append(tup)
        print(apply_gold_charge)
        print(apply_diamond_charge)
        if gold_charge:
            for pro in apply_gold_charge:
                make_value_product = self.env['product.product'].browse(pro[1])
                uom = self.env.ref('uom.product_uom_unit')
                make = self.env['purchase.order.line'].create({
                                        'product_id': make_value_product.id,
                                        'name': make_value_product.name,
                                        'product_qty': 1,
                                        'price_unit': pro[0],
                                        'product_uom': uom.id,
                                        'order_id':res.id,
                                        'date_planned': datetime.today() ,
                                        'is_make_value': True,
                                        'price_subtotal': pro[0],
                                    })
        if diamond_charge:
            for pro in apply_diamond_charge:
                make_value_product = self.env['product.product'].browse(pro[1])
                uom = self.env.ref('uom.product_uom_unit')
                make = self.env['purchase.order.line'].create({
                                        'product_id': make_value_product.id,
                                        'name': make_value_product.name,
                                        'product_qty': 1,
                                        'price_unit': pro[0],
                                        'product_uom': uom.id,
                                        'order_id':res.id,
                                        'date_planned': datetime.today() ,
                                        'is_make_value': True,
                                        'price_subtotal': pro[0],
                                    })
        return res

    def write(self, values):
        print("WRITE")
        res = super(PurchaseOrder, self).write(values)
        making_order_line = self.env['purchase.order.line'].search([('order_id','=',self.id),('is_make_value','=',True)])
        if self.state not in  ['done','purchase']:
            if making_order_line:
                making_order_line.unlink()
            total_make_rate = 0
            total_qty = 0
            product_charge_gold_list = []
            product_charge_diamond_list = []
            for line in self.order_line:
                if line.product_id and line.product_id.categ_id.is_gold:
                    product_charge_gold_list.append(line.product_id.making_charge_id.id)
                elif line.product_id and line.product_id.categ_id.is_diamond:
                    product_charge_diamond_list.append(line.product_id.making_charge_diamond_id.id)
                else:
                    product_charge_gold_list.append(line.product_id.making_charge_id.id)
                    product_charge_diamond_list.append(line.product_id.making_charge_diamond_id.id)

            print(product_charge_gold_list)
            print(product_charge_diamond_list)

            done_gold_product = []
            total_charge_gold = []
            for line in product_charge_gold_list:
                if line in done_gold_product:
                    continue
                products_for_this_make = self.env['product.product'].search([('making_charge_id','=',line)])
                order_lines_in_this_order = self.env['purchase.order.line'].search([('order_id','=',self.id),('product_id','in',products_for_this_make.ids)])
                for sol in order_lines_in_this_order:
                    total_charge_gold.append((sol.make_value,sol.product_id.making_charge_id.id))
                done_gold_product.append(line)

            done_diamond_product = []
            total_charge_diamond = []
            for line in product_charge_diamond_list:
                if line in done_diamond_product:
                    continue
                products_for_this_make = self.env['product.product'].search([('making_charge_diamond_id','=',line)])
                order_lines_in_this_order = self.env['purchase.order.line'].search([('order_id','=',self.id),('product_id','in',products_for_this_make.ids)])
                for sol in order_lines_in_this_order:
                    total_charge_diamond.append((sol.d_make_value,sol.product_id.making_charge_diamond_id.id))
                done_diamond_product.append(line)

            apply_gold_charge = []
            apply_diamond_charge = []
            gold_charge = False
            diamond_charge = False
            print("______________________________")
            print(total_charge_gold)
            print(total_charge_diamond)
            for tup in total_charge_gold:
                if tup[0] > 0.00:
                    gold_charge = True
                    apply_gold_charge.append(tup)

            for tup in total_charge_diamond:
                if tup[0] > 0.00:
                    diamond_charge = True
                    apply_diamond_charge.append(tup)

            print("****************************")
            print(apply_gold_charge)
            print(apply_diamond_charge)
            if gold_charge:
                for pro in apply_gold_charge:
                    make_value_product = self.env['product.product'].browse(pro[1])
                    uom = self.env.ref('uom.product_uom_unit')
                    make = self.env['purchase.order.line'].create({
                                            'product_id': make_value_product.id,
                                            'name': make_value_product.name,
                                            'product_qty': 1,
                                            'price_unit': pro[0],
                                            'product_uom': uom.id,
                                            'order_id':self.id,
                                            'date_planned': datetime.today() ,
                                            'is_make_value': True,
                                            'price_subtotal': pro[0],
                                        })
            if diamond_charge:
                for pro in apply_diamond_charge:
                    make_value_product = self.env['product.product'].browse(pro[1])
                    uom = self.env.ref('uom.product_uom_unit')
                    make = self.env['purchase.order.line'].create({
                                            'product_id': make_value_product.id,
                                            'name': make_value_product.name,
                                            'product_qty': 1,
                                            'price_unit': pro[0],
                                            'product_uom': uom.id,
                                            'order_id':self.id,
                                            'date_planned': datetime.today() ,
                                            'is_make_value': True,
                                            'price_subtotal': pro[0],
                                        })
            return res
    total_gold_vale_order = fields.Float('Total Value', compute="_compute_total_gold_vale_order")
    def _compute_total_gold_vale_order(self):
        for this in self:
            total = 0.0
            for line in this.order_line:
                if line.product_id.is_making_charges or line.product_id.is_diamond_making_charges:
                    total = total
                else:
                    total = total+line.price_subtotal
            this.total_gold_vale_order = total
    total_make_vale_order = fields.Float('Total labor/Make Value', compute="_compute_total_make_vale_order")
    def _compute_total_make_vale_order(self):
        for this in self:
            total = 0.0
            for line in this.order_line:
                if line.product_id.is_making_charges or line.product_id.is_diamond_making_charges:
                    total = total+line.price_subtotal
                else:
                    total = total
            this.total_make_vale_order = total

    period_from = fields.Float('Period From')
    period_to = fields.Float('Period To')
    period_uom_id = fields.Many2one('uom.uom', 'Period UOM')
    is_gold_fixed = fields.Boolean(string='Is Gold Fixed',
                                   compute='check_gold_fixed')
    stock_move_id = fields.Many2one('account.move', string='Stock Entry – Gold')
    bill_move_id = fields.Many2one('account.move', string='Bill Entry - Gold')

    def action_view_invoice(self):
        '''
        This function returns an action that display existing vendor bills of given purchase order ids.
        When only one found, show the vendor bill immediately.
        '''
        action = self.env.ref('account.action_move_in_invoice_type')
        result = action.read()[0]
        create_bill = self.env.context.get('create_bill', False)
        # override the context to get rid of the default filtering
        # read.is_fixed
        if self.order_type.is_fixed :
            result['context'] = {
                'default_type': 'in_invoice',
                'default_company_id': self.company_id.id,
                'default_purchase_id': self.id,
                'default_purchase_type': "fixed",
            }
        # read.gold
        elif  self.order_type.is_unfixed :
            result['context'] = {
                'default_type': 'in_invoice',
                'default_company_id': self.company_id.id,
                'default_purchase_id': self.id,
                'default_purchase_type': "unfixed",
            }
        else:
            result['context'] = {
                'default_type': 'in_invoice',
                'default_company_id': self.company_id.id,
                'default_purchase_id': self.id,
            }
        # choose the view_mode accordingly
        if len(self.invoice_ids) > 1 and not create_bill:
            result['domain'] = "[('id', 'in', " + str(self.invoice_ids.ids) + ")]"
        else:
            res = self.env.ref('account.view_move_form', False)
            form_view = [(res and res.id or False, 'form')]
            if 'views' in result:
                result['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                result['views'] = form_view
            # Do not set an invoice_id if we want to create a new bill.
            if not create_bill:
                result['res_id'] = self.invoice_ids.id or False
        result['context']['default_invoice_origin'] = self.name
        result['context']['default_ref'] = self.partner_ref
        print("+++++++++++++++++++++++++++++++++++++++++")
        print(result)
        print("+++++++++++++++++++++++++++++++++++++++++")
        return result

    @api.model
    def _prepare_picking(self):
        res = super(PurchaseOrder, self)._prepare_picking()
        res.update({
            'period_from': self.period_from,
            'period_to': self.period_to,
            'period_uom_id': self.period_uom_id and self.period_uom_id.id or False
        })
        # read.gold
        # read.is_unfixed
        if self.order_type.is_unfixed:
            res.update({'purchase_type':'unfixed'})
        elif self.order_type.is_fixed:
            res.update({'purchase_type':'fixed'})
        return res

    @api.depends('order_type')
    def check_gold_fixed(self):
        for rec in self:
            rec.is_gold_fixed = rec.order_type and \
                                rec.order_type.is_fixed or rec.order_type.is_unfixed and \
                                rec.order_type.gold and True or False


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    # diamond_price =fields.Float()
    price_unit = fields.Float(string='Unit Price', required=True,
                              digits='Product Price', copy=False, default=lambda self: self.default_price_unit_get())
    @api.depends('product_id')
    def default_price_unit_get(self):
        for this in self:
            if this.product_id:
                if this.order_id.diamond:
                    return this.product_id.list_price
                else:
                    return 0.00
            else:
                return 0.00

    gross_wt = fields.Float('Gross Wt', digits=(16, 3))
    total_gross_wt = fields.Float('Total Gross', compute='_get_gold_rate' ,digits=(16, 3))
    received_gross_wt = fields.Float('received Gross Wt', digits=(16, 3))
    purity_id = fields.Many2one('gold.purity', 'Purity')
    pure_wt = fields.Float('Pure Wt', compute='_get_gold_rate', digits=(16, 3))
    purity_hall = fields.Float('Purity H', digits=(16, 3))
    purity_diff = fields.Float('Purity +/-', digits=(16, 3))
    total_pure_weight = fields.Float('Pure Weight', compute='_get_gold_rate',
                                     digits=(16, 3))

    def _get_gold_stock(self):
        for this in self:
            if this.product_id and this.purity_id:
                quants = self.env['stock.quant'].search([('product_id','=',this.product_id.id),('location_id','=',8)])
                total = 0.0
                for quant in quants:
                    # print(quant.lot_id.name)
                    # print(quant.inventory_quantity)
                    total = total + quant.inventory_quantity
                this.stock = total
            else:
                this.stock = 0.0

    stock = fields.Float('Stock', digits=(16, 3), compute='_get_gold_stock')
    make_rate = fields.Monetary('Make Rate/G', digits=(16, 3))
    make_value = fields.Monetary('Make Value', compute='_get_gold_rate',
                                 digits=(16, 3), default=0.00)
    polish_rhodium = fields.Float('Polish & Rhodium',digits=(16,3))

    gold_rate = fields.Float('Gold Rate/G', compute='_get_gold_rate',
                             digits=(16, 3))
    gold_value = fields.Monetary('Gold Value', compute='_get_gold_rate',
                                 digits=(16, 3))
    is_make_value = fields.Boolean(string='is_make_value')
    discount = fields.Float()
    total_with_make = fields.Float('Total Value + Make Value', compute="_compute_total_with_make")
    scrap_state_read = fields.Boolean(compute="_compute_scrap_state_read")
    @api.onchange('product_id')
    def _compute_scrap_state_read(self):
        for this in self:
            if this.product_id and this.product_id.categ_id.is_scrap:
                this.scrap_state_read = True
            elif this.product_id and not this.product_id.categ_id.is_scrap:
                this.scrap_state_read = False
    def _compute_total_with_make(self):
        for this in self:
            if this.product_id.is_making_charges or this.product_id.is_diamond_making_charges:
                this.total_with_make = 0.0
            else:
                this.total_with_make = this.price_subtotal +this.make_value + this.d_make_value

    @api.onchange('purity_hall','product_qty')
    def onchange_purity_hall(self):
        for rec in self:
            if rec.purity_hall > 1000 or rec.purity_hall < 0.00 :
                raise ValidationError(_('purity hallmark between 1 - 1000'))
            if rec.purity_hall:
                rec.purity_diff = ( rec.product_qty * (rec.purity_hall - rec.purity_id.purity)) / 100

    # def write(self, vals):
    #     res = super(PurchaseOrderLine, self).write(vals)
    #     if vals.get('make_rate'):
    #         if vals.get('make_rate') > 0.00 and len(self.order_id.order_line) == 1 :
    #             product_object = self.env['product.product'].browse([self.product_id.id])
    #             make_value_product = product_object.making_charge_id
    #             uom = self.env.ref('uom.product_uom_unit')
    #             make = self.env['purchase.order.line'].create({
    #                                     'product_id': make_value_product.id,
    #                                     'name': make_value_product.name,
    #                                     'product_qty': 1,
    #                                     'price_unit': 0.00,
    #                                     'product_uom': uom.id,
    #                                     'order_id':self.order_id.id,
    #                                     'date_planned': datetime.today() ,
    #                                     'is_make_value': True,
    #                                     'price_subtotal': 0.00,
    #                                 })
    #     return res

    @api.onchange('product_qty')
    def update_gross(self):
        if self.product_id and self.product_id.categ_id.is_scrap and self.product_qty:
            self.gross_wt = self.product_qty
        elif  self.product_id and self.product_id.categ_id.is_diamond and self.product_qty:
            self.carat = self.product_qty
    # @api.model
    # def create(self, vals):
    #     res = super(PurchaseOrderLine, self).create(vals)
    #
    #     if vals.get('product_id'):
    #         product_object = self.env['product.product'].browse([vals.get('product_id')])
    #         if product_object.gold and not product_object.scrap:
    #             if not  product_object.making_charge_id.id :
    #                 raise ValidationError(_('Please fill make value product for this product'))
    #
    #             make_value_product = product_object.making_charge_id
    #             uom = self.env.ref('uom.product_uom_unit')
    #             if vals.get('make_rate') > 0.00:
    #                 make = self.env['purchase.order.line'].create({
    #                                     'product_id': make_value_product.id,
    #                                     'name': make_value_product.name,
    #                                     'product_qty': 1,
    #                                     'price_unit': 0.00,
    #                                     'product_uom': uom.id,
    #                                     'order_id': vals.get('order_id'),
    #                                     'date_planned': datetime.today() ,
    #                                     'is_make_value': True,
    #                                     'price_subtotal': 0.00,
    #                                 })
    #     return res


    # @api.onchange('d_make_value')
    # def _compute_total_with_d_make(self):
    #     pass

    @api.depends('product_id', 'product_qty', 'price_unit', 'gross_wt',
                 'purity_id', 'purity_diff', 'make_rate',
                 'order_id', 'order_id.order_type', 'order_id.currency_id')
    def _get_gold_rate(self):
        for rec in self:
            # if rec.product_id.making_charge_id.id:
            #     make_value_product = self.env['product.product'].browse([rec.product_id.making_charge_id.id])
            #     product_make_object = self.env['purchase.order.line'].search([('order_id','=',rec.order_id.id),('product_id','=',make_value_product.id)])
            if rec.product_id.categ_id.is_scrap:
                rec.pure_wt = rec.gross_wt * (rec.purity_id and (
                        rec.purity_id.scrap_purity / 1000.000) or 0)
            else:
                rec.pure_wt = rec.product_qty * rec.gross_wt * (rec.purity_id and (
                        rec.purity_id.purity / 1000.000) or 0)
            rec.total_pure_weight = rec.pure_wt + rec.purity_diff
            # NEED TO ADD PURITY DIFF + rec.purity_diff
            # new_pure_wt = rec.pure_wt + rec.purity_diff
            # rec.stock = (rec.product_id and rec.product_id.available_gold or
            #              0.00) + new_pure_wt
            if rec.order_id.diamond:
                rec.make_value = 0.00
            else:
                if rec.product_id.categ_id.is_scrap:
                    rec.make_value = rec.gross_wt * rec.make_rate
                else:
                    rec.make_value = rec.product_qty * rec.gross_wt * rec.make_rate
            if rec.order_id.gold:
                rec.gold_rate = rec.order_id.gold_rate / 1000.000000000000
                rec.gold_value = rec.gold_rate and (
                        rec.total_pure_weight * rec.gold_rate) or 0
            else:
                if rec.order_id.assembly:
                    rec.gold_rate = rec.order_id.gold_rate / 1000.000000000000
                    rec.gold_value = rec.gold_rate and (
                            rec.total_pure_weight * rec.gold_rate) or 0
                else:
                    rec.gold_rate = 0.00
                    rec.gold_value = 0.00
            if rec.product_id.categ_id.is_scrap:
                rec.total_gross_wt = rec.gross_wt
            else:
                rec.total_gross_wt = rec.gross_wt * rec.product_qty


            # make_value_product = self.env['product.product'].browse([rec.product_id.making_charge_id.id])
            # product_basic_line = self.env['purchase.order.line'].search([('order_id','=',rec.order_id.id),('product_id','=',make_value_product.id)])
            # for line in product_basic_line:
            #     product_make_object.write({'gold_rate' : 0.00 ,'price_subtotal' : rec.make_value ,'price_unit':rec.make_value})



    @api.depends('product_qty', 'price_unit', 'taxes_id', 'gross_wt',
                 'purity_id', 'purity_diff', 'make_rate',
                 'order_id', 'order_id.order_type',
                 'order_id.state', 'order_id.order_type.gold')
    def _compute_amount(self):
        for line in self:
            if line.order_id and (line.order_id.order_type.is_fixed or line.order_id.order_type.gold) and line.product_id.gold:
                taxes = line.taxes_id.compute_all(
                    line.gold_value,
                    line.order_id.currency_id,
                    1,
                    line.product_id,
                    line.order_id.partner_id)
                line.update({
                    'price_tax': sum(
                        t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                    'price_total': taxes['total_included'],
                    'price_subtotal': taxes['total_excluded'],
                })
            elif line.order_id.diamond:
                taxes = line.taxes_id.compute_all(
                    (line.price_unit * line.product_qty) - ((line.price_unit * line.discount / 100) * line.product_qty),
                    line.order_id.currency_id,
                    1,
                    line.product_id,
                    line.order_id.partner_id)
                line.update({
                    'price_tax': sum(
                        t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                    'price_total': taxes['total_included'],
                    'price_subtotal': taxes['total_excluded'],
                })
            else:
                vals = line._prepare_compute_all_values()
                taxes = line.taxes_id.compute_all(
                    vals['price_unit'],
                    vals['currency_id'],
                    vals['product_qty'],
                    vals['product'],
                    vals['partner'],)
                line.update({
                    'price_tax': sum(
                        t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                    'price_total': taxes['total_included'],
                    'price_subtotal': taxes['total_excluded'],
                })

    def _prepare_stock_moves(self, picking):
        res = super(PurchaseOrderLine, self)._prepare_stock_moves(picking)
        if self.product_id and self.product_id.categ_id.is_scrap:
            res and res[0].update({
                'carat': self.carat,
                'gross_weight': self.gross_wt,
                'pure_weight': self.pure_wt,
                'purity': self.purity_id.scrap_purity or 1,
                'gold_rate': self.gold_rate,
                'selling_karat_id':
                    self.product_id.product_template_attribute_value_ids and
                    self.product_id.product_template_attribute_value_ids.mapped(
                        'product_attribute_value_id')[0].id or
                    False
                ,'buying_making_charge':self.make_rate
            })
        else:
            res and res[0].update({
                'carat': self.carat,
                'gross_weight': self.gross_wt * self.product_qty,
                'pure_weight': self.pure_wt,
                'purity': self.purity_id.purity or 1,
                'gold_rate': self.gold_rate,
                'selling_karat_id':
                    self.product_id.product_template_attribute_value_ids and
                    self.product_id.product_template_attribute_value_ids.mapped(
                        'product_attribute_value_id')[0].id or
                    False
                ,'buying_making_charge':self.make_rate
            })
        return res

    # def _prepare_account_move_line(self, move):
    #     res = super(PurchaseOrderLine, self)._prepare_account_move_line(move)
    #     #make_value_product = self.env.ref('gold_purchases.make_value_product')
    #     product_object = self.env['product.product'].browse([res.get('product_id')])
    #
    #     price_un = 0.00
    #     diff_gross = 0.00
    #     if product_object.is_making_charges:
    #         price_un = res.get('price_unit')
    #     if product_object.gold:
    #         if product_object.purchase_method == "receive":
    #             new_pure = 0.0
    #             total_pure_weight = 0.0
    #             diff_gross = 0.0
    #             if self.received_gross_wt < (self.gross_wt * self.product_qty):
    #                 total_pure_weight = 0.0
    #                 if self.product_id.categ_id.is_scrap == False:
    #                     total_pure_weight = self.received_gross_wt * (self.purity_id and (
    #                         self.purity_id.purity / 1000.000) or 1)
    #                 else:
    #                     total_pure_weight = self.received_gross_wt * (self.purity_id and (
    #                         self.purity_id.scrap_purity / 1000.000) or 1)
    #                 try:
    #                     diff_gross =  (self.gross_wt * self.product_qty) / self.received_gross_wt
    #                 except:
    #                     raise UserError(_('You Should Receive Quantities First'))
    #                 new_pure = 0.0
    #                 if self.product_id.categ_id.is_scrap:
    #                     new_pure = total_pure_weight
    #                 else:
    #                     new_pure = total_pure_weight / self.product_qty
    #
    #                 new_purity_diff =  self.purity_diff / self.product_qty
    #                 res.update({
    #                     'carat':self.carat,
    #                     'gross_wt': self.received_gross_wt ,
    #                     'pure_wt': new_pure - new_purity_diff ,
    #                     'purity_id': self.purity_id and self.purity_id.id or False,
    #                     'purity_diff': new_purity_diff,
    #                     'gold_rate': self.gold_rate,
    #                     'make_rate': self.make_rate,
    #                     'make_value': self.make_value / diff_gross ,
    #                     'gold_value': self.gold_rate and (new_pure * self.gold_rate) or 0,
    #                     'price_unit': self.gold_rate and (new_pure * self.gold_rate) or 0,
    #                     'price_subtotal': self.gold_rate and (new_pure * self.gold_rate) or 0,
    #                     'discount': self.discount,
    #                 })
    #             else:
    #                 res.update({
    #                     'carat':self.carat,
    #                     'gross_wt': self.gross_wt,
    #                     'pure_wt': self.pure_wt,
    #                     'purity_id': self.purity_id and self.purity_id.id or False,
    #                     'purity_diff': self.purity_diff,
    #                     'gold_rate': self.gold_rate,
    #                     'make_rate': self.make_rate,
    #                     'make_value': self.make_value,
    #                     'gold_value': self.gold_value,
    #                     'price_unit': self.gold_value,
    #                     'price_subtotal': self.gold_value,
    #                     'discount': self.discount,
    #                 })
    #         else:
    #             # if self.product_qty < (self.gross_wt * self.product_qty):
    #             #     total_pure_weight = self.product_qty * (self.purity_id and (
    #             #         self.purity_id.purity / 1000.000) or 1)
    #             #     try:
    #             #         diff_gross =  (self.gross_wt * self.product_qty) / self.product_qty
    #             #     except:
    #             #         raise UserError(_('You Should Receive Quantities First'))
    #             #     new_pure = total_pure_weight / self.product_qty
    #             #     new_purity_diff =  self.purity_diff / self.product_qty
    #             #     res.update({
    #             #         'gross_wt': self.received_gross_wt ,
    #             #         'pure_wt': new_pure - new_purity_diff ,
    #             #         'purity_id': self.purity_id and self.purity_id.id or False,
    #             #         'purity_diff': new_purity_diff,
    #             #         'gold_rate': self.gold_rate,
    #             #         'make_rate': self.make_rate,
    #             #         'make_value': self.make_value / diff_gross ,
    #             #         'gold_value': self.gold_rate and (new_pure * self.gold_rate) or 0,
    #             #         'price_unit': self.gold_rate and (new_pure * self.gold_rate) or 0 ,
    #             #     })
    #             # else:
    #             res.update({
    #                 'carat':self.carat,
    #                 'gross_wt': self.gross_wt,
    #                 'pure_wt': self.pure_wt,
    #                 'purity_id': self.purity_id and self.purity_id.id or False,
    #                 'purity_diff': self.purity_diff,
    #                 'gold_rate': self.gold_rate,
    #                 'make_rate': self.make_rate,
    #                 'make_value': self.make_value,
    #                 'gold_value': self.gold_value,
    #                 'price_unit': self.gold_value,
    #                 'price_subtotal': self.gold_value,
    #                 'discount': self.discount,
    #             })
    #     product_object = self.env['product.product'].browse([res.get('product_id')])
    #     make_value_product = product_object.making_charge_id
    #     if product_object.is_making_charges:
    #         purchase_order = self.env['purchase.order'].browse([self.order_id.id])
    #         new_gross_wt = 0.00
    #         new_product_qty = 0.00
    #         new_received_gross_wt =0.00
    #         for line in purchase_order.order_line:
    #             if line.product_id == self.product_id:
    #                 if line.product_id.purchase_method == 'receive':
    #                     if line.gross_wt > 0.00 and line.received_gross_wt > 0.00:
    #                         new_gross_wt = line.gross_wt
    #                         new_product_qty = line.product_qty
    #                         new_received_gross_wt = line.received_gross_wt
    #                 else:
    #                     if line.gross_wt > 0.00 and line.product_qty > 0.00:
    #                         new_gross_wt = line.gross_wt
    #                         new_product_qty = line.product_qty
    #                         new_received_gross_wt = line.received_gross_wt
    #                     # print(new_gross_wt)
    #                     # print(new_product_qty)
    #                     # print(new_received_gross_wt)
    #         if self.product_id.purchase_method == 'receive':
    #             # print(price_un)
    #             # print(new_gross_wt)
    #             # print(new_product_qty)
    #             # print(new_received_gross_wt)
    #             if new_received_gross_wt <=0:
    #                 raise ValidationError(_('You Should Receive Products First'))
    #             else:
    #                 diff_gross =  (new_gross_wt * new_product_qty) / new_received_gross_wt
    #             if diff_gross > 0.00:
    #                 res.update({'price_unit': price_un / diff_gross , 'quantity': 1.00,'gold_rate':0.00})
    #             else:
    #                 res.update({'price_unit': price_un, 'quantity': 1.00,'gold_rate':0.00})
    #         else:
    #             # if new_product_qty <=0:
    #             #     raise ValidationError(_('You Should Receive Products First'))
    #             # else:
    #             diff_gross =  (new_gross_wt * new_product_qty)
    #             if diff_gross > 0.00:
    #                 res.update({'price_unit': price_un / diff_gross , 'quantity': 1.00,'gold_rate':0.00})
    #             else:
    #                 res.update({'price_unit': price_un, 'quantity': 1.00,'gold_rate':0.00})
    #
    #
    #     print("res")
    #     print(res)
    #     print("res")
    #     return res

    def _prepare_account_move_line(self, move):
        res = super(PurchaseOrderLine, self)._prepare_account_move_line(move)
        if self.product_id.is_making_charges or self.product_id.is_diamond_making_charges:
            res.update({
            'quantity':self.product_qty,
            'price_unit':self.price_unit,
            })
        else:
            if self.product_id.purchase_method == 'receive':
                if self.product_id.categ_id.is_scrap:
                    res.update({
                    'quantity':self.qty_received,
                    'carat':self.carat,
                    'gross_wt': self.qty_received,
                    'total_gross_weight': self.qty_received,
                    'pure_wt': (self.qty_received ) * (self.purity_id.scrap_purity/ 1000.000000000000),
                    'purity_id': self.purity_id and self.purity_id.id or False,
                    'purity_diff': self.purity_diff,
                    'gold_rate': self.gold_rate,
                    'make_rate': self.make_rate,
                    'make_value': self.make_value,
                    'd_make_value': self.d_make_value,
                    'gold_value': (self.gold_rate * self.qty_received  * (self.purity_id.scrap_purity/ 1000.000000000000)),
                    'price_unit': (self.gold_rate * (self.purity_id.scrap_purity/ 1000.000000000000)),
                    'price_subtotal': (self.gold_rate * self.qty_received  * (self.purity_id.scrap_purity/ 1000.000000000000)),
                    'discount': self.discount,
                    })
                elif self.product_id.categ_id.is_gold:
                    res.update({
                    'quantity':self.qty_received,
                    'carat':self.carat,
                    'gross_wt': self.gross_wt,
                    'total_gross_weight':self.qty_received * self.gross_wt,
                    'pure_wt': (self.qty_received * self.gross_wt) * (self.purity_id.purity/ 1000.000000000000),
                    'purity_id': self.purity_id and self.purity_id.id or False,
                    'purity_diff': self.purity_diff,
                    'gold_rate': self.gold_rate,
                    'make_rate': self.make_rate,
                    'make_value': self.make_value,
                    'd_make_value': self.d_make_value,
                    'gold_value': (self.gold_rate * (self.qty_received * self.gross_wt) * (self.purity_id.purity/ 1000.000000000000)),
                    'price_unit': (self.gold_rate * (self.qty_received * self.gross_wt) * (self.purity_id.purity/ 1000.000000000000)) / self.qty_received,
                    'price_subtotal': (self.gold_rate * (self.qty_received * self.gross_wt) * (self.purity_id.purity/ 1000.000000000000)),
                    'discount': self.discount,
                    })
                elif self.product_id.categ_id.is_diamond:
                    res.update({
                    'quantity':self.product_qty,
                    'carat':self.carat,
                    'gross_wt': self.gross_wt,
                    'total_gross_weight': self.total_gross_wt,
                    'pure_wt': self.pure_wt,
                    'purity_id': self.purity_id and self.purity_id.id or False,
                    'purity_diff': self.purity_diff,
                    'gold_rate': self.gold_rate,
                    'make_rate': self.make_rate,
                    'make_value': self.make_value,
                    'd_make_value': self.d_make_value,
                    'gold_value': self.gold_value,
                    'price_unit': self.price_unit,
                    'price_subtotal': self.price_unit * self.product_qty,
                    'discount': self.discount,
                    })
            else:
                if self.product_id.categ_id.is_scrap:
                    res.update({
                    'quantity':self.quantity,
                    'carat':self.carat,
                    'gross_wt': self.quantity,
                    'total_gross_weight': self.quantity,
                    'pure_wt': (self.quantity ) * (self.purity_id.scrap_purity/ 1000.000000000000),
                    'purity_id': self.purity_id and self.purity_id.id or False,
                    'purity_diff': self.purity_diff,
                    'gold_rate': self.gold_rate,
                    'make_rate': self.make_rate,
                    'make_value': self.make_value,
                    'd_make_value': self.d_make_value,
                    'gold_value': (self.gold_rate * self.quantity  * (self.purity_id.scrap_purity/ 1000.000000000000)),
                    'price_unit': (self.gold_rate * (self.purity_id.scrap_purity/ 1000.000000000000)),
                    'price_subtotal': (self.gold_rate * self.quantity  * (self.purity_id.scrap_purity/ 1000.000000000000)),
                    'discount': self.discount,
                    })
                elif self.product_id.categ_id.is_gold:
                    res.update({
                    'quantity':self.quantity,
                    'carat':self.carat,
                    'gross_wt': self.gross_wt,
                    'total_gross_weight':self.quantity * self.gross_wt,
                    'pure_wt': (self.quantity * self.gross_wt) * (self.purity_id.purity/ 1000.000000000000),
                    'purity_id': self.purity_id and self.purity_id.id or False,
                    'purity_diff': self.purity_diff,
                    'gold_rate': self.gold_rate,
                    'make_rate': self.make_rate,
                    'make_value': self.make_value,
                    'd_make_value': self.d_make_value,
                    'gold_value': (self.gold_rate * (self.quantity * self.gross_wt) * (self.purity_id.purity/ 1000.000000000000)),
                    'price_unit': (self.gold_rate * (self.quantity * self.gross_wt) * (self.purity_id.purity/ 1000.000000000000)) / self.quantity,
                    'price_subtotal': (self.gold_rate * (self.quantity * self.gross_wt) * (self.purity_id.purity/ 1000.000000000000)),
                    'discount': self.discount,
                    })
                elif self.product_id.categ_id.is_diamond:
                    res.update({
                    'quantity':self.product_qty,
                    'carat':self.carat,
                    'gross_wt': self.gross_wt,
                    'total_gross_weight': self.total_gross_wt,
                    'pure_wt': self.pure_wt,
                    'purity_id': self.purity_id and self.purity_id.id or False,
                    'purity_diff': self.purity_diff,
                    'gold_rate': self.gold_rate,
                    'make_rate': self.make_rate,
                    'make_value': self.make_value,
                    'd_make_value': self.d_make_value,
                    'gold_value': self.gold_value,
                    'price_unit': self.price_unit,
                    'price_subtotal': self.price_unit * self.product_qty,
                    'discount': self.discount,
                    })
        return res

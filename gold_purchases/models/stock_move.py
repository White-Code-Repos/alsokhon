 # -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools import float_compare, float_round, float_is_zero



class ItemCategory(models.Model):
    _name = 'item.category'
    _description = "Item Category"

    name = fields.Char('Name')
    sub_category_lines = fields.One2many('item.category.line',
                                         'parent_category_id',
                                         string="Sub Category")


class SubCategory(models.Model):
    _name = 'item.category.line'
    _description = "Sub Category"

    name = fields.Char('Name')
    parent_category_id = fields.Many2one('item.category',
                                         string="Parent Category")


class StockMove(models.Model):
    _inherit = 'stock.move'

    gold = fields.Boolean(string="Gold", compute="_compute_gold_state")
    diamond = fields.Boolean(string="Gold", compute="_compute_gold_state")
    assembly = fields.Boolean(string="assembly", compute="_compute_gold_state")
    def _compute_gold_state(self):
        for this in self:
            if this.product_id.categ_id.is_gold:
                this.gold = True
                this.diamond = False
                this.assembly = False
                break
            elif this.product_id.categ_id.is_diamond:
                this.gold = False
                this.assembly = False
                this.diamond = True
                break
            else:
                this.gold = False
                this.assembly = True
                this.diamond = False
    gross_weight = fields.Float(string='Gross Weight', digits=(16, 3))
    pure_weight = fields.Float('Pure Weight', digits=(16, 3))
    purity = fields.Float(string="Purity", digits=(16, 3))
    gold_rate = fields.Float(string='Gold Rate', digits=(16, 3))
    item_category_id = fields.Many2one('item.category', string="Item Category")
    sub_category_id = fields.Many2one('item.category.line',
                                      string="Sub Category")
    selling_karat_id = fields.Many2one('product.attribute.value',
                                       string="Selling Karat")
    selling_making_charge = fields.Monetary('Selling Making Charge',
                                            currency_field='company_currency_id',
                                            digits=(16, 3))
    buying_making_charge = fields.Monetary('Buying Making Charge',
                                            currency_field='company_currency_id',
                                            digits=(16, 3))
    company_currency_id = fields.Many2one('res.currency',
                                          string="Company Currency",
                                          related='company_id.currency_id')
    lot_id = fields.Many2one('stock.production.lot', string='Lot / Serial Number')


    def _create_in_svl(self, forced_quantity=None):
        """Create a `stock.valuation.layer` from `self`.

        :param forced_quantity: under some circunstances, the quantity to value is different than
            the initial demand of the move (Default value = None)
        """
        svl_vals_list = []
        for move in self:
            move = move.with_context(force_company=move.company_id.id)
            valued_move_lines = move._get_in_move_lines()
            valued_quantity = 0
            for valued_move_line in valued_move_lines:
                valued_quantity += valued_move_line.product_uom_id._compute_quantity(
                    valued_move_line.qty_done, move.product_id.uom_id)
            unit_cost = abs(
                move._get_price_unit())  # May be negative (i.e. decrease an out move).
            if move.product_id.cost_method == 'standard':
                unit_cost = move.product_id.standard_price
            # Check Gold Product and pass gold rate, pure weight instead of
            # cost, qty
            if move.product_id.categ_id.is_assembly:
                purchase_order = self.env['purchase.order']
                if 'P0' in move.origin:
                    # print(move.origin)
                    purchase_order = self.env['purchase.order'].search([('name','=',move.origin)])
                    if len(purchase_order) > 0:
                        # print(purchase_order)
                        pol = self.env['purchase.order.line'].search([('order_id','=',purchase_order.id),('product_id','=',move.product_id.id)])
                        # print(pol)
                        # print(pol.price_unit)
                        # print(pol.make_value)
                        # print(pol.d_make_value)
                        # print(pol.gold_value)
                        # print(pol.product_id.standard_price)
                        # print(purchase_order.assembly_type)
                        if purchase_order.assembly_no_giving:
                            # print("J")
                            # print(pol.price_unit + pol.d_make_value + pol.make_value)
                            # print("J")
                            svl_vals = move.product_id._prepare_in_svl_vals(
                                pol.product_qty, pol.price_unit + pol.d_make_value)
                        elif purchase_order.assembly_give_both:
                            diamond_price = 0.0
                            for line in purchase_order.assembly_description_diamond:
                                diamond_price += line.stones_value
                            svl_vals = move.product_id._prepare_in_svl_vals(
                                pol.product_qty, pol.price_unit + pol.d_make_value  + pol.gold_value + diamond_price)
                        elif purchase_order.assembly_give_gold:
                            # print("GG")
                            # print(pol.price_unit + pol.d_make_value + pol.make_value + pol.gold_value)
                            # print("GG")
                            svl_vals = move.product_id._prepare_in_svl_vals(
                                pol.product_qty, pol.price_unit + pol.d_make_value  + pol.gold_value)
                        elif purchase_order.assembly_give_diamond:
                            # print("GD")
                            # print(pol.price_unit)
                            # print(pol.d_make_value)
                            # print(pol.make_value)
                            # print(pol.product_id.standard_price)
                            # print("GD")
                            diamond_price = 0.0
                            for line in purchase_order.assembly_description_diamond:
                                diamond_price += line.stones_value
                            svl_vals = move.product_id._prepare_in_svl_vals(
                                pol.product_qty, pol.price_unit + pol.d_make_value  + diamond_price)
            elif move.product_id.gold:
                if move.origin:
                    if 'P0' in move.origin:
                        svl_vals = move.product_id._prepare_in_svl_vals(
                            move.pure_weight, move.gold_rate)
                    elif 'Assembly Gold Transfer' in move.origin:
                        purchase_order = move.picking_id.assembly_purchase_id
                        assembly_return = purchase_order.assembly_back_gold_ids.filtered(lambda x: x.product_id and
                                                                       x.product_id == move.product_id)
                        svl_vals = move.product_id._prepare_in_svl_vals(
                            assembly_return.pure_weight , assembly_return.gold_rate)
                    elif 'Assembly Scrap Transfer' in move.origin:
                        purchase_order = move.picking_id.assembly_purchase_id
                        assembly_return = purchase_order.assembly_back_gold_ids.filtered(lambda x: x.product_id and
                                                                       x.product_id == move.product_id)
                        svl_vals = move.product_id._prepare_in_svl_vals(
                            assembly_return.pure_weight , assembly_return.gold_rate)
                else:
                    svl_vals = move.product_id._prepare_in_svl_vals(
                        move.pure_weight, move.gold_rate)
            elif move.product_id.diamond:
                purchase_order = self.env['purchase.order']
                if 'P0' in move.origin:
                    purchase_order = self.env['purchase.order'].search([('name','=',move.origin)])
                    if len(purchase_order) > 0:
                        pol = self.env['purchase.order.line'].search([('order_id','=',purchase_order.id),('product_id','=',move.product_id.id)])
                        svl_vals = move.product_id._prepare_in_svl_vals(
                            pol.carat, (pol.price_unit + pol.d_make_value / pol.carat))
                elif 'Assembly Stone Transfer' in move.origin:
                    purchase_order = move.picking_id.assembly_purchase_id
                    assembly_return = purchase_order.assembly_back_diamond_ids.filtered(lambda x: x.product_id and
                                                                   x.product_id == move.product_id)
                    svl_vals = move.product_id._prepare_in_svl_vals(
                        assembly_return.carat , assembly_return.carat_cost)
            else:
                svl_vals = move.product_id._prepare_in_svl_vals(
                    forced_quantity or valued_quantity, unit_cost)
            svl_vals.update(move._prepare_common_svl_vals())
            # print(svl_vals)
            if forced_quantity:
                svl_vals[
                    'description'] = 'Correction of %s (modification of past move)' % move.picking_id.name or move.name
            svl_vals_list.append(svl_vals)

        stock_val_layer = self.env['stock.valuation.layer'].sudo().create(svl_vals_list)
        for layer in stock_val_layer:
            if not layer.stock_move_id.picking_id.backorder_id:
                layer.write({'value': layer.value +  layer.stock_move_id.purchase_line_id.make_value })
            layer.stock_move_id.purchase_line_id.received_gross_wt = layer.stock_move_id.purchase_line_id.received_gross_wt + layer.stock_move_id.gross_weight
        return stock_val_layer
#NEW
    # def _create_out_svl(self, forced_quantity=None):
    #     """Create a `stock.valuation.layer` from `self`.
    #
    #     :param forced_quantity: under some circunstances, the quantity to value is different than
    #         the initial demand of the move (Default value = None)
    #     """
    #     svl_vals_list = []
    #     for move in self:
    #         move = move.with_context(force_company=move.company_id.id)
    #         valued_move_lines = move._get_out_move_lines()
    #         valued_quantity = 0
    #         for valued_move_line in valued_move_lines:
    #             valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done, move.product_id.uom_id)
    #         if float_is_zero(forced_quantity or valued_quantity, precision_rounding=move.product_id.uom_id.rounding):
    #             continue
    #         svl_vals = move.product_id._prepare_out_svl_vals(forced_quantity or valued_quantity, move.company_id)
    #         svl_vals.update(move._prepare_common_svl_vals())
    #         if forced_quantity:
    #             svl_vals['description'] = 'Correction of %s (modification of past move)' % move.picking_id.name or move.name
    #         svl_vals_list.append(svl_vals)
    #     return self.env['stock.valuation.layer'].sudo().create(svl_vals_list)
#NEW

#    def _create_out_svl(self, forced_quantity=None):
 #       """Create a `stock.valuation.layer` from `self`.

  #      :param forced_quantity: under some circunstances, the quantity to value is different than
  #          the initial demand of the move (Default value = None)
  #      """
        #svl_vals_list = []
        #for move in self:
         #   move = move.with_context(force_company=move.company_id.id)
          #  valued_move_lines = move._get_out_move_lines()
          #  valued_quantity = 0
          #  for valued_move_line in valued_move_lines:
          #      valued_quantity += valued_move_line.product_uom_id._compute_quantity(valued_move_line.qty_done, move.product_id.uom_id)
         #   if float_is_zero(forced_quantity or valued_quantity, precision_rounding=move.product_id.uom_id.rounding):
         #       continue
             # Check Gold Product and pass gold rate, pure weight instead of
            # cost, qty
         #   if move.product_id.gold:
         #       svl_vals = move.product_id._prepare_out_svl_vals(move.pure_weight, move.company_id)
         #       svl_vals['unit_cost'] = 0.00
         #       svl_vals['quantity'] = 0.00
         #       svl_vals['value'] = 0.00
         #   else:
         #       svl_vals = move.product_id._prepare_out_svl_vals(forced_quantity or valued_quantity, move.company_id)
         #   svl_vals.update(move._prepare_common_svl_vals())
         #   if forced_quantity:
         #       svl_vals['description'] = 'Correction of %s (modification of past move)' % move.picking_id.name or move.name

         #   svl_vals_list.append(svl_vals)
        ##return self.env['stock.valuation.layer'].sudo().create(svl_vals_list)


    def _action_done(self, cancel_backorder=False):
        res = super(StockMove, self)._action_done()
        self.product_id.compute_available_gold()
        return res


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'
    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        """ Override to handle the "inventory mode" and set the `inventory_quantity`
        in view list grouped.
        """
        if 'purity' in fields:
            fields.remove('purity')
        result = super(StockMoveLine, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        return result

    # @api.onchange('lot_id', 'gross_weight')
    # def change_lot(self):
    #     if self.lot_id:
    #         if self.lot_id.product_id and self.lot_id.product_id.categ_id.is_scrap:
    #             # self.lot_id.write({
    #             # 'gross_weight': 0.0,
    #             # 'purity': 0.0,
    #             # 'selling_making_charge': 0.0
    #             # })
    #             self.lot_id.write({
    #             'gross_weight': self.lot_id.gross_weight + self.gross_weight,
    #             'purity': self.purity,
    #             'selling_making_charge':self.selling_making_charge
    #             })
    #         elif self.lot_id.product_id and not self.lot_id.product_id.categ_id.is_scrap:
    #             # self.lot_id.write({
    #             # 'gross_weight': 0.0,
    #             # 'purity': 0.0,
    #             # 'selling_making_charge': 0.0
    #             # })
    #             self.lot_id.write({
    #             'gross_weight': self.gross_weight,
    #             'purity': self.purity,
    #             'selling_making_charge':self.selling_making_charge
    #             })
    image = fields.Binary()
    # related='actual_gross_weight',

    gross_weight = fields.Float(string='Gross Weight', store=True)
                                # related='move_id.gross_weight',

    actual_gross_weight = fields.Float(string='Gross Weight', store=True)
    purity_id = fields.Many2one('gold.purity', string="Purity Karat", compute="_compute_purity_id")
    def _compute_purity_id(self):
        for this in self:
            this.purity_id = False
            if this.product_id and this.product_id.categ_id.is_scrap:
                purity_id = self.env['gold.purity'].search([('scrap_purity','=',this.purity)])
                if purity_id:
                    this.purity_id = purity_id.id
            elif this.product_id and not this.product_id.categ_id.is_scrap:
                purity_id = self.env['gold.purity'].search([('purity','=',this.purity)])
                if purity_id:
                    this.purity_id = purity_id.id
    purity = fields.Float(related="move_id.purity", string="Purity", store=True)
    pure_weight = fields.Float(compute='get_pure_weight', string="Pure Weight",
                               store=True, digits=(16, 3))
    item_category_id = fields.Many2one('item.category', string="Item Category")
    sub_category_id = fields.Many2one('item.category.line',
                                      string="Sub Category")
    selling_karat_id = fields.Many2one('product.attribute.value',
                                       string="Selling Karat",
                                       compute='get_karat')
    selling_making_charge = fields.Monetary('Selling Making Charge',
                                            digits=(16, 3))
    buying_making_charge = fields.Monetary('Buying Making Charge',
                                            digits=(16, 3))
    currency_id = fields.Many2one('res.currency', string="Company Currency",
                                  related='company_id.currency_id')



    @api.depends('move_id')
    def get_karat(self):
        for rec in self:
            rec.selling_karat_id = rec.move_id and \
                                   rec.move_id.selling_karat_id and \
                                   rec.move_id.selling_karat_id.id or False

    # @api.constrains('gross_weight')
    # def validate_gross_weight(self):
    #     for record in self:
    #         if record.gross_weight > record.actual_gross_weight:
    #             raise ValidationError(_(" The total Gross Weight for %s Can Not exceed the Gross Wt on the Purchase Order line.")%record.lot_name)

    @api.depends('gross_weight', 'purity')
    def get_pure_weight(self):
        for rec in self:
            rec.pure_weight = rec.gross_weight * (rec.purity / 1000.000)


    def write(self, vals):
        res = super(StockMoveLine, self).write(vals)
        print("WRITEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEEE")
        # if vals.get('lot_id', False):
        #     for move_line in self:
        #         if move_line.product_id and move_line.product_id.gold:
        #             lot_rec = self.env['stock.production.lot'].search(
        #                 [('id', '=', vals.get('lot_id'))])
        #             lot_rec.gross_weight = move_line.gross_weight
        #             lot_rec.purity = move_line.purity
        #             lot_rec.pure_weight = move_line.pure_weight
        #             lot_rec.item_category_id = move_line.item_category_id.id if \
        #                 move_line.item_category_id else False
        #             lot_rec.sub_category_id = move_line.sub_category_id.id if \
        #                 move_line.sub_category_id else False
        #             lot_rec.selling_making_charge = \
        #                 move_line.selling_making_charge if \
        #                     move_line.selling_making_charge else False
        #             lot_rec.selling_karat_id = move_line.selling_karat_id.id if \
        #                 move_line.selling_karat_id else False

        # if vals.get('gross_weight', False):
        #     for move_line_gross in self:
        #         move_line_gross.move_id.write({'gross_weight':  vals.get('gross_weight')})
        #         move_line_gross.move_id.write({'pure_weight':  vals.get('gross_weight') * (self.purity / 1000.000) })

        return res

    @api.model
    def create(self, vals):
        res = super(StockMoveLine, self).create(vals)
        print(res.lot_id.product_id)
        print(res.lot_id.product_id.categ_id.is_scrap)
        if res.lot_id.product_id and res.lot_id.product_id.categ_id.is_scrap and res.move_id._is_in():
            res.lot_id.write({
            'gross_weight': res.lot_id.gross_weight + res.gross_weight,
            'purity': res.purity,
            'selling_making_charge':res.selling_making_charge,
            'buying_making_charge':res.buying_making_charge,
            'pure_weight':res.pure_weight,
            'item_category_id':res.item_category_id.id,
            'sub_category_id':res.sub_category_id.id,
            'selling_karat_id':res.selling_karat_id.id,
            })
        elif res.lot_id.product_id and res.lot_id.product_id.categ_id.is_diamond and res.move_id._is_in():
            res.lot_id.write({
            'carat': res.lot_id.carat + res.carat,
            'gross_weight': res.lot_id.gross_weight + res.gross_weight,
            'purity': res.purity,
            'selling_making_charge':res.selling_making_charge,
            'buying_making_charge':res.buying_making_charge,
            'pure_weight':res.pure_weight,
            'item_category_id':res.item_category_id.id,
            'sub_category_id':res.sub_category_id.id,
            'selling_karat_id':res.selling_karat_id.id,
            })
        elif res.lot_id.product_id and res.lot_id.product_id.categ_id.is_gold and res.move_id._is_in():
            res.lot_id.write({
            'gross_weight': res.gross_weight,
            'purity': res.purity,
            'selling_making_charge':res.selling_making_charge,
            'buying_making_charge':res.buying_making_charge,
            'pure_weight':res.pure_weight,
            'item_category_id':res.item_category_id.id,
            'sub_category_id':res.sub_category_id.id,
            'selling_karat_id':res.selling_karat_id.id,
            })
        elif res.lot_id.product_id and res.lot_id.product_id.categ_id.is_assembly and res.move_id._is_in():
            print("^^^^^^^^^^^^^^^^^^^^^")
            assembly_description_gold = []
            assembly_description_diamond = []
            if res.move_id.origin and 'P0' in res.move_id.origin:
                purchase_obj = self.env['purchase.order'].search([('name','=',res.move_id.origin)])
                if purchase_obj:
                    for line in purchase_obj.assembly_description_gold:
                        assembly_description_gold.append((0,0,{
                        'product_id':line.product_id.id,
                        'quantity':line.quantity,
                        'gross_weight':line.gross_weight,
                        'pure_weight':line.pure_weight,
                        'purity_id':line.purity_id.id,
                        'purity':line.purity,
                        # 'polish_rhodium':line.polish_rhodium
                        }))
                    for line in purchase_obj.assembly_description_diamond:
                        assembly_description_diamond.append((0,0,{
                        'product_id':line.product_id.id,
                        'carat':line.carat,
                        'carat_price':line.carat_price,
                        'stones_value':line.stones_value,
                        'stones_quantity':line.stones_quantity,
                        'stone_setting_rate':line.stone_setting_rate,
                        'stone_setting_value':line.stone_setting_value,
                        }))
            res.lot_id.write({
            'carat': res.carat,
            'gross_weight': res.gross_weight,
            'purity': res.purity,
            'selling_making_charge':res.selling_making_charge,
            'buying_making_charge':res.buying_making_charge,
            'pure_weight':res.pure_weight,
            'item_category_id':res.item_category_id.id,
            'sub_category_id':res.sub_category_id.id,
            'selling_karat_id':res.selling_karat_id.id,
            'assembly_description_gold':assembly_description_gold,
            'assembly_description_diamond':assembly_description_diamond,
            })


        # if vals.get('gross_weight', False):
        #     if vals.get('move_id'):
        #         stock_move = self.env['stock.move'].browse([vals.get('move_id')])
        #         stock_move.write({'gross_weight':  vals.get('gross_weight')})
        #         stock_move.write({'pure_weight':  vals.get('gross_weight') * (stock_move.purity / 1000.000) })

        return res

class StockInventoryLine(models.Model):
    _inherit = 'stock.inventory.line'

    gross_weight = fields.Float('Gross Weight', digits=(16, 3))
    pure_weight = fields.Float('Pure Weight', digits=(16, 3))


class StockValuationLayer(models.Model):
    _inherit = 'stock.valuation.layer'

    pure_weight = fields.Float('Pure Weight', digits=(16, 3))
    gold_rate = fields.Float(string='Gold Rate', digits=(16, 3))
    gross_weight = fields.Float('Gross Weight',related="stock_move_id.gross_weight" ,  store=True,digits=(16, 3))
    purity = fields.Float(related="stock_move_id.purity" , string="purity", store=True,digits=(16, 3))
    is_scrap = fields.Boolean(related="product_id.categ_id.is_scrap" , string="scrap", store=True)
    qty_done = fields.Float(related="stock_move_id.product_qty" , string="product_qty", store=True)
    picking_id = fields.Many2one('stock.picking',related="stock_move_id.picking_id" , string="picking_id", store=True)
    is_full_paid = fields.Boolean(string="full paid")
    paid_pure = fields.Float(string="Paid Pure", digits=(16, 3))
    paid_gross = fields.Float(string="Paid Gross", digits=(16, 3))

    @api.onchange('paid_gross')
    def onchange_paid_gross(self):
        for rec in self:
            rec.write({'paid_pure': rec.paid_gross  *  (rec.stock_move_id.purity / 1000)})


    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        """ Override to handle the "inventory mode" and set the `inventory_quantity`
        in view list grouped.
        """
        if 'purity' in fields:
            fields.remove('purity')
        result = super(StockValuationLayer, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
        return result

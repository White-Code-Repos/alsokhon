# -*- coding: utf-8 -*-
from datetime import date , timedelta , datetime
from collections import namedtuple, OrderedDict, defaultdict
from dateutil.relativedelta import relativedelta
from odoo.tools.misc import split_every
from psycopg2 import OperationalError

from odoo import api, fields, models, registry, SUPERUSER_ID, _
from odoo.osv import expression
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, float_compare, float_is_zero, float_round

from odoo.exceptions import UserError,ValidationError

import logging
_logger = logging.getLogger(__name__)

#
class DetailsAssembly(models.Model):
    """docstring for DetailsAssembly."""
    _name = 'details.assembly'

    product_id = fields.Many2one('product.product')
    quantity = fields.Float()
    sale_id = fields.Many2one('sale.order')
    sol_product = fields.Many2one('product.product')


class assemblyDescriptionSaleGold(models.Model):
    """docstring for assemblyDescriptionSaleGold."""
    _name = 'assembly.description.sale.gold'

    product_id = fields.Many2one('product.product')
    quantity = fields.Float()
    gross_weight = fields.Float()
    pure_weight = fields.Float()
    purity_id = fields.Many2one('gold.purity')
    purity = fields.Float()
    sale_order_gold = fields.Many2one('sale.order')
    sol_product = fields.Many2one('product.product')

class assemblyDescriptionSaleDiamond(models.Model):
    """docstring for assemblyDescriptionSaleDiamond."""
    _name = 'assembly.description.sale.diamond'

    product_id = fields.Many2one('product.product')
    carat = fields.Float()
    stones_quantity = fields.Float()
    sale_order_diamond = fields.Many2one('sale.order')
    sol_product = fields.Many2one('product.product')


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    order_category = fields.Selection([('whole_sale','Whole-sale'),('retail','Retail')],required=True)
    # details_assembly = fields.One2many('details.assembly','sale_id')
    details_assembly_gold = fields.One2many('assembly.description.sale.gold','sale_order_gold')
    details_assembly_diamond = fields.One2many('assembly.description.sale.diamond','sale_order_diamond')





    @api.model
    def create(self, values):
        making_order_line = self.env['sale.order.line'].search([('order_id','=',self.id),('is_make_value','=',True)])
        if making_order_line:
            making_order_line.unlink()
        res = super(SaleOrder, self).create(values)
        list_assemply_gold = []
        list_assemply_diamond = []
        for line in res.order_line:
            if line.lot_id and line.product_id.categ_id.is_assembly:
                list_assemply_gold = []
                list_assemply_diamond = []
                for detgol in line.lot_id.assembly_description_gold:
                    list_assemply_gold.append((0,0,{
                    'product_id':detgol.product_id.id,
                    'quantity':detgol.quantity,
                    'gross_weight':detgol.gross_weight,
                    'purity_id':detgol.purity_id,
                    'purity':detgol.purity,
                    'pure_weight':detgol.pure_weight,
                    'sale_order_gold':line.order_id.id,
                    'sol_product':line.product_id.id,
                    }))
                for detdim in line.lot_id.assembly_description_diamond:
                    list_assemply_gold.append((0,0,{
                    'product_id':detdim.product_id.id,
                    'carat':detdim.carat,
                    'stones_quantity':detdim.stones_quantity,
                    'sale_order_diamond':line.order_id.id,
                    'sol_product':line.product_id.id,
                    }))
        res.write({'details_assembly_gold':list_assemply_gold})
        res.write({'details_assembly_diamond':list_assemply_diamond})
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
        done_gold_product = []
        total_charge_gold = []
        for line in product_charge_gold_list:
            if line in done_gold_product:
                continue
            products_for_this_make = self.env['product.product'].search([('making_charge_id','=',line)])
            order_lines_in_this_order = self.env['sale.order.line'].search([('order_id','=',res.id),('product_id','in',products_for_this_make.ids)])
            for sol in order_lines_in_this_order:
                total_charge_gold.append((sol.make_value,sol.product_id.making_charge_id.id))
            done_gold_product.append(line)

        done_diamond_product = []
        total_charge_diamond = []
        for line in product_charge_diamond_list:
            if line in done_diamond_product:
                continue
            products_for_this_make = self.env['product.product'].search([('making_charge_diamond_id','=',line)])
            order_lines_in_this_order = self.env['sale.order.line'].search([('order_id','=',res.id),('product_id','in',products_for_this_make.ids)])
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
                make = self.env['sale.order.line'].create({
                                        'product_id': make_value_product.id,
                                        'name': make_value_product.name,
                                        'product_uom_qty': 1,
                                        'price_unit': pro[0],
                                        'product_uom': uom.id,
                                        'order_id':res.id,
                                        # 'date_planned': datetime.today() ,
                                        'is_make_value': True,
                                        'price_subtotal': pro[0],
                                    })
        if diamond_charge:
            for pro in apply_diamond_charge:
                make_value_product = self.env['product.product'].browse(pro[1])
                uom = self.env.ref('uom.product_uom_unit')
                make = self.env['sale.order.line'].create({
                                        'product_id': make_value_product.id,
                                        'name': make_value_product.name,
                                        'product_uom_qty': 1,
                                        'price_unit': pro[0],
                                        'product_uom': uom.id,
                                        'order_id':res.id,
                                        # 'date_planned': datetime.today() ,
                                        'is_make_value': True,
                                        'price_subtotal': pro[0],
                                    })
        return res

    def write(self, values):
        for dde in self.details_assembly_gold:
            dde.unlink()
        for dded in self.details_assembly_diamond:
            dded.unlink()
        list_assemply_gold = []
        list_assemply_diamond = []
        for line in self.order_line:
            if line.lot_id and line.product_id.categ_id.is_assembly:
                list_assemply_gold = []
                list_assemply_diamond = []
                for detgol in line.lot_id.assembly_description_gold:
                    list_assemply_gold.append((0,0,{
                    'product_id':detgol.product_id.id,
                    'quantity':detgol.quantity,
                    'gross_weight':detgol.gross_weight,
                    'purity_id':detgol.purity_id,
                    'purity':detgol.purity,
                    'pure_weight':detgol.pure_weight,
                    'sale_order_gold':line.order_id.id,
                    'sol_product':line.product_id.id,
                    }))
                for detdim in line.lot_id.assembly_description_diamond:
                    list_assemply_gold.append((0,0,{
                    'product_id':detdim.product_id.id,
                    'carat':detdim.carat,
                    'stones_quantity':detdim.stones_quantity,
                    'sale_order_diamond':line.order_id.id,
                    'sol_product':line.product_id.id,
                    }))
        values['details_assembly_gold'] = list_assemply_gold
        values['details_assembly_diamond'] = list_assemply_diamond
        res = super(SaleOrder, self).write(values)

        making_order_line = self.env['sale.order.line'].search([('order_id','=',self.id),('is_make_value','=',True)])
        if self.state not in  ['done','sale']:
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
            done_gold_product = []
            total_charge_gold = []
            for line in product_charge_gold_list:
                if line in done_gold_product:
                    continue
                products_for_this_make = self.env['product.product'].search([('making_charge_id','=',line)])
                order_lines_in_this_order = self.env['sale.order.line'].search([('order_id','=',self.id),('product_id','in',products_for_this_make.ids)])
                for sol in order_lines_in_this_order:
                    total_charge_gold.append((sol.make_value,sol.product_id.making_charge_id.id))
                done_gold_product.append(line)

            done_diamond_product = []
            total_charge_diamond = []
            for line in product_charge_diamond_list:
                if line in done_diamond_product:
                    continue
                products_for_this_make = self.env['product.product'].search([('making_charge_diamond_id','=',line)])
                order_lines_in_this_order = self.env['sale.order.line'].search([('order_id','=',self.id),('product_id','in',products_for_this_make.ids)])
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
                    make = self.env['sale.order.line'].create({
                                            'product_id': make_value_product.id,
                                            'name': make_value_product.name,
                                            'product_uom_qty': 1,
                                            'price_unit': pro[0],
                                            'product_uom': uom.id,
                                            'order_id':self.id,
                                            # 'date_planned': datetime.today() ,
                                            'is_make_value': True,
                                            'price_subtotal': pro[0],
                                        })
            if diamond_charge:
                for pro in apply_diamond_charge:
                    make_value_product = self.env['product.product'].browse(pro[1])
                    uom = self.env.ref('uom.product_uom_unit')
                    make = self.env['sale.order.line'].create({
                                            'product_id': make_value_product.id,
                                            'name': make_value_product.name,
                                            'product_uom_qty': 1,
                                            'price_unit': pro[0],
                                            'product_uom': uom.id,
                                            'order_id':self.id,
                                            # 'date_planned': datetime.today() ,
                                            'is_make_value': True,
                                            'price_subtotal': pro[0],
                                        })
            return res

    total_gold_vale_order = fields.Float('Total Value', compute="_compute_total_gold_value_order")
    def _compute_total_gold_value_order(self):
        for this in self:
            total = 0.0
            for line in this.order_line:
                if line.product_id.is_making_charges or line.product_id.is_diamond_making_charges:
                    total = total
                else:
                    total = total+line.price_subtotal
            this.total_gold_vale_order = total
    total_make_vale_order = fields.Float('Total Labor/Make Value', compute="_compute_total_make_value_order")
    def _compute_total_make_value_order(self):
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
    inv_move_id = fields.Many2one('account.move', string='Invoice Entry - Gold')

    def action_view_invoice(self):
        invoices = self.mapped('invoice_ids')
        action = self.env.ref('account.action_move_out_invoice_type').read()[0]
        if len(invoices) > 1:
            action['domain'] = [('id', 'in', invoices.ids)]
        elif len(invoices) == 1:
            form_view = [(self.env.ref('account.view_move_form').id, 'form')]
            if 'views' in action:
                action['views'] = form_view + [(state,view) for state,view in action['views'] if view != 'form']
            else:
                action['views'] = form_view
            action['res_id'] = invoices.id
        else:
            action = {'type': 'ir.actions.act_window_close'}

        context = {
            'default_type': 'out_invoice',
        }
        if len(self) == 1:
            context.update({
                'default_partner_id': self.partner_id.id,
                'default_partner_shipping_id': self.partner_shipping_id.id,
                'default_invoice_payment_term_id': self.payment_term_id.id or self.partner_id.property_payment_term_id.id or self.env['account.move'].default_get(['invoice_payment_term_id']).get('invoice_payment_term_id'),
                'default_invoice_origin': self.mapped('name'),
                'default_user_id': self.user_id.id,
            })
        if self.order_type.is_fixed:
            context.update({
                'default_sale_type': "fixed",
            })
        elif  self.order_type.gold:
            context.update({
                'default_sale_type': "unfixed",
            })
        else:
            pass
        action['context'] = context
        print("-----------------------------------------")
        print(action['context'])
        print("-----------------------------------------")
        return action

    @api.depends('order_type')
    def check_gold_fixed(self):
        for rec in self:
            rec.is_gold_fixed = rec.order_type and \
                                rec.order_type.is_fixed or rec.order_type.is_unfixed and \
                                rec.order_type.gold and True or False

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'





    def _prepare_procurement_values(self, group_id=False):
        values = super(SaleOrderLine, self)._prepare_procurement_values(group_id)
        print("================================================================")
        values.update({'lot_id':self.lot_id})
        return values
    lot_id = fields.Many2one('stock.production.lot', string='Lot / Serial Number', required=True)

    @api.onchange('lot_id')
    def _get_making(self):
        if self.lot_id and self.product_id:
            if self.product_id.categ_id.is_scrap or self.product_id.categ_id.is_diamond :
                self.product_uom_qty = self.lot_id.product_qty
            self.purity_id = self.lot_id.purity_id.id
            self.carat = self.lot_id.carat
            self.make_rate = self.lot_id.selling_making_charge
            self.price_unit = 0
            # print(self.lot_id.gross_weight)
            # print(self.lot_id.pure_weight)
            self.gross_wt = self.lot_id.gross_weight
            self.pure_wt = self.lot_id.pure_weight
            if self.lot_id.purity_id.purity != self.lot_id.purity:
                self.purity_hall = self.lot_id.purity
                self.onchange_purity_hall()
            # self.purity = self.lot_id.purity
            # stock_move_line = self.env['stock.move.line'].search([('lot_id','=',self.lot_id.id),('product_id','=',self.product_id.id)])
            # if stock_move_line and len(stock_move_line) == 1:
            #     if stock_move_line.picking_id:
            #         if stock_move_line.picking_id.group_id:
            #             if stock_move_line.picking_id.group_id.name:
            #                 if 'P0' in stock_move_line.picking_id.group_id.name:
            #                     purchase_order = self.env['purchase.order'].search([('name','=',stock_move_line.picking_id.group_id.name)])
            #                     if purchase_order and len(purchase_order) == 1:
            #                         for line in purchase_order.order_line:
            #                             if line.product_id == self.product_id:
            #                                 self.purity_id = line.purity_id.id
                                            # self.make_rate = line.make_rate
                                            # self.make_value = line.make_value
    def _get_gold_stock(self):
        for this in self:
            if this.product_id:
                quants = self.env['stock.quant'].search([('product_id','=',this.product_id.id),('location_id','=',8)])
                total = 0.0
                for quant in quants:
                    # print(quant.lot_id.name)
                    # print(quant.inventory_quantity)
                    total = total + quant.inventory_quantity
                this.stock = total


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
    stock = fields.Float('Stock', compute='_get_gold_stock', digits=(16, 3))
    make_rate = fields.Monetary('Make Rate/G', digits=(16, 3))
    make_value = fields.Monetary('Make Value', compute='_get_gold_rate',
                                 digits=(16, 3), default=0.00)
    gold_rate = fields.Float('Gold Rate/G', compute='_get_gold_rate',
                             digits=(16, 3))
    gold_value = fields.Monetary('Gold Value', compute='_get_gold_rate',
                                 digits=(16, 3))
    is_make_value = fields.Boolean(string='is_make_value')
    total_with_make = fields.Float('Total Value + Make Value', compute="_compute_total_with_make")

    def _compute_total_with_make(self):
        for this in self:
            if this.product_id.is_making_charges or this.product_id.is_diamond_making_charges:
                this.total_with_make = 0.0
            else:
                this.total_with_make = this.price_subtotal +this.make_value + this.d_make_value
    @api.onchange('purity_hall','product_uom_qty')
    def onchange_purity_hall(self):
        for rec in self:
            if rec.purity_hall > 1000 or rec.purity_hall < 0.00 :
                raise ValidationError(_('purity hallmark between 1 - 1000'))
            if rec.purity_hall:
                rec.purity_diff = ( rec.product_uom_qty * (rec.purity_hall - rec.purity_id.purity)) / 100

    scrap_state_read = fields.Boolean(compute="_compute_scrap_state_read")
    @api.onchange('product_id')
    def _compute_scrap_state_read(self):
        for this in self:
            if this.product_id and this.product_id.categ_id.is_scrap:
                this.scrap_state_read = True
            elif this.product_id and not this.product_id.categ_id.is_scrap:
                this.scrap_state_read = False
            else:
                this.scrap_state_read = False

    # def write(self, vals):
    #     res = super(SaleOrderLine, self).write(vals)
    #     if vals.get('make_rate'):
    #         if vals.get('make_rate') > 0.00 and len(self.order_id.order_line) == 1 :
    #             product_object = self.env['product.product'].browse([self.product_id.id])
    #             make_value_product = product_object.making_charge_id
    #             uom = self.env.ref('uom.product_uom_unit')
    #             make = self.env['sale.order.line'].create({
    #                                     'product_id': make_value_product.id,
    #                                     'name': make_value_product.name,
    #                                     'product_uom_qty': 1,
    #                                     'price_unit': 0.00,
    #                                     'product_uom': uom.id,
    #                                     'order_id':self.order_id.id,
    #                                     # 'date_planned': datetime.today() ,
    #                                     'is_make_value': True,
    #                                     'price_subtotal': 0.00,
    #                                 })
    #     return res
    #
    # @api.model
    # def create(self, vals):
    #     res = super(SaleOrderLine, self).create(vals)
    #
    #     if vals.get('product_id'):
    #         product_object = self.env['product.product'].browse([vals.get('product_id')])
    #         if product_object.gold:
    #             if not  product_object.making_charge_id.id :
    #                 raise ValidationError(_('Please fill make value product for this product'))
    #
    #             make_value_product = product_object.making_charge_id
    #             uom = self.env.ref('uom.product_uom_unit')
    #             if vals.get('make_rate') > 0.00:
    #                 make = self.env['sale.order.line'].create({
    #                                     'product_id': make_value_product.id,
    #                                     'name': make_value_product.name,
    #                                     'product_uom_qty': 1,
    #                                     'price_unit': 0.00,
    #                                     'product_uom': uom.id,
    #                                     'order_id': vals.get('order_id'),
    #                                     # 'date_order': datetime.today() ,
    #                                     'is_make_value': True,
    #                                     'price_subtotal': 0.00,
    #                                 })
    #     return res

    @api.onchange('product_uom_qty')
    def update_gross(self):
        if self.product_id and self.product_id.categ_id.is_scrap and self.product_uom_qty:
            self.gross_wt = self.product_uom_qty
        elif  self.product_id and self.product_id.categ_id.is_diamond and self.product_uom_qty:
            self.carat = self.product_uom_qty


    @api.depends('product_id', 'product_uom_qty', 'price_unit', 'gross_wt',
                 'purity_id', 'purity_diff', 'make_rate',
                 'order_id', 'order_id.order_type', 'order_id.currency_id')
    def _get_gold_rate(self):
        for rec in self:
            # if rec.product_id.making_charge_id.id:
            #     make_value_product = self.env['product.product'].browse([rec.product_id.making_charge_id.id])
            #     product_make_object = self.env['sale.order.line'].search([('order_id','=',rec.order_id.id),('product_id','=',make_value_product.id)])
            if rec.product_id.categ_id.is_scrap:
                if rec.purity_diff != 0:
                    rec.pure_wt = rec.gross_wt * rec.purity_hall / 1000.000
                else:
                    rec.pure_wt = rec.gross_wt * (rec.purity_id and (
                            rec.purity_id.scrap_purity / 1000.000) or 0)

            else:
                if rec.purity_diff != 0:
                    rec.pure_wt = rec.product_qty * rec.gross_wt * rec.purity_hall / 1000.000
                    # (rec.purity_id and (
                    #         rec.purity_id.purity / 1000.000) or 0)
                else:
                    rec.pure_wt = rec.product_qty * rec.gross_wt * (rec.purity_id and (
                            rec.purity_id.purity / 1000.000) or 0)
            rec.total_pure_weight = rec.pure_wt
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
                    rec.make_value = rec.product_uom_qty * rec.gross_wt * rec.make_rate
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
                rec.total_gross_wt = rec.gross_wt * rec.product_uom_qty


            # make_value_product = self.env['product.product'].browse([rec.product_id.making_charge_id.id])
            # product_basic_line = self.env['sale.order.line'].search([('order_id','=',rec.order_id.id),('product_id','=',make_value_product.id)])
            # for line in product_basic_line:
            #     product_make_object.write({'gold_rate' : 0.00 ,'price_subtotal' : rec.make_value ,'price_unit':rec.make_value})

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id', 'gross_wt',
                 'purity_id', 'purity_diff', 'make_rate',
                 'order_id', 'order_id.order_type',
                 'order_id.state', 'order_id.order_type.gold')
    def _compute_amount(self):
        """
        Compute the amounts of the SO line.
        """
        for line in self:
            if line.order_id and (line.order_id.order_type.is_fixed or line.order_id.order_type.gold) and line.product_id.gold:
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                # taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
                taxes = line.tax_id.compute_all(line.gold_value, line.order_id.currency_id, 1, product=line.product_id, partner=line.order_id.partner_id)
                line.update({
                    'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                    'price_total': taxes['total_included'],
                    'price_subtotal': taxes['total_excluded'],
                })
                if self.env.context.get('import_file', False) and not self.env.user.user_has_groups('account.group_account_manager'):
                    line.tax_id.invalidate_cache(['invoice_repartition_line_ids'], [line.tax_id.id])
            elif line.order_id.diamond:
                # price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                price = ((line.price_unit * line.product_uom_qty) - ((line.price_unit * line.discount / 100) * line.product_uom_qty))
                print(price)
                taxes = line.tax_id.compute_all(price, line.order_id.currency_id, 1, product=line.product_id, partner=line.order_id.partner_shipping_id)
                print(taxes)
                line.update({
                    'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                    'price_total': taxes['total_included'],
                    'price_subtotal': taxes['total_excluded'],
                })
                if self.env.context.get('import_file', False) and not self.env.user.user_has_groups('account.group_account_manager'):
                    line.tax_id.invalidate_cache(['invoice_repartition_line_ids'], [line.tax_id.id])
            else:
                price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
                line.update({
                    'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                    'price_total': taxes['total_included'],
                    'price_subtotal': taxes['total_excluded'],
                })
                if self.env.context.get('import_file', False) and not self.env.user.user_has_groups('account.group_account_manager'):
                    line.tax_id.invalidate_cache(['invoice_repartition_line_ids'], [line.tax_id.id])

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
    #             if self.received_gross_wt < (self.gross_wt * self.product_uom_qty):
    #                 total_pure_weight = self.received_gross_wt * (self.purity_id and (
    #                     self.purity_id.purity / 1000.000) or 1)
    #                 diff_gross =  (self.gross_wt * self.product_uom_qty) / self.received_gross_wt
    #                 new_pure = self.total_pure_weight / self.product_uom_qty
    #                 new_purity_diff =  self.purity_diff / self.product_uom_qty
    #                 res.update({
    #                     'gross_wt': self.received_gross_wt ,
    #                     'pure_wt': new_pure - new_purity_diff ,
    #                     'purity_id': self.purity_id and self.purity_id.id or False,
    #                     'purity_diff': new_purity_diff,
    #                     'gold_rate': self.gold_rate,
    #                     'make_rate': self.make_rate,
    #                     'make_value': self.make_value / diff_gross ,
    #                     'gold_value': self.gold_rate and (new_pure * self.gold_rate) or 0,
    #                     'price_unit': self.gold_rate and (new_pure * self.gold_rate) or 0 ,
    #                 })
    #             else:
    #                 res.update({
    #                     'gross_wt': self.gross_wt,
    #                     'pure_wt': self.pure_wt,
    #                     'purity_id': self.purity_id and self.purity_id.id or False,
    #                     'purity_diff': self.purity_diff,
    #                     'gold_rate': self.gold_rate,
    #                     'make_rate': self.make_rate,
    #                     'make_value': self.make_value,
    #                     'gold_value': self.gold_value,
    #                     'price_unit': self.gold_value / self.product_uom_qty   ,
    #                 })
    #         else:
    #             if self.received_gross_wt < (self.gross_wt * self.product_uom_qty):
    #                 total_pure_weight = self.received_gross_wt * (self.purity_id and (
    #                     self.purity_id.purity / 1000.000) or 1)
    #                 diff_gross =  (self.gross_wt * self.product_uom_qty) / self.received_gross_wt
    #                 new_pure = self.total_pure_weight / self.product_uom_qty
    #                 new_purity_diff =  self.purity_diff / self.product_uom_qty
    #                 res.update({
    #                     'gross_wt': self.received_gross_wt ,
    #                     'pure_wt': new_pure - new_purity_diff ,
    #                     'purity_id': self.purity_id and self.purity_id.id or False,
    #                     'purity_diff': new_purity_diff,
    #                     'gold_rate': self.gold_rate,
    #                     'make_rate': self.make_rate,
    #                     'make_value': self.make_value / diff_gross ,
    #                     'gold_value': self.gold_rate and (new_pure * self.gold_rate) or 0,
    #                     'price_unit': self.gold_rate and (new_pure * self.gold_rate) or 0 ,
    #                 })
    #             else:
    #                 res.update({
    #                     'gross_wt': self.gross_wt,
    #                     'pure_wt': self.pure_wt,
    #                     'purity_id': self.purity_id and self.purity_id.id or False,
    #                     'purity_diff': self.purity_diff,
    #                     'gold_rate': self.gold_rate,
    #                     'make_rate': self.make_rate,
    #                     'make_value': self.make_value,
    #                     'gold_value': self.gold_value,
    #                     'price_unit': self.gold_value / self.product_uom_qty   ,
    #                 })
    #     product_object = self.env['product.product'].browse([res.get('product_id')])
    #     make_value_product = product_object.making_charge_id
    #     if product_object.is_making_charges:
    #         purchase_order = self.env['purchase.order'].browse([self.order_id.id])
    #         new_gross_wt = 0.00
    #         new_product_qty = 0.00
    #         new_received_gross_wt =0.00
    #         for line in purchase_order.order_line:
    #             if line.gross_wt > 0.00 and line.received_gross_wt > 0.00:
    #                 new_gross_wt = line.gross_wt
    #                 new_product_qty = line.product_uom_qty
    #                 new_received_gross_wt = line.received_gross_wt
    #         diff_gross =  (new_gross_wt * new_product_qty) / new_received_gross_wt
    #         if diff_gross > 0.00:
    #             res.update({'price_unit': price_un / diff_gross , 'quantity': 1.00,'gold_rate':0.00})
    #         else:
    #             res.update({'price_unit': price_un, 'quantity': 1.00,'gold_rate':0.00})
    #
    #     return res


    def _prepare_invoice_line(self):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.

        :param qty: float quantity to invoice
        """
        self.ensure_one()
        res = {
            'display_type': self.display_type,
            'sequence': self.sequence,
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'quantity': self.qty_to_invoice,
            'discount': self.discount,
            'price_unit': self.price_unit,
            'tax_ids': [(6, 0, self.tax_id.ids)],
            'analytic_account_id': self.order_id.analytic_account_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
            'sale_line_ids': [(4, self.id)],
            # 'gross_wt':self.gross_wt,
            # 'purity_id':self.purity_id.id,
            # 'pure_wt':self.pure_wt,
            # 'purity_diff':self.purity_diff,
            # 'make_rate':self.make_rate,
            # 'make_value':self.make_value,
            # 'gold_rate':self.gold_rate,
            # 'gold_value':self.gold_value,
            # 'price_subtotal':self.price_subtotal,
        }
        product_object = self.env['product.product'].browse([self.product_id.id])
        price_un = 0.00
        diff_gross = 0.00
        if product_object.is_making_charges:
            price_un = res.get('price_unit')
        if product_object.gold:
            if product_object.invoice_policy == "delivery":
                if self.received_gross_wt < (self.gross_wt * self.product_uom_qty):
                    total_pure_weight = self.received_gross_wt * (self.purity_id and (
                        self.purity_id.purity / 1000.000) or 1)
                    try:
                        diff_gross =  (self.gross_wt * self.product_uom_qty) / self.received_gross_wt
                    except:
                        raise UserError('You Should Deliver Quantities First')
                    new_pure = total_pure_weight / self.product_uom_qty
                    new_purity_diff =  self.purity_diff / self.product_uom_qty
                    res.update({
                        'gross_wt': self.received_gross_wt ,
                        'pure_wt': new_pure - new_purity_diff ,
                        'purity_id': self.purity_id and self.purity_id.id or False,
                        'purity_diff': new_purity_diff,
                        'gold_rate': self.gold_rate,
                        'make_rate': self.make_rate,
                        'make_value': self.make_value / diff_gross ,
                        'gold_value': self.gold_rate and (new_pure * self.gold_rate) or 0,
                        'price_unit': self.gold_rate and (new_pure * self.gold_rate) or 0 ,
                        'discount': self.discount ,
                    })
                else:
                    res.update({
                        'gross_wt': self.gross_wt,
                        'pure_wt': self.pure_wt,
                        'purity_id': self.purity_id and self.purity_id.id or False,
                        'purity_diff': self.purity_diff,
                        'gold_rate': self.gold_rate,
                        'make_rate': self.make_rate,
                        'make_value': self.make_value,
                        'gold_value': self.gold_value,
                        'price_unit': self.gold_value / self.product_uom_qty   ,
                        'discount': self.discount ,
                    })
            else:
                # if self.received_gross_wt < (self.gross_wt * self.product_uom_qty):
                #     total_pure_weight = self.received_gross_wt * (self.purity_id and (
                #         self.purity_id.purity / 1000.000) or 1)
                #     try:
                #         diff_gross =  (self.gross_wt * self.product_uom_qty) / self.product_uom_qty
                #     except:
                #         raise UserError('You Should Deliver Quantities First')
                #     new_pure = self.total_pure_weight / self.product_uom_qty
                #     new_purity_diff =  self.purity_diff / self.product_uom_qty
                #     res.update({
                #         'gross_wt': self.received_gross_wt ,
                #         'pure_wt': new_pure - new_purity_diff ,
                #         'purity_id': self.purity_id and self.purity_id.id or False,
                #         'purity_diff': new_purity_diff,
                #         'gold_rate': self.gold_rate,
                #         'make_rate': self.make_rate,
                #         'make_value': self.make_value / diff_gross ,
                #         'gold_value': self.gold_rate and (new_pure * self.gold_rate) or 0,
                #         'price_unit': self.gold_rate and (new_pure * self.gold_rate) or 0 ,
                #     })
                # else:
                res.update({
                    'gross_wt': self.gross_wt,
                    'pure_wt': self.pure_wt,
                    'purity_id': self.purity_id and self.purity_id.id or False,
                    'purity_diff': self.purity_diff,
                    'gold_rate': self.gold_rate,
                    'make_rate': self.make_rate,
                    'make_value': self.make_value,
                    'gold_value': self.gold_value,
                    'price_unit': self.gold_value / self.product_uom_qty   ,
                    'discount': self.discount ,
                })
        product_object = self.env['product.product'].browse([res.get('product_id')])
        make_value_product = product_object.making_charge_id
        if product_object.is_making_charges:
            sale_order = self.env['sale.order'].browse([self.order_id.id])
            new_gross_wt = 0.00
            new_product_qty = 0.00
            new_received_gross_wt =0.00
            for line in sale_order.order_line:
                if line.product_id == self.product_id:
                    if line.product_id.invoice_policy == 'receive':
                        if line.gross_wt > 0.00 and line.received_gross_wt > 0.00:
                            new_gross_wt = line.gross_wt
                            new_product_qty = line.product_uom_qty
                            new_received_gross_wt = line.received_gross_wt
                    else:
                        if line.gross_wt > 0.00 and line.product_uom_qty > 0.00:
                            new_gross_wt = line.gross_wt
                            new_product_qty = line.product_uom_qty
                            new_received_gross_wt = line.received_gross_wt
                        # print(new_gross_wt)
                        # print(new_product_qty)
                        # print(new_received_gross_wt)
            if self.product_id.invoice_policy == 'delivery':
                if new_received_gross_wt <=0:
                    raise ValidationError(_('You Should Deliver Products First'))
                else:
                    diff_gross =  (new_gross_wt * new_product_qty) / new_received_gross_wt
                if diff_gross > 0.00:
                    res.update({'price_unit': price_un / diff_gross , 'quantity': 1.00,'gold_rate':0.00})
                else:
                    res.update({'price_unit': price_un, 'quantity': 1.00,'gold_rate':0.00})
            else:
                # if new_product_qty <=0:
                #     raise ValidationError(_('DownDown'))
                # else:
                diff_gross =  (new_gross_wt * new_product_qty)
                if diff_gross > 0.00:
                    res.update({'price_unit': price_un / diff_gross , 'quantity': 1.00,'gold_rate':0.00})
                else:
                    res.update({'price_unit': price_un, 'quantity': 1.00,'gold_rate':0.00})


        if self.display_type:
            res['account_id'] = False
        return res

class stock_move(models.Model):
    _inherit='stock.move'
    lot_id = fields.Many2one('stock.production.lot')
    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        self.ensure_one()
        # apply putaway
        location_dest_id = self.location_dest_id._get_putaway_strategy(self.product_id).id or self.location_dest_id.id
        vals = {
            'move_id': self.id,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'location_id': self.location_id.id,
            'location_dest_id': location_dest_id,
            'picking_id': self.picking_id.id,
        }
        if quantity:
            rounding = self.env['decimal.precision'].precision_get('Product Unit of Measure')
            uom_quantity = self.product_id.uom_id._compute_quantity(quantity, self.product_uom, rounding_method='HALF-UP')
            uom_quantity = float_round(uom_quantity, precision_digits=rounding)
            uom_quantity_back_to_product_uom = self.product_uom._compute_quantity(uom_quantity, self.product_id.uom_id, rounding_method='HALF-UP')
            if float_compare(quantity, uom_quantity_back_to_product_uom, precision_digits=rounding) == 0:
                vals = dict(vals, product_uom_qty=uom_quantity)
            else:
                vals = dict(vals, product_uom_qty=quantity, product_uom_id=self.product_id.uom_id.id)
        if reserved_quant:
            # print("reserved_quant")
            # print(reserved_quant)
            # print("reserved_quant")
            vals = dict(
                vals,
                location_id=reserved_quant.location_id.id,
                lot_id=reserved_quant.lot_id.id or False,
                package_id=reserved_quant.package_id.id or False,
                owner_id =reserved_quant.owner_id.id or False,
            )
        # if self.lot_id and self.origin and 'S0' in self.origin:
        #     vals['lot_id'] = self.lot_id.id
        #     print("VALS")
        #     print(vals)
        #     print("VALS")
        return vals
#     def _create_out_svl(self):
#         res = super(stock_move,self)._create_out_svl()
#         res.stock_move_id.sale_line_id.received_gross_wt = res.stock_move_id.sale_line_id.received_gross_wt + res.stock_move_id.gross_weight
#         return res

class StockRule(models.Model):
    _inherit = 'stock.rule'

    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, company_id, values):
        ''' Returns a dictionary of values that will be used to create a stock move from a procurement.
        This function assumes that the given procurement has a rule (action == 'pull' or 'pull_push') set on it.

        :param procurement: browse record
        :rtype: dictionary
        '''
        group_id = False
        if self.group_propagation_option == 'propagate':
            group_id = values.get('group_id', False) and values['group_id'].id
        elif self.group_propagation_option == 'fixed':
            group_id = self.group_id.id

        date_expected = fields.Datetime.to_string(
            fields.Datetime.from_string(values['date_planned']) - relativedelta(days=self.delay or 0)
        )

        partner = self.partner_address_id or (values.get('group_id', False) and values['group_id'].partner_id)
        if partner:
            product_id = product_id.with_context(lang=partner.lang or self.env.user.lang)

        # it is possible that we've already got some move done, so check for the done qty and create
        # a new move with the correct qty
        qty_left = product_qty
        move_values = {
            'name': name[:2000],
            'company_id': self.company_id.id or self.location_src_id.company_id.id or self.location_id.company_id.id or company_id.id,
            'product_id': product_id.id,
            'product_uom': product_uom.id,
            'product_uom_qty': qty_left,
            'partner_id': partner.id if partner else False,
            'location_id': self.location_src_id.id,
            'location_dest_id': location_id.id,
            'move_dest_ids': values.get('move_dest_ids', False) and [(4, x.id) for x in values['move_dest_ids']] or [],
            'rule_id': self.id,
            'procure_method': self.procure_method,
            'origin': origin,
            'picking_type_id': self.picking_type_id.id,
            'group_id': group_id,
            'route_ids': [(4, route.id) for route in values.get('route_ids', [])],
            'warehouse_id': self.propagate_warehouse_id.id or self.warehouse_id.id,
            'date': date_expected,
            'date_expected': date_expected,
            'propagate_cancel': self.propagate_cancel,
            'propagate_date': self.propagate_date,
            'propagate_date_minimum_delta': self.propagate_date_minimum_delta,
            'description_picking': product_id._get_description(self.picking_type_id),
            'priority': values.get('priority', "1"),
            'delay_alert': self.delay_alert,
            'lot_id':values.get('lot_id',False).id
        }
        for field in self._get_custom_move_fields():
            if field in values:
                move_values[field] = values.get(field)
        return move_values

    @api.model
    def _run_pull(self, procurements):
        moves_values_by_company = defaultdict(list)
        mtso_products_by_locations = defaultdict(list)
        print("procurementsprocurementsprocurementsprocurementsprocurements")
        print("procurementsprocurementsprocurementsprocurementsprocurements")
        print("procurementsprocurementsprocurementsprocurementsprocurements")
        print("procurementsprocurementsprocurementsprocurementsprocurements")
        print("procurementsprocurementsprocurementsprocurementsprocurements")
        print(procurements)
        print("procurementsprocurementsprocurementsprocurementsprocurements")
        print("procurementsprocurementsprocurementsprocurementsprocurements")
        print("procurementsprocurementsprocurementsprocurementsprocurements")
        print("procurementsprocurementsprocurementsprocurementsprocurements")
        print("procurementsprocurementsprocurementsprocurementsprocurements")
        # To handle the `mts_else_mto` procure method, we do a preliminary loop to
        # isolate the products we would need to read the forecasted quantity,
        # in order to to batch the read. We also make a sanitary check on the
        # `location_src_id` field.
        for procurement, rule in procurements:
            if not rule.location_src_id:
                msg = _('No source location defined on stock rule: %s!') % (rule.name, )
                raise UserError(msg)

            if rule.procure_method == 'mts_else_mto':
                mtso_products_by_locations[rule.location_src_id].append(procurement.product_id.id)

        # Get the forecasted quantity for the `mts_else_mto` procurement.
        forecasted_qties_by_loc = {}
        for location, product_ids in mtso_products_by_locations.items():
            products = self.env['product.product'].browse(product_ids).with_context(location=location.id)
            forecasted_qties_by_loc[location] = {product.id: product.free_qty for product in products}

        # Prepare the move values, adapt the `procure_method` if needed.
        for procurement, rule in procurements:
            procure_method = rule.procure_method
            if rule.procure_method == 'mts_else_mto':
                qty_needed = procurement.product_uom._compute_quantity(procurement.product_qty, procurement.product_id.uom_id)
                qty_available = forecasted_qties_by_loc[rule.location_src_id][procurement.product_id.id]
                if float_compare(qty_needed, qty_available, precision_rounding=procurement.product_id.uom_id.rounding) <= 0:
                    procure_method = 'make_to_stock'
                    forecasted_qties_by_loc[rule.location_src_id][procurement.product_id.id] -= qty_needed
                else:
                    procure_method = 'make_to_order'

            # print(procurement[7])
            # print(type(procurement[7]))
            # print(len(procurement[7]))
            # print(procurement[7]['lot_id'])
            move_values = rule._get_stock_move_values(*procurement)
            move_values['procure_method'] = procure_method
            moves_values_by_company[procurement.company_id.id].append(move_values)

        for company_id, moves_values in moves_values_by_company.items():
            # create the move as SUPERUSER because the current user may not have the rights to do it (mto product launched by a sale for example)
            moves = self.env['stock.move'].sudo().with_context(force_company=company_id).create(moves_values)
            # Since action_confirm launch following procurement_group we should activate it.
            # print("++++++++++++++++++++++++++++==")
            # print(moves)
            # print(moves_values)
            # print(moves.origin)
            # print(moves.lot_id)
            # print("++++++++++++++++++++++++++++==")
            moves._action_confirm()
            picking_id = self.env['stock.picking'].browse(moves[0].picking_id.id)
            if picking_id.origin:
                if 'S0' in picking_id.origin:
                    sale_order = self.env['sale.order'].search([('name','=',picking_id.origin)])
                    picking_id.write(({
                            'period_from': sale_order.period_from,
                            'period_to': sale_order.period_to,
                            'period_uom_id': sale_order.period_uom_id and sale_order.period_uom_id.id or False
                        }))
                    if sale_order.order_type.gold and sale_order.order_type.is_unfixed:
                        picking_id.write({'sale_type':'unfixed'})
                    elif sale_order.order_type.gold and sale_order.order_type.is_fixed:
                        picking_id.write({'sale_type':'fixed'})
                    for sol in sale_order.order_line:
                        for move in moves:
                            if sol.product_id.id == move.product_id.id:
                                if move.product_id.categ_id.is_scrap:
                                    move.update({
                                        'gross_weight': sol.gross_wt,
                                        'pure_weight': sol.pure_wt,
                                        'purity': sol.purity_id.scrap_purity or 1,
                                        'gold_rate': sol.gold_rate,
                                        'selling_karat_id':
                                            sol.product_id.product_template_attribute_value_ids and
                                            sol.product_id.product_template_attribute_value_ids.mapped(
                                                'product_attribute_value_id')[0].id or
                                            False
                                    })
                                else:
                                    move.update({
                                        'carat': sol.carat,
                                        'gross_weight': sol.gross_wt * sol.product_uom_qty,
                                        'pure_weight': sol.pure_wt,
                                        'purity': sol.purity_id.purity or 1,
                                        'gold_rate': sol.gold_rate,
                                        'selling_karat_id':
                                            sol.product_id.product_template_attribute_value_ids and
                                            sol.product_id.product_template_attribute_value_ids.mapped(
                                                'product_attribute_value_id')[0].id or
                                            False
                                    })
        return True

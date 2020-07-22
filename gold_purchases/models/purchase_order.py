# -*- coding: utf-8 -*-
from odoo import api, fields, models
from datetime import date , timedelta , datetime


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    period_from = fields.Float('Period From')
    period_to = fields.Float('Period To')
    period_uom_id = fields.Many2one('uom.uom', 'Period UOM')
    is_gold_fixed = fields.Boolean(string='Is Gold Fixed',
                                   compute='check_gold_fixed')
    stock_move_id = fields.Many2one('account.move', string='Stock Entry – Gold')
    bill_move_id = fields.Many2one('account.move', string='Bill Entry - Gold')

    @api.model
    def _prepare_picking(self):
        res = super(PurchaseOrder, self)._prepare_picking()
        res.update({
            'period_from': self.period_from,
            'period_to': self.period_to,
            'period_uom_id': self.period_uom_id and self.period_uom_id.id or False
        })
        return res

    @api.depends('order_type')
    def check_gold_fixed(self):
        for rec in self:
            rec.is_gold_fixed = rec.order_type and \
                                rec.order_type.is_fixed and \
                                rec.order_type.gold and True or False


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    price_unit = fields.Float(string='Unit Price', required=True,
                              digits='Product Price', copy=False, default=0)
    gross_wt = fields.Float('Gross Wt', digits=(16, 3))
    purity_id = fields.Many2one('gold.purity', 'Purity')
    pure_wt = fields.Float('Pure Wt', compute='_get_gold_rate', digits=(16, 3))
    purity_diff = fields.Float('Purity +/-', digits=(16, 3))
    total_pure_weight = fields.Float('Pure Weight', compute='_get_gold_rate',
                                     digits=(16, 3))
    stock = fields.Float('Stock', compute='_get_gold_rate', digits=(16, 3))
    make_rate = fields.Monetary('Make Rate/G', digits=(16, 3))
    make_value = fields.Monetary('Make Value', compute='_get_gold_rate',
                                 digits=(16, 3))
    gold_rate = fields.Float('Gold Rate/G', compute='_get_gold_rate',
                             digits=(16, 3))
    gold_value = fields.Monetary('Gold Value', compute='_get_gold_rate',
                                 digits=(16, 3))
    
    
    @api.model
    def create(self, vals):
        res = super(PurchaseOrderLine, self).create(vals)
        
        if vals.get('product_id'):
            product_object = self.env['product.product'].browse([vals.get('product_id')])
            if product_object.gold:
                make_value_product = self.env.ref('gold_purchases.make_value_product')
                uom = self.env.ref('uom.product_uom_unit')
                make = self.env['purchase.order.line'].create({
                                    'product_id': make_value_product.id,
                                    'name': make_value_product.name,
                                    'product_qty': 1,
                                    'price_unit': 0.00,
                                    'product_uom': uom.id,
                                    'order_id': vals.get('order_id'),
                                    'date_planned': datetime.today() ,
                                    'price_subtotal': (vals.get('gross_wt') * vals.get('make_rate')),
                                })
        return res

                

    @api.depends('product_id', 'product_qty', 'price_unit', 'gross_wt',
                 'purity_id', 'purity_diff', 'make_rate',
                 'order_id', 'order_id.order_type', 'order_id.currency_id')
    def _get_gold_rate(self):
        for rec in self:
            make_value_product = self.env.ref('gold_purchases.make_value_product')
            product_make_object = self.env['purchase.order.line'].search([('order_id','=',rec.order_id.id),('product_id','=',make_value_product.id)])
            rec.pure_wt = rec.gross_wt * (rec.purity_id and (
                    rec.purity_id.purity / 1000.000) or 1)
            rec.total_pure_weight = rec.pure_wt
            # NEED TO ADD PURITY DIFF + rec.purity_diff
            rec.stock = (rec.product_id and rec.product_id.available_gold or
                         0.00) + rec.pure_wt + rec.purity_diff
            rec.make_value = rec.gross_wt * rec.make_rate
            rec.gold_rate = rec.order_id.gold_rate / 1000.000000000000
            rec.gold_value = rec.gold_rate and (
                    rec.total_pure_weight * rec.gold_rate) or 0
            product_basic_line = self.env['purchase.order.line'].search([('order_id','=',rec.order_id.id),('product_id','!=',make_value_product.id)])
            if rec.product_id.id == make_value_product.id:
                for line in product_basic_line:
                    product_make_object.write({'price_subtotal' : line.gross_wt * line.make_rate})

            

    @api.depends('product_qty', 'price_unit', 'taxes_id', 'gross_wt',
                 'purity_id', 'purity_diff', 'make_rate',
                 'order_id', 'order_id.order_type',
                 'order_id.state', 'order_id.order_type.gold')
    def _compute_amount(self):
        for line in self:
            if line.order_id and line.order_id.order_type.is_fixed and \
                    line.product_id.gold:
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
                    'price_unit': 0
                })
            else:
                vals = line._prepare_compute_all_values()
                taxes = line.taxes_id.compute_all(
                    vals['price_unit'],
                    vals['currency_id'],
                    vals['product_qty'],
                    vals['product'],
                    vals['partner'])
                line.update({
                    'price_tax': sum(
                        t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                    'price_total': taxes['total_included'],
                    'price_subtotal': taxes['total_excluded'],
                })

    def _prepare_stock_moves(self, picking):
        res = super(PurchaseOrderLine, self)._prepare_stock_moves(picking)
        res and res[0].update({
            'gross_weight': self.gross_wt,
            'pure_weight': self.pure_wt,
            'purity': self.purity_id.purity or 1,
            'gold_rate': self.gold_rate,
            'selling_karat_id':
                self.product_id.product_template_attribute_value_ids and
                self.product_id.product_template_attribute_value_ids.mapped(
                    'product_attribute_value_id')[0].id or
                False
        })
        return res

    def _prepare_account_move_line(self, move):
        res = super(PurchaseOrderLine, self)._prepare_account_move_line(move)
        res.update({
            'gross_wt': self.gross_wt,
            'pure_wt': self.total_pure_weight,
            'purity_id': self.purity_id and self.purity_id.id or False,
            'purity_diff': self.purity_diff,
            'gold_rate': self.gold_rate,
            'make_rate': self.make_rate,
            'make_value': self.make_value,
            'gold_value': self.gold_value,
            'price_unit': self.gold_value ,
        })
        return res

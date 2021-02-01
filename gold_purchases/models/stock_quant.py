""" init object stock.quant """

import logging

from odoo import fields, models, api

LOGGER = logging.getLogger(__name__)


class StockQuant(models.Model):
    """ init object stock.quant """
    _inherit = 'stock.quant'


    diamond = fields.Boolean(string="Stone", compute="_compute_gold_state")
    gold = fields.Boolean(string="Gold", compute="_compute_gold_state")
    def _compute_gold_state(self):
        for this in self:
            if this.product_id.categ_id.is_gold:
                this.gold = True
                this.diamond = False
            else:
                this.gold = False
                this.diamond = True
    move_line_id = fields.Many2one(comodel_name="stock.move.line",
                                   compute="_compute_move_line_values",
                                   string="Move Line", )
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
    gross_weight = fields.Float(compute="_compute_move_line_values",
                                string='Gross Weight', )
    purity = fields.Float(string="Purity",
                          compute="_compute_move_line_values", )
    pure_weight = fields.Float(string="Pure Weight", digits=(16, 3),
                               compute="_compute_move_line_values", )

    item_category_id = fields.Many2one('item.category', string="Item Category",
                                       compute="_compute_move_line_values",
                                       search="_search_item_category_id")
    sub_category_id = fields.Many2one('item.category.line',
                                      string="Sub Category",
                                      search="_search_sub_category_id",
                                      compute="_compute_move_line_values", )
    selling_karat_id = fields.Many2one('product.attribute.value',
                                       string="Selling Karat",
                                       search="_search_selling_karat_id",
                                       compute="_compute_move_line_values", )
    selling_making_charge = fields.Monetary('Selling Making Charge',
                                            digits=(16, 3),
                                            compute="_compute_move_line_values", )

    @api.depends('lot_id', 'product_id')
    def _compute_move_line_values(self):
        """
        Compute move_line_id
        """
        for rec in self:
            gross_weight = 0
            purity = 0
            pure_weight = 0
            item_category_id = self.env['item.category']
            sub_category_id = self.env['item.category.line']
            selling_karat_id = self.env['product.attribute.value']
            selling_making_charge = 0
            move_line_id = self.env['stock.move.line']
            if rec.lot_id and rec.product_id:
                move_line_id = move_line_id.search([
                    ('lot_id', '=', rec.lot_id.id),
                    ('product_id', '=', rec.product_id.id)
                ], limit=1)
                if move_line_id:
                    gross_weight = move_line_id.gross_weight
                    purity = move_line_id.purity
                    pure_weight = move_line_id.pure_weight
                    item_category_id = move_line_id.item_category_id
                    sub_category_id = move_line_id.sub_category_id
                    selling_karat_id = move_line_id.selling_karat_id
                    selling_making_charge = move_line_id.selling_making_charge
            rec.gross_weight = gross_weight
            rec.purity = purity
            rec.pure_weight = pure_weight
            rec.item_category_id = item_category_id
            rec.sub_category_id = sub_category_id
            rec.selling_karat_id = selling_karat_id
            rec.selling_making_charge = selling_making_charge
            rec.move_line_id = move_line_id

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None,
                   orderby=False, lazy=True):
        """
        Override read_group
        """
        result = super(StockQuant, self).read_group(domain, fields, groupby,
                                                    offset=offset, limit=limit,
                                                    orderby=orderby, lazy=lazy)
        quants = self.env['stock.quant']
        for line in result:
            if '__domain' in line:
                quants = self.search(line['__domain'])
            if 'gross_weight' in fields:
                line['gross_weight'] = sum(quants.mapped('gross_weight'))
            if 'purity' in fields:
                line['purity'] = sum(quants.mapped('purity'))
            if 'pure_weight' in fields:
                line['pure_weight'] = sum(quants.mapped('pure_weight'))
            if 'selling_making_charge' in fields:
                line['selling_making_charge'] = sum(quants.mapped(
                    'selling_making_charge'))
        return result
    def _search_item_category_id(self, operator, value):
        """
        Search item_category_id
        """
        ids = []
        quants = self.env['stock.quant'].search([])
        if isinstance(value, int):
            ids = quants.filtered(lambda q: q.item_category_id.id == value).ids
        elif isinstance(value, str):
            ic_ids = self.env['item.category'].search(
                [('name', 'ilike', value)]).ids
            ids = quants.filtered(
                lambda q: q.item_category_id and q.item_category_id.id in ic_ids
            ).ids
        elif isinstance(value, bool):
            if operator == '=' and value or operator == '!=' and not value:
                ids = quants.filtered(lambda q: q.item_category_id).ids
            else:
                ids = quants.filtered(lambda q: not q.item_category_id).ids
        if ids:
            return [('id', 'in', ids)]
        return []

    def _search_sub_category_id(self, operator, value):
        """
        Search sub_category_id
        """
        ids = []
        quants = self.env['stock.quant'].search([])
        if isinstance(value, int):
            ids = quants.filtered(lambda q: q.sub_category_id.id == value).ids
        elif isinstance(value, str):
            icl_ids = self.env['item.category.line'].search(
                [('name', 'ilike', value)]).ids
            ids = quants.filtered(
                lambda q: q.sub_category_id and q.sub_category_id.id in icl_ids
            ).ids
        elif isinstance(value, bool):
            if operator == '=' and value or operator == '!=' and not value:
                ids = quants.filtered(lambda q: q.sub_category_id).ids
            else:
                ids = quants.filtered(lambda q: not q.sub_category_id).ids
        if ids:
            return [('id', 'in', ids)]
        return []


    def _search_selling_karat_id(self, operator, value):
        """
        Search selling_karat_id
        """
        ids = []
        quants = self.env['stock.quant'].search([])
        if isinstance(value, int):
            ids = quants.filtered(lambda q: q.selling_karat_id.id == value).ids
        elif isinstance(value, str):
            pavids = self.env['product.attribute.value'].search(
                [('name', 'ilike', value)]).ids
            ids = quants.filtered(
                lambda q: q.selling_karat_id and q.selling_karat_id.id in pavids
            ).ids
        elif isinstance(value, bool):
            if operator == '=' and value or operator == '!=' and not value:
                ids = quants.filtered(lambda q: q.selling_karat_id).ids
            else:
                ids = quants.filtered(lambda q: not q.selling_karat_id).ids
        if ids:
            return [('id', 'in', ids)]
        return []

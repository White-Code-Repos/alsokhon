""" init object stock.quant """

import logging

from odoo import fields, models, api

LOGGER = logging.getLogger(__name__)


class StockQuant(models.Model):
    """ init object stock.quant """
    _inherit = 'stock.quant'

    total_value = fields.Float(string="Total Value", digits=(16, 3), compute="_compute_total_value_gold")
    def _compute_total_value_gold(self):
        for this in self:
            this.total_value = this.gross_weight * this.value
    # purity_id = fields.Many2one('gold.purity', 'Purity', compute='_get_gold_rate',)
    # pure_wt = fields.Float('Pure Wt', compute='_get_gold_rate', digits=(16, 3))
    # total_pure_weight = fields.Float('Pure Weight', compute='_get_gold_rate',digits=(16, 3))
    # purity_diff = fields.Float('Purity +/-', digits=(16, 3))
    # gold_rate = fields.Float('Gold Rate/G', compute='_get_gold_rate',digits=(16, 3))
    # gold_value = fields.Float("Total Value", compute="_compute_gold_value")
    #
    # def _get_gold_rate(self):
    #     for rec in self:
    #         if rec.lot_id and rec.product_id:
    #             move_line_id = move_line_id.search([
    #                 ('lot_id', '=', rec.lot_id.id),
    #                 ('product_id', '=', rec.product_id.id)
    #             ], limit=1)
    #             if move_line_id and move_line_id.move_id and move_line_id.move_id:
    #                 rec.pure_wt = rec.product_qty * rec.gross_wt * (rec.purity_id and (
    #                         rec.purity_id.purity / 1000.000) or 0)
    #                 rec.total_pure_weight = rec.pure_wt + rec.purity_diff
    #                 # NEED TO ADD PURITY DIFF + rec.purity_diff
    #                 new_pure_wt = rec.pure_wt + rec.purity_diff
    #                 rec.stock = (rec.product_id and rec.product_id.available_gold or
    #                              0.00) + new_pure_wt
    #
    #                 rec.make_value = rec.product_qty * rec.gross_wt * rec.make_rate
    #                 rec.gold_rate = rec.order_id.gold_rate / 1000.000000000000
    #                 rec.gold_value = rec.gold_rate and (
    #                         rec.total_pure_weight * rec.gold_rate) or 0
    #                 rec.total_gross_wt = rec.gross_wt * rec.product_qty

# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductCategory(models.Model):
    _inherit = 'product.category'

    is_gold = fields.Boolean('Is Gold')
    is_scrap = fields.Boolean(string='Scrap')
    is_assembly = fields.Boolean('Assembly')

# # -*- coding: utf-8 -*-
from odoo import models, fields, api


class Ks_RecentlyViewedProducts(models.Model):
    _inherit = 'res.users'
    _description = 'Adding product template to res users'

    ks_viewed_products = fields.Many2many("product.template",'product_template_res_user',
                                          'res_user_id', 'product_template_id')



class Ks_ProductTemplate(models.Model):
    _inherit = 'product.template'
    _description = 'Adding users to products'

    ks_products_templates = fields.Many2many("res.users",'product_template_res_users')


class ks_RcentlyViewedRel(models.Model):
    _name = "product.template.res.users"
    _description = 'A rel table for user and their recently viewed products'

    product_template_id = fields.Many2one("product.template")
    res_user_id = fields.Many2one("res.users")
    recently_viewed_date = fields.Datetime(default=fields.Datetime.now())


class KSRATING(models.AbstractModel):
    _inherit = 'rating.mixin'
    _description = 'rating for published product only'

    def _rating_domain(self):
        """ Returns a normalized domain on rating.rating to select the records to
            include in count, avg, ... computation of current model.
        """
        return ['&', '&', ('res_model', '=', self._name), ('res_id', 'in', self.ids), ('consumed', '=', True), ('website_published', '=', True)]



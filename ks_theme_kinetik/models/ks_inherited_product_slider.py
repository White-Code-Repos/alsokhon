# # -*- coding: utf-8 -*-
from odoo import models, fields, api



class Ks_IrUiView(models.Model):
    _inherit = "ks_product.slider"

    ks_is_full_width = fields.Boolean(string="Full Width",default=False)

class Ks_IrUiView(models.Model):
    _inherit = "ks_product.grid"

    ks_template_selection = fields.Selection([('t1', 'Template1'), ('t2', 'Template2'), ],
                                             string='Template type', required='true', default='t1')

class Ks_Alternate_Slider(models.Model):
    _inherit = 'product.template'

    ks_is_accessories_slider = fields.Boolean("Accessories Slider", default=False)
    ks_accessories_repeat_product = fields.Boolean("Repeat Product", default=False)
    ks_accessories_slider_speed = fields.Integer("Slider Speed")
    ka_accessories_automitic_slider = fields.Boolean("Auto Slider", default=False)
    ks_accessories_navigation = fields.Boolean("Navigation buttons", default=False)

    ks_is_alternate_slider = fields.Boolean("Alternate Slider", default=False)
    ks_alternate_repeat_product = fields.Boolean("Repeat Product", default=False)
    ks_alternate_slider_speed = fields.Integer("Slider Speed")
    ka_alternate_automitic_slider = fields.Boolean("Auto Slider", default=False)
    ks_alternate_navigation = fields.Boolean("Navigation buttons", default=False)

class Ks_Breadcumb_Image(models.Model):
    _name = 'ks_theme_kinetik.ks_breadcumb'
    _description = "use to display image for default breadcrumb"

    name = fields.Char('Name', default='Shop Breadcumb')
    breadcumb_image = fields.Binary("Breadcumb Image")
    ks_breadcumb_image_url = fields.Char('url', compute='calculate_image_url',store=True)

    @api.depends('breadcumb_image')
    def calculate_image_url(self):
        self.ks_breadcumb_image_url = "/web/image/ks_theme_kinetik.ks_breadcumb/" + str(self.id) + "/breadcumb_image"


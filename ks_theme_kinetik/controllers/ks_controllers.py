# -*- coding: utf-8 -*-

from odoo import http,fields
from odoo.http import request
import json
from odoo.addons.website_sale.controllers.main import WebsiteSale
from datetime import datetime
from odoo.addons.http_routing.models.ir_http import slug
from odoo import http
from odoo.addons.website_sale.controllers.variant import WebsiteSaleVariantController


class WebsiteSaleStockVariantController(WebsiteSaleVariantController):
    def second_calculation(self, date_start, date_end):
        date_end = datetime(date_end.year, date_end.month, date_end.day,23,59,59)
        date_start = datetime(date_start.year, date_start.month, date_start.day)
        now = datetime.now()
        if (now >= date_start and date_end >= now):
            seconds = int((date_end - now).total_seconds())
        else:
            seconds = 0
        return seconds

    @http.route()
    def get_combination_info_website(self, product_template_id, product_id, combination, add_qty, **kw):
        kw['context'] = {'website_sale_stock_get_quantity': True}
        res = super(WebsiteSaleStockVariantController, self).get_combination_info_website(product_template_id,
                                                                                           product_id, combination,
                                                                                           add_qty, **kw)
        kw.pop('pricelist_id')
        seconds = 0
        product = request.env['product.product'].browse(res['product_id'])
        suitable_pricelist_id = request.website.get_current_pricelist()._compute_price_rule(
            list(zip(product, [add_qty], [False])),
            date=False,
            uom_id=False
        )[res['product_id']][1]
        ks_pricelist_item = request.env['product.pricelist.item'].sudo().browse(suitable_pricelist_id)
        if ks_pricelist_item.date_start and ks_pricelist_item.date_end:
            date_start = ks_pricelist_item.date_start
            date_end = ks_pricelist_item.date_end
            if (date_end and date_start):
                seconds = self.second_calculation(date_start, date_end)
        res.update({
            "seconds": seconds,
        })
        return res


class WebsiteSale(WebsiteSale):


    # result = len(listOfStrings) > 0 and all(elem == listOfStrings[0] for elem in listOfStrings)

    @http.route([
        '/ks_deal_of_the_day',
    ], type='json', auth="public", website=True)
    def ks_deal_of_the_day(self):
        value = []
        qty = []
        item_ids = request.env['ks_theme_kinetik.ks_deal_of_the_day'].sudo().search([]).ks_selected_product.item_ids
        for x in range(0, len(item_ids)):
            qty.append(item_ids[x].min_quantity)
        if (len(qty) > 0):
            if not (len(qty) > 0 and all(elem == qty[0] for elem in qty)):
                # index = qty.index(max(qty))
                item_ids = request.env['ks_theme_kinetik.ks_deal_of_the_day'].sudo().search(
                    []).ks_selected_product.item_ids.search([], order='min_quantity DESC')[0]
            else:
                item_ids = request.env['ks_theme_kinetik.ks_deal_of_the_day'].sudo().search(
                    []).ks_selected_product.item_ids.search([], order='create_date DESC')[0]
        date_start = item_ids.date_start
        date_end = item_ids.date_end
        if not (date_end and date_start):
            seconds = 0
        else:
            seconds = self.second_calculation(date_start, date_end)
        value.append(seconds)
        apld_on = item_ids.applied_on
        if apld_on == '0_product_variant':
            prd_vrnt = item_ids.product_id.product_tmpl_id
            url = "/shop/product/%s" % slug(prd_vrnt)
        elif apld_on == '1_product':
            prd = item_ids.product_tmpl_id
            url = "/shop/product/%s" % slug(prd)
        elif apld_on == '2_product_category':
            url = "/shop"
        elif apld_on == '3_global':
            url = "/shop"
        value.append(url)
        return value

    @http.route([
        '/ks_product_images',
    ], type='json', auth="public", website=True)
    def ks_multi_images(self, **kw):
        ks_p_id = int(kw['ks_p_id'])
        value = []
        res_env = request.env['product.template'].sudo().search([('id', '=', ks_p_id)])
        if res_env.ks_is_accessories_slider:
            ks_prod_accessories = {
                "name": "Accessories",
                "ks_navigation": res_env.ks_accessories_navigation,
                "ks_is_slider": res_env.ks_is_accessories_slider,
                "ks_repeat": res_env.ks_accessories_repeat_product,
                "ks_speed": res_env.ks_accessories_slider_speed,
                "ks_auto": res_env.ka_accessories_automitic_slider,
                'rtl': request.env['res.lang'].search([('code', '=', request.env.lang)]).direction == 'rtl'
            }
            value.append(ks_prod_accessories)
        if res_env.ks_is_alternate_slider:
            ks_prod_alternate = {
                "name": "Alternate",
                "ks_navigation": res_env.ks_alternate_navigation,
                "ks_slider": res_env.ks_is_alternate_slider,
                "ks_repeat": res_env.ks_alternate_repeat_product,
                "ks_speed": res_env.ks_alternate_slider_speed,
                "ks_auto": res_env.ka_alternate_automitic_slider,
                'rtl': request.env['res.lang'].search([('code', '=', request.env.lang)]).direction == 'rtl'
            }
            value.append(ks_prod_alternate)

        return value

    # @http.route(['/shop/wishlist/remove/<model("product.wishlist"):wish>'], type='json', auth="public", website=True)
    # def rm_from_wishlist(self, wish, **kw):
    #
    #     """Here we have override the wishlist remove controller form product.wishlist model.
    #     This is used to remove procuct from wishlist for every user and each website"""
    #     request.env['product.wishlist'].sudo().search([('id', '=', wish.id)]).unlink()
    #     return True

    @http.route(['/shop/cart/update'], type='http', auth="public", methods=['POST'], website=True, csrf=False)
    def cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
        """This is used to handle event of add to cart button redirect from detail page but only add fron shop page"""
        super(WebsiteSale, self).cart_update(product_id, add_qty, set_qty, **kw)
        if kw.get('express'):
            return request.redirect("/shop/checkout?express=1")
        elif 'product_template_id' in kw or 'timer' in kw:
            return request.redirect("/shop/cart")
        else:
            return request.redirect('/shop')
    # This is used for update the count of product
    # @http.route(["/cart/count/update"], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    # def cart_update_grid(self,product_id, add_qty=1, set_qty=0, **kw):
    #     quantity= request.website.sale_get_order().cart_quantity
    #     return quantity

    @http.route(["/details/cart/update"], type='json', auth="public", methods=['POST'], website=True, csrf=False)
    def cart_update_grid_modal(self,**kw):
        optional_product_len = len(
            request.env['product.template'].sudo().search([('id', '=', int(kw['template_id']))]).optional_product_ids)
        return optional_product_len

    @http.route(['/ks_shop/cart/update'], type='http', auth="public", methods=['POST'], website=True, csrf=False)
    def ks_cart_update(self, product_id, add_qty=1, set_qty=0, **kw):
        """This route is called when adding a product to cart (no options)."""
        sale_order = request.website.sale_get_order(force_create=True)
        if sale_order.state != 'draft':
            request.session['sale_order_id'] = None
            sale_order = request.website.sale_get_order(force_create=True)

        product_custom_attribute_values = None
        if kw.get('product_custom_attribute_values'):
            product_custom_attribute_values = json.loads(kw.get('product_custom_attribute_values'))

        no_variant_attribute_values = None
        if kw.get('no_variant_attribute_values'):
            no_variant_attribute_values = json.loads(kw.get('no_variant_attribute_values'))

        sale_order._cart_update(
            product_id=int(product_id),
            add_qty=add_qty,
            set_qty=set_qty,
            product_custom_attribute_values=product_custom_attribute_values,
            no_variant_attribute_values=no_variant_attribute_values
        )
        return request.redirect("/")

    @http.route('/beauty', auth='public', website=True)
    def ks_beauty(self, **kw):
        return http.request.render('ks_theme_kinetik.ks_theme_beauty')

    @http.route('/fitness', auth='public', website=True)
    def ks_gym(self, **kw):
        return http.request.render('ks_theme_kinetik.ks_theme_gym')

    @http.route('/corporate', auth='public', website=True)
    def ks_corporate(self, **kw):
        return http.request.render('ks_theme_kinetik.ks_theme_corporate')

    @http.route('/medical', auth='public', website=True)
    def ks_medical(self, **kw):
        return http.request.render('ks_theme_kinetik.ks_theme_hospital')

    @http.route('/furniture', auth='public', website=True)
    def ks_furniture(self, **kw):
        return http.request.render('ks_theme_kinetik.ks_theme_furniture')

    @http.route('/food', auth='public', website=True)
    def ks_food(self, **kw):
        return http.request.render('ks_theme_kinetik.ks_theme_food')

    @http.route('/pet', auth='public', website=True)
    def ks_pet_shop(self, **kw):
        return http.request.render('ks_theme_kinetik.ks_theme_pet')

    @http.route('/jewel', auth='public', website=True)
    def ks_jewellery_shop(self, **kw):
        return http.request.render('ks_theme_kinetik.ks_theme_jewellery')

    @http.route('/watch', auth='public', website=True)
    def ks_watch_shop(self, **kw):
        return http.request.render('ks_theme_kinetik.ks_theme_watch')

    @http.route('/about', auth='public', website=True)
    def ks_about(self, **kw):
        return http.request.render('ks_theme_kinetik.ks_theme_about_us')

    @http.route('/team', auth='public', website=True)
    def ks_team(self, **kw):
        return http.request.render('ks_theme_kinetik.ks_theme_team')

    @http.route('/price', auth='public', website=True)
    def ks_price(self, **kw):
        return http.request.render('ks_theme_kinetik.ks_theme_pricing')

    @http.route('/services', auth='public', website=True)
    def ks_services(self, **kw):
        return http.request.render('ks_theme_kinetik.ks_theme_services')

    @http.route('/books', auth='public', website=True)
    def ks_services(self, **kw):
        return http.request.render('ks_theme_kinetik.ks_theme_books')

    @http.route(['/shop/product/<model("product.template"):product>'], type='http', auth="public", website=True)
    def product(self, product, category='', search='', **kwargs):
        seconds = 0
        values = super(WebsiteSale, self).product(product, category, search)
        values.qcontext.update({
            "current_url_fb": "http://www.facebook.com/sharer/sharer.php?u=" + request.httprequest.base_url,
            "current_url_twit": "https://twitter.com/intent/tweet?text=" + request.httprequest.base_url,
            "current_url_lin": "http://www.linkedin.com/shareArticle?mini=true-url=" + request.httprequest.base_url,
            "current_url_gplus": "https://plus.google.com/share?url=" + request.httprequest.base_url,
            "seconds": seconds,
            'unit_of_measure_name':request.env['product.template'].browse(product.id).sudo()._get_weight_uom_name_from_ir_config_parameter()
        })
        query = "select product_template_id FROM product_template_res_users where res_user_id = %s ORDER BY recently_viewed_date DESC"
        request.env.cr.execute(query, (request.env.user.id,))
        ids = request.env.cr.fetchall()
        product_template_ids = [i[0] for i in ids]
        if product.id not in product_template_ids:
            request.env.cr.execute("insert into product_template_res_users"
                                   "  (res_user_id, product_template_id,recently_viewed_date)"
                                   "  values"
                                   "  (%s, %s, %s)",
                                   (request.env.user.id, product.id, fields.Datetime.now()))
        else:
            request.env.cr.execute(
                'UPDATE product_template_res_users SET recently_viewed_date=%s WHERE product_template_id=%s and res_user_id=%s',
                (fields.Datetime.now(), product.id, request.env.user.id))
        return request.render("website_sale.product", values.qcontext)

# -*- coding: utf-8 -*-
import json
from odoo.addons.website_sale.controllers import main
from werkzeug.exceptions import NotFound
from odoo import fields, http, tools, _
from odoo.http import request
from odoo.addons.http_routing.models.ir_http import slug
from odoo.addons.website.controllers.main import QueryURL
from odoo.addons.website.models.ir_http import sitemap_qs2dom
from odoo.osv import expression
import math

main.PPG = 24
PPG=main.PPG
PPR = 4

"""
     To optimize search when user clicks on a brand it will filter data and render products template
     @override 
"""

class TableCompute(object):

    def __init__(self):
        self.table = {}

    def _check_place(self, posx, posy, sizex, sizey, ppr):
        res = True
        for y in range(sizey):
            for x in range(sizex):
                if posx + x >= ppr:
                    res = False
                    break
                row = self.table.setdefault(posy + y, {})
                if row.setdefault(posx + x) is not None:
                    res = False
                    break
            for x in range(ppr):
                self.table[posy + y].setdefault(x, None)
        return res

    def process(self, products, ppg=24, ppr=4):
        # Compute products positions on the grid
        minpos = 0
        index = 0
        maxy = 0
        x = 0
        for p in products:
            x = min(max(p.website_size_x, 1), ppr)
            y = min(max(p.website_size_y, 1), ppr)
            if index >= ppg:
                x = y = 1

            pos = minpos
            while not self._check_place(pos % ppr, pos // ppr, x, y, ppr):
                pos += 1
            # if 21st products (index 20) and the last line is full (ppr products in it), break
            # (pos + 1.0) / ppr is the line where the product would be inserted
            # maxy is the number of existing lines
            # + 1.0 is because pos begins at 0, thus pos 20 is actually the 21st block
            # and to force python to not round the division operation
            if index >= ppg and ((pos + 1.0) // ppr) > maxy:
                break

            if x == 1 and y == 1:   # simple heuristic for CPU optimization
                minpos = pos // ppr

            for y2 in range(y):
                for x2 in range(x):
                    self.table[(pos // ppr) + y2][(pos % ppr) + x2] = False
            self.table[pos // ppr][pos % ppr] = {
                'product': p, 'x': x, 'y': y,
                'class': " ".join(x.html_class for x in p.website_style_ids if x.html_class)
            }
            if index <= ppg:
                maxy = max(maxy, y + (pos // ppr))
            index += 1

        # Format table according to HTML needs
        rows = sorted(self.table.items())
        rows = [r[1] for r in rows]
        for col in range(len(rows)):
            cols = sorted(rows[col].items())
            x += len(cols)
            rows[col] = [r[1] for r in cols if r[1]]

        return rows


class WebsiteSale(main.WebsiteSale):
    """ @Override
        To add other domains for the search box
    """

    def _get_search_domain(self, search, category, attrib_values, brand=None, ks_max_selected_price= None,ks_min_selected_price=None):
        domain = request.website.sale_product_domain()
        try:
            if search:
                for srch in search.split(" "):
                    domain += [
                        '|', '|', '|', '|', '|', ('name', 'ilike', srch), ('description', 'ilike', srch),
                        ('description_sale', 'ilike', srch), ('ks_product_brand_id.name', 'ilike', srch),
                        ('public_categ_ids.name', 'ilike', srch), ('product_variant_ids.default_code', 'ilike', srch)]
            if category:
                domain += [('public_categ_ids', 'child_of', int(category))]

            if attrib_values:
                attrib = None
                ids = []
                for value in attrib_values:
                    if not attrib:
                        attrib = value[0]
                        ids.append(value[1])
                    elif value[0] == attrib:
                        ids.append(value[1])
                    elif attrib == 0:
                        domain += [('ks_product_brand_id.id', 'in', ids)]
                    else:
                        domain+=([('attribute_line_ids.value_ids', 'in', ids)])
                        attrib = value[0]
                        ids = [value[1]]
                if attrib:
                    domain+=([('attribute_line_ids.value_ids', 'in', ids)])
                elif attrib == 0:
                    domain += [('ks_product_brand_id.id', 'in', ids)]
            if brand:
                attrib = None
                ids = []
                for value in brand:
                    if not attrib:
                        attrib = value[0]
                        ids.append(value[1])
                    elif value[0] == attrib:
                        ids.append(value[1])
                    elif attrib == 0:
                        domain += [('ks_product_brand_id.id', 'in', ids)]

                domain += [('ks_product_brand_id.id', 'in', ids)]
            if ks_min_selected_price and ks_max_selected_price:
                domain += [('list_price', '<=', float(ks_max_selected_price)),
                       ('list_price', '>=', float(ks_min_selected_price))]

            return domain
        except Exception:
            pass

    def sitemap_shop(env, rule, qs):
        if not qs or qs.lower() in '/shop':
            yield {'loc': '/shop'}

        Category = env['product.public.category']
        dom = sitemap_qs2dom(qs, '/shop/category', Category._rec_name)
        dom += env['website'].get_current_website().website_domain()
        for cat in Category.search(dom):
            loc = '/shop/category/%s' % slug(cat)
            if not qs or qs.lower() in loc:
                yield {'loc': loc}

    def ks_getShopValues(self, page=0, category=None, search='', ppg=False, **post):
        add_qty = int(post.get('add_qty', 1))
        Category = request.env['product.public.category']
        if category:
            category = Category.search([('id', '=', int(category))], limit=1)
            if not category or not category.can_access_from_current_website():
                raise NotFound()
        else:
            category = Category

        if ppg:
            try:
                ppg = int(ppg)
                post['ppg'] = ppg
            except ValueError:
                ppg = False
        if not ppg:
            ppg = 24

        ppr = request.env['website'].get_current_website().shop_ppr or 4

        if request.httprequest.args.getlist('attrib'):
            attrib_list = request.httprequest.args.getlist('attrib')
            try:
                if post.get('filter_variant_remove'):
                    attrib_list.remove(post['filter_variant_remove'])
            except:
                pass
        else:
            attrib_list = post.get('attrib')
            try:
                if post.get('filter_variant_remove'):
                    attrib_list.remove(post['filter_variant_remove'])
            except:
                pass
        if attrib_list == None:
            attrib_list = []
        attrib_values = [[int(x) for x in v.split("-")] for v in attrib_list if v]
        attributes_ids = {v[0] for v in attrib_values}
        attrib_set = {v[1] for v in attrib_values}
        brnd_list = post.get('brnd', request.httprequest.args.getlist('brnd'))
        if request.httprequest.args.getlist('brnd'):
            brnd_list = request.httprequest.args.getlist('brnd')
            try:
                if post.get('filter_brand_remove'):
                    brnd_list.remove(post['filter_brand_remove'])
            except:
                pass
        else:
            brnd_list = post.get('brnd')
            try:
                if post.get('filter_brand_remove'):
                    brnd_list.remove(post['filter_brand_remove'])
            except:
                pass
        if brnd_list == None:
            brnd_list = []
        if 'filter' in post:
            ks_filer_val = post['filter']
            filter = ks_filer_val.split("_")
            if filter.__len__() == 2 and filter[0] == "brand":
                # search = filter[1]
                brnd_list = ['0-' + str(
                    request.env["ks_product_manager.ks_brand"].search([("name", "=", filter[1])], limit=1).id)]
        brnds_values = [[int(x) for x in v.split("-")] for v in brnd_list if v]
        brnds_set = {v[1] for v in brnds_values}

        product_ids = request.env['product.template'].search(['&', ('sale_ok', '=', True), ('active', '=', True)])
        ks_min_price_avail = ks_max_price_avail = 0
        product_count = len(product_ids)
        if product_ids:
            request.cr.execute('select min(list_price),max(list_price) from product_template where id in %s',
                               (tuple(product_ids.ids),))
            min_max_vals = request.cr.fetchall()
            ks_min_price_avail = min_max_vals[0][0] or 0
            ks_max_price_avail = min_max_vals[0][1] or 1

        ks_min_selected_price = post.get('min', ks_min_price_avail)
        ks_max_selected_price = post.get('max', ks_max_price_avail)

        domain = self._get_search_domain(search, category, attrib_values, brnds_values,
                                         ks_max_selected_price=ks_max_selected_price,
                                         ks_min_selected_price=ks_min_selected_price)

        pricelist_context, pricelist = self._get_pricelist_context()

        request.context = dict(request.context, pricelist=pricelist.id, partner=request.env.user.partner_id)

        url = "/shop"
        if search:
            post["search"] = search
        if attrib_list:
            post['attrib'] = attrib_list

        Product = request.env['product.template'].with_context(bin_size=True)

        Category = request.env['product.public.category']
        search_categories = False
        search_product = Product.search(domain)
        website_domain = request.website.website_domain()
        categs_domain = [('parent_id', '=', False)] + website_domain
        if search:
            categories = search_product.mapped('public_categ_ids')
            search_categories = Category.search(
                [('product_tmpl_ids', 'in', search_product.ids)] + website_domain).parents_and_self
            categs_domain.append(('id', 'in', search_categories.ids))
            # categs = search_categories.filtered(lambda c: not c.parent_id)
        else:
            search_categories = Category
        categs = Category.search(categs_domain)

        if category:
            url = "/shop/category/%s" % slug(category)
            parent_category_ids = [category.id]
            current_category = category
            while current_category.parent_id:
                parent_category_ids.append(current_category.parent_id.id)
                current_category = current_category.parent_id
        keep = QueryURL('/shop', category=category and int(category), search=search, attrib=attrib_list,
                        brnd=brnd_list,
                        min=ks_min_selected_price, ppg=ppg, max=ks_max_selected_price, order=post.get('order'))
        if post.get('filter_remove'):
            category=None
            del(post['filter_remove'])
            keep = QueryURL('/shop', search=search, attrib=attrib_list,
                        brnd=brnd_list,
                        min=ks_min_selected_price,ppg=ppg, max=ks_max_selected_price, order=post.get('order'))
        pager = request.website.pager(url=url, total=len(search_product), page=page, step=ppg, scope=7, url_args=post)
        if post.get('offset', False):
            pager =request.website.pager(url=url, total=len(search_product) - post['offset'], page=page, step=ppg, scope=7,
                                  url_args=post)
            products = Product.search(domain, offset=post['offset'], limit=ppg,
                                      order=self._get_search_order(post))
        else:
            products = Product.search(domain, offset=pager['offset'], limit=ppg, order=self._get_search_order(post))

        product_count = len(search_product)
        ProductAttribute = request.env['product.attribute']
        if products:
            # get all products without limit
            attributes = ProductAttribute.search([('product_tmpl_ids', 'in', search_product.ids)])
        else:
            attributes = ProductAttribute.browse(attributes_ids)
        compute_currency = request.website.get_current_pricelist().currency_id
        brands = request.env["ks_product_manager.ks_brand"].search([("ks_is_published", "=", True)])
        layout_mode = ''
        if not layout_mode:
            if request.website.viewref('website_sale.products_list_view').active:
                layout_mode = 'list'
            else:
                layout_mode = 'grid'
        ks_img_url = ""
        if category is None:
            category = 0
            cat_name = ''
        else:
            cat_name = category.name
            if category.ks_categ_background:
                ks_img_url = "/web/image/product.public.category/" + str(category.id) + "/ks_categ_background"
        values = {
            'search': search,
            'category': category,
            'attrib_values': attrib_values,
            'attrib_set': attrib_set,
            'pager': pager,
            'pricelist': pricelist,
            'ks_img_url': ks_img_url,
            'add_qty': add_qty,
            'products': products,
            'search_count': product_count,  # common for all searchbox
            'bins': TableCompute().process(products, ppg, ppr),
            'ppr': ppr,
            'rows': ppr,
            'categories': categs,
            'attributes': attributes,
            'compute_currency': compute_currency,
            'keep': keep,
            # 'parent_category_ids': parent_category_ids,
            'search_categories_ids': search_categories.ids,
            'layout_mode': layout_mode,
            'min_price_selected': ks_min_selected_price,
            'max_price_selected': ks_max_selected_price,
            'min_price_set': math.floor(float(ks_min_price_avail)),
            'max_price_set': math.ceil(float(ks_max_price_avail)),
            'brands': brands,
            'brnd_set': brnds_set,
            'ppg': ppg,
            'order': post.get('order'),
            'category_name': cat_name,
            'page_count': pager['page_count'],
            'breadcumb_shop': request.env['ks_theme_kinetik.ks_breadcumb'].search([]).ks_breadcumb_image_url,
        }
        if category:
            values['main_object'] = category
        return values

    @http.route([
        '''/shop''',
        '''/shop/page/<int:page>''',
        '''/shop/category/<model("product.public.category"):category>''',
        '''/shop/category/<model("product.public.category"):category>/page/<int:page>'''
    ], type='http', auth="public", website=True, sitemap=sitemap_shop)
    def shop(self, page=0, category=None, search='', ppg=False, **post):
        if post.get('filter_clear'):
            return request.redirect('/shop')
        if post.get('filter_remove'):
            category=None
        values = self.ks_getShopValues(page, category, search, ppg, **post)
        return request.render("website_sale.products", values)

    @http.route(['/shop/load/more'], type='json', auth="public", website=True)
    def shop_load_more(self, **post):
        ks_page_offset = 24
        ppg = 24
        list_view = False
        ks_search, ks_max, ks_min, ks_category, ks_order = ("" for i in range(5))
        ks_attrib, ks_brands = ([] for i in range(2))
        ks_cate = request.env['product.public.category']
        if post.get("filters", False):
            for filter in post.get("filters"):
                if filter['name'] == 'search':
                    ks_search = filter['value']
                elif filter['name'] == 'attrib':
                    ks_attrib.append(filter['value'])
                elif filter['name'] == 'brnd':
                    ks_brands.append(filter['value'])
                elif filter['name'] == 'min':
                    ks_min = filter['value']
                elif filter['name'] == 'max':
                    ks_max = filter['value']
                elif filter['name'] == 'ppg':
                    ppg = filter['value']
                elif filter['name'] == 'category':
                    ks_category = filter['value']
                    ks_cate = ks_cate.search([('name', '=', ks_category)], limit=1)
                elif filter['name'] == 'num':
                    ks_page_offset = filter['value']
                elif filter['name'] == 'order':
                    ks_order = filter['value']
                elif filter['name'] == 'search_2':
                    if (len(ks_search)==0):
                        ks_search = filter['value']
                post.update({
                    "attrib": ks_attrib,
                    "brnd": ks_brands,
                    "offset": int(ks_page_offset)
                })
        if ks_order !='':
            post.update({
                'order':ks_order
            })
        values = self.ks_getShopValues(page=1, category=ks_cate, search=ks_search, ppg=ppg, min=ks_min,
                                    max=ks_max, **post)
        shop_products = request.env['ir.ui.view'].render_template("ks_theme_kinetik.products_infinite_loader", values)
        if request.website.viewref('website_sale.products_list_view').active:
            shop_products = request.env['ir.ui.view'].render_template("ks_theme_kinetik.products_list_view_load_more",
                                                                      values)
            list_view=True
        return ({
            "template": shop_products,
            "no_more": len(values['products']),
            'page_count':values['pager']['page_count'],
            'list_view':list_view
        })
# -*- coding: utf-8 -*-
{
    'name': "Gold Sales",
    'description': """
       Gold Sales""",
    'author': "White-Code, Abdulrahman Warda",
    'website': "http://www.white-code.co.uk",
    'URL': "https://system.white-code.co.uk/web#id=1667&action=395&model=project.task&view_type=form&menu_id=263",
    'category': 'Sales',
    'version': '13.0.0.1',
    # 'depends': ['purchase_stock', 'stock_account','account','po_gold_form','purchase_product_matrix',
    #             'purchase_order_type', 'account_accountant','stock','account_reports'],
    'depends': ['sale_stock', 'stock_account','account', 'account_accountant','stock','account_reports','sale_order_type','sale','product'],
    'data': [
        'views/res_partner_view.xml',
        'views/account_view.xml',
        'views/product_template_view.xml',
        'views/sale_order_view.xml',
        'views/stock_picking_view.xml',
        'views/stock_quant.xml',
        'wizard/fixing_unfixed_inv.xml',
        'wizard/gold_payment.xml',
        'security/ir.model.access.csv'
    ],

}

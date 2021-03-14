# -*- coding: utf-8 -*-
{
    'name': "PO Gold Form",
    'description': """
       Gold Form""",
    'author': "White-Code, Kalpesh Gajera",
    'website': "http://www.white-code.co.uk",
    'URL': "https://system.white-code.co.uk/web#id=1741&action=395&model=project.task&view_type=form&menu_id=263",
    'category': 'Purchase',
    'version': '13.0.0.1',
    'depends': ['product', 'purchase', 'gold_rate', 'purchase_order_type','currency_rate_live'],
    'data': [
        'views/product_view.xml',
        'views/purchase_order_view.xml',
    ],

}

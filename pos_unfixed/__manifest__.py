# -*- coding: utf-8 -*-

{
    'name': 'POS Unfixed Products',
    'version': '1.0',
    'category': 'Point of Sale',
    'sequence': 6,
    'author': 'White-Code, Ahmed Elmahdi',
    'summary': 'This module allows you to select unfixed products in pos .',
    'description': """

This module allows you to select unfixed products in pos

""",
    'depends': ['point_of_sale','gold_purchases'],
    'data': [
        'views/views.xml',
    ],
    'qweb': [
        'static/src/xml/pos.xml',
    ],
    'installable': True,
    'website': 'white-code.co.uk/2019/',
    'auto_install': False,
}

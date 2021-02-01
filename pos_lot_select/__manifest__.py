# -*- coding: utf-8 -*-

{
    'name': 'POS Lot/Serial Number(s)',
    'version': '1.0',
    'category': 'Point of Sale',
    'sequence': 6,
    'author': 'White-Code, Abdulrahman Warda',
    'summary': 'This module allows you to select Lot of products in pos .',
    'description': """

=======================

This module allows you to select Lot of products in pos and calculate its relation to gold cycle and its rates and making charges .

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

# -*- coding: utf-8 -*-

{
    'name': 'POS Product Validate',
    'version': '1.0',
    'category': 'Point of Sale',
    'sequence': 6,
    'author': 'White-Code, Ahmed Elmahdi',
    'description': """
""",
    'depends': ['point_of_sale'],
    'data': [
        'views/views.xml',
    ],
    'qweb': [
        'static/src/xml/pos.xml',
    ],
    'installable': True,
    'auto_install': False,
}

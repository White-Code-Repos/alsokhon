# -*- coding: utf-8 -*-

{
    'name': 'Point of Sale Order Note',
    'version': '1.0',
    'category': 'Point of Sale',
    'sequence': 6,
    'author': 'White-Code, Ahmed Elmahdi',
    'summary': 'Allows you to add note in order and orderline. Also provide product base shortcut notes.',
    'description': "Allows you to add note in order and orderline. Also provide product base shortcut notes.",
    'depends': ['point_of_sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'qweb': [
        'static/src/xml/pos.xml',
    ],

    'installable': True,
    'website': 'white-code.co.uk/2019/',
    'auto_install': False,

}

# -*- coding: utf-8 -*-
{
    'name': 'POS Check Payment',
    'summary': """Allow users to pay by check and to record details about the check paid
 directly from the user interface""",
    'category': 'Point Of Sale',
    'license': 'LGPL-3',
    'author': "White-Code, Ahmed Elmahdi",
    'website': 'white-code.co.uk/2019/',
    'depends': ['point_of_sale'],
    'data': [
        'views/pos_check.xml',
        'views/pos_order_view.xml',
    ],

    'installable': True,
    'application': True,
    'qweb': ['static/src/xml/pos_check.xml'],
}

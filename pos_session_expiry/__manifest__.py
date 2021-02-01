# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring, manifest-version-format
# pylint: disable=manifest-required-author
{
    'name': 'POS Session Expiry',
    'summary': 'POS Close Session Expiry',
    'author': "White-Code, Hashem ALy",
    'website': "http://www.white-code.co.uk",
    'category': 'Sales/Point Of Sale',
    'version': '13.0.0.1.0',
    'license': 'AGPL-3',
    'depends': [
        'point_of_sale',
    ],
    'data': [
        'views/point_of_sale_assets.xml',
        'views/pos_config_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}

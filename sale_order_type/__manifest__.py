# Copyright 2015 Camptocamp SA
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

{
    'name': 'Sale Order Type',
    'version': '13.0.0.1',
    'author': "White-Code, Abdulrahman Warda",
    'website': "http://www.white-code.co.uk",
    'category': 'Sale Management',
    'depends': [
        'sale',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/view_sale_order_type.xml',
        'views/view_sale_order.xml',
        'views/res_partner_view.xml',
        'data/sale_order_type.xml',
    ],
    'installable': True,
    'auto_install': False,
}

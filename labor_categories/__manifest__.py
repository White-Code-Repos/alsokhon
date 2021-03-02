# -*- coding: utf-8 -*-
{
    'name': "Working Calendar Change",

    'summary': """
        Working Calendar Change Request""",

    'description': """
        Employee can request to change Working Hours and manager Approve or reject
    """,

    'author': "Zienab Abd EL Nasser",
    'website': "",

    'category': 'Uncategorized',
    'version': '0.1',
    'depends':['hr','resource'],
    'data': [
        'security/ir.model.access.csv',
        # 'views/purchase_config.xml',
        'views/purchase_order_view.xml',
        'views/vendor_bill_view.xml',

    ],
}

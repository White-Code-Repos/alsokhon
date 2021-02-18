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
        'views/calendar_change_view.xml',

    ],
    # 'images': ['static/description/banner.png'],
}

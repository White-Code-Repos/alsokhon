# -*- coding: utf-8 -*-
{
    'name': 'POS Invoice Report',

    'version': '1.0',

    'category': 'Point Of Sale',

    'description': """ This app allow you to print pos invoice instead of normal recepit""",

    'author': 'White-Code, Abdulrahman Warda',

    'depends': ['point_of_sale', 'base'],
    'qweb': ['static/src/xml/pos.xml'],

    'website': 'white-code.co.uk/2019/',

    'data': [
        # 'data/mail_data.xml',
        'report/pos_report_templates.xml' ,
        'report/pos_report.xml',
        'view/assets.xml',

        ],
}

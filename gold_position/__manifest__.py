# pylint: disable=missing-docstring, manifest-required-author
{
    'name': "Gold Position Reports",
    'summary': "Gold Position Reports",
    'author': "Hashem Aly",
    'category': 'account',
    'version': '13.0.0.1.0',
    'license': 'AGPL-3',
    'depends': [
        'web',
        'gold_capital',
        'gold_purchases',
        'account_reports',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/gold_position.xml',
        'wizard/gold_position_fix_wizard_view.xml',
        'views/gold_position.xml',
        'views/gold_fixing_position_view.xml',
        # 'reports/report_view.xml',
        'views/gold_fixing_template.xml',
        'wizard/button_get_data_wiz_view.xml',
    ],
    'qweb': [
        "static/src/xml/new_button.xml",
        "static/src/xml/new_button_2.xml",
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
}

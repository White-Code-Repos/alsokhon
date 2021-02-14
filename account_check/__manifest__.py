# -*- coding: utf-8 -*-
{
    'name': 'Account Check Management',
    'version': '1.0',
    'category': 'Accounting',
    'summary': 'Accounting, Payment, Check, Third, Issue',
    'author': 'OpenERP Team de Localizacion Argentina',
    'license': 'AGPL-3',
    'images': [
    ],
    'depends': [
        'account', 'gold_purchases'
        # for bank and cash menu and also for better usability
        # 'account_payment_fix',
    ],
    'data': [
        # data
        'data/account_payment_method_data.xml',
        'data/sequence.xml',

        # security
        'security/ir.model.access.csv',
        'security/account_check_security.xml',

        # wizard
        'wizard/account_check_action_wizard_view.xml',
        'wizard/check_action_view_changes.xml',
        'wizard/account_sell_check_view.xml',
        'wizard/action_hand_view.xml',
        'wizard/transfer_to_treasury_wizard_view.xml',
        'wizard/check_action_return_trea_view.xml',

        # views
        'views/account_payment_view.xml',
        'views/account_check_view.xml',
        'views/account_journal_dashboard_view.xml',
        'views/account_journal_view.xml',
        'views/account_checkbook_view.xml',
        'views/account_move_view.xml',
        # 'views/res_company_view.xml',
        'views/account_chart_template_view.xml',
        'views/check_portfolio.xml',

    ],
    'demo': [
    ],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
    'application': True,
}

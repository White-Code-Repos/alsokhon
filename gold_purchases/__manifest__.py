# -*- coding: utf-8 -*-
{
    'name': "Gold Purchases",
    'description': """
       Gold Purchases""",
    'author': "White-Code, Kalpesh Gajera",
    'website': "http://www.white-code.co.uk",
    'URL': "https://system.white-code.co.uk/web#id=1667&action=395&model=project.task&view_type=form&menu_id=263",
    'category': 'Purchase',
    'version': '13.0.0.1',
    'depends': ['purchase_stock', 'stock_account','account','po_gold_form','purchase_product_matrix',
                'purchase_order_type', 'account_accountant','stock','account_reports'],
    'data': [
        'security/ir.model.access.csv',
        'data/gold_purity_data.xml',
        'data/account_journal_data.xml',
        'views/res_partner_view.xml',
        'wizard/gold_payment_view.xml',
        'views/account_view.xml',
        'views/product_product_view.xml',
        'views/product_template_view.xml',
        'views/stock_move_view.xml',
        'views/stock_production_lot_view.xml',
        'views/purchase_order_view.xml',
        'views/stock_picking_view.xml',
        'views/gold_purity_view.xml',
        'views/stock_quant.xml',
        'wizard/fixing_unfixed_bill.xml',
        # 'reports/gold_fixing_register.xml',
    ],

}

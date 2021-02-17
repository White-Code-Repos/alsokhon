# -*- coding: utf-8 -*-
from odoo import fields, models, api

class PosOrder(models.Model):
    _inherit = "pos.order"

    def _payment_fields(self, order, ui_paymentline):
        res = super(PosOrder, self)._payment_fields(order, ui_paymentline)

        print("((res))")
        print(res)
        print(ui_paymentline)
        res.update({
            'check_bank_id': ui_paymentline.get('check_bank_id'),
            # 'check_bank_acc': ui_paymentline.get('check_bank_acc'),
            'check_number': ui_paymentline.get('check_number'),
            'check_owner': ui_paymentline.get('check_owner'),
            'check_payment_date': ui_paymentline.get('check_payment_date'),
            'check_issue_date': ui_paymentline.get('check_issue_date')
        })
        print(res)
        return res

    def add_payment(self, data):
        statement_id = super(PosOrder, self).add_payment(data)
        print("QWEWQEQWDsfsafdsgdfg")
        print(statement_id)
        print(data)
        # StatementLine = self.env['account.bank.statement.line']
        # statement_lines = StatementLine.search([
        #     ('statement_id', '=', statement_id),
        #     ('pos_statement_id', '=', self.id),
        #     ('journal_id', '=', data['journal']),
        #     ('amount', '=', data['amount'])
        # ])
        print("WJDJQWHL")
        # for line in statement_lines:
        #     if line.journal_id.check_info_required and not line.check_bank_id:
        #         check_bank_id = data.get('check_bank_id')
        #         if isinstance(check_bank_id, (tuple, list)):
        #             check_bank_id = check_bank_id[0]
        #
        #         check_vals = {
        #             'check_bank_id': check_bank_id,
        #             'check_bank_acc': data.get('check_bank_acc'),
        #             'check_number': data.get('check_number'),
        #             'check_owner': data.get('check_owner')
        #         }
        #         line.write(check_vals)
        #         break

        return statement_id

class pos_payment_method(models.Model):
    _inherit = 'pos.payment.method'

    is_check = fields.Boolean(string="Check", default=False)

class pos_payment(models.Model):
    _inherit = 'pos.payment'

    check_number = fields.Char('Check Number',readonly=True,copy=False)
    check_bank_id = fields.Many2one('res.bank','Check Bank',readonly=True,copy=False)
    check_owner = fields.Char('Check Owner',readonly=True,copy=False)
    check_payment_date = fields.Date('Check Payment Date',readonly=True,copy=False)
    check_issue_date = fields.Date('Check Issue Date',readonly=True,copy=False)

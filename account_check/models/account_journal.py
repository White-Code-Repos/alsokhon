# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    checkbook_ids = fields.One2many(
        comodel_name='account.checkbook',
        inverse_name='journal_id',
        string='Checkbooks',
    )

    # 3 fields for Check accounts that have been moved from company..
    deferred_check_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Notes Payable Account',
        help='Deferred Checks account, for eg. "Deferred Checks"',
    )

    holding_check_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Notes Receivable Account',
        help='Holding Checks account for third checks, '
             'for eg. "Holding Checks"',
    )

    under_collection_check_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Checks Under Collection'
    )

    payment_received_bool = fields.Boolean()
    payment_issued_bool = fields.Boolean()

    @api.onchange('inbound_payment_method_ids', 'outbound_payment_method_ids')
    def onchange_payment(self):
        for pay in self.inbound_payment_method_ids:
            if pay.code in self.inbound_payment_method_ids.mapped('code'):
                if pay.code == 'received_third_check' and 'manual' in self.outbound_payment_method_ids.mapped('code') \
                        and not 'issue_check' in self.outbound_payment_method_ids.mapped('code'):
                    self.payment_received_bool = True
                    self.payment_issued_bool = False
                elif pay.code == 'received_third_check' and 'issue_check' in self.outbound_payment_method_ids.mapped(
                        'code'):
                    self.payment_received_bool = True
                    self.payment_issued_bool = True
                elif 'issue_check' in self.outbound_payment_method_ids.mapped(
                        'code') and pay.code == 'manual' and 'received_third_check' \
                        not in self.inbound_payment_method_ids.mapped('code'):
                    self.payment_received_bool = False
                    self.payment_issued_bool = True

    def _get_check_account(self, type):
        self.ensure_one()
        if type == 'holding':
            account = self.holding_check_account_id
        elif type == 'rejected':
            account = self.rejected_check_account_id
        elif type == 'deferred':
            account = self.deferred_check_account_id
        else:
            raise UserError(_("Type %s not implemented!"))
        if not account:
            raise UserError(_(
                'No checks %s account defined for Journal %s'
            ) % (type, self.name))
        return account

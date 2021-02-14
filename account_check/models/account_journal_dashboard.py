# -*- coding: utf-8 -*-
from ast import literal_eval

from odoo import models
from odoo.tools.misc import formatLang


class AccountJournal(models.Model):
    _inherit = "account.journal"

    def get_journal_dashboard_datas(self):
        domain_holding_third_checks = [
            ('type', '=', 'third_check'),
            ('journal_id', '=', self.id),
            ('state', '=', 'holding')
        ]
        domain_handed_issue_checks = [
            ('type', '=', 'issue_check'),
            ('journal_id', '=', self.id),
            ('state', '=', 'handed')
        ]
        handed_checks = self.env['account.check'].search(
            domain_handed_issue_checks)
        holding_checks = self.env['account.check'].search(
            domain_holding_third_checks)
        return dict(
            super(AccountJournal, self).get_journal_dashboard_datas(),
            num_holding_third_checks=len(holding_checks),
            show_third_checks=(
                    'received_third_check' in
                    self.inbound_payment_method_ids.mapped('code')),
            show_issue_checks=(
                    'issue_check' in
                    self.outbound_payment_method_ids.mapped('code')),
            num_handed_issue_checks=len(handed_checks),
            handed_amount=formatLang(
                self.env, sum(handed_checks.mapped('amount')),
                currency_obj=self.currency_id or self.company_id.currency_id),
            holding_amount=formatLang(
                self.env, sum(holding_checks.mapped('amount')),
                currency_obj=self.currency_id or self.company_id.currency_id),
        )

    def open_action_checks(self):
        check_type = self.env.context.get('check_type', False)
        if check_type == 'third_check':
            action_name = 'account_check.action_collected_check'
            state = 'holding'
        elif check_type == 'issue_check':
            action_name = 'account_check.action_issued_check'
            state = 'handed'
        else:
            return False
        actions = self.env.ref(action_name)
        action_read = actions.read()[0]
        context = {'search_default_journal_id': self.id,
                   'search_default_state': state,
                   'default_type': check_type}
        action_read['context'] = context
        return action_read

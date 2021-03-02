# -*- coding: utf-8 -*-
import logging

from odoo import fields, models, _, api
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountPayment(models.Model):
    _inherit = 'account.payment'
    check_ids = fields.Many2many(comodel_name="account.check", relation="payment_id", string="Checks",
                                 states={'draft': [('readonly', '=', False)]})

    # only for v8 comatibility where more than one check could be received
    # or issued
    check_ids_copy = fields.Many2many(
        related='check_ids',
        readonly=True,
    )
    readonly_currency_id = fields.Many2one(
        related='currency_id',
        readonly=True,
    )
    readonly_amount = fields.Monetary(
        related='amount',
        readonly=True,
    )
    # we add this field for better usability on issue checks and received
    # checks. We keep m2m field for backward compatibility where we allow to
    # use more than one check per payment
    check_id = fields.Many2one(
        'account.check',
        compute='_compute_check',
        string='Check',
    )

    # Add by omnya 07/07/2020
    treasury_journal_id = fields.Many2one(comodel_name='account.journal', string='Treasury')

    @api.depends('check_ids')
    def _compute_check(self):
        for rec in self:
            # we only show checks for issue checks or received thid checks
            # if len of checks is 1
            if rec.payment_method_code in (
                    'received_third_check',
                    'issue_check',) and len(rec.check_ids) == 1:
                rec.check_id = rec.check_ids[0].id
            else:
                rec.check_id = False

    # check fields, just to make it easy to load checks without need to create
    # them by a m2o record
    check_name = fields.Char(
        'Check Name',
        readonly=True,
        copy=False,
        states={'draft': [('readonly', False)]},
    )
    check_number = fields.Char(
        'Check Number',
        readonly=True,
        states={'draft': [('readonly', False)]},
        copy=False
    )
    check_number_id = fields.Many2one(comodel_name='checkbook.sequence', string='Check Number', required=False,
                                      states={'draft': [('readonly', False)]})
    check_issue_date = fields.Date(
        'Check Issue Date',
        readonly=True,
        copy=False,
        states={'draft': [('readonly', False)]},
        default=fields.Date.context_today,
    )
    check_payment_date = fields.Date(
        'Check Payment Date',
        readonly=True,
        help="Only if this check is post dated",
        states={'draft': [('readonly', False)]}
    )
    checkbook_id = fields.Many2one(
        'account.checkbook',
        'Checkbook',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    check_subtype = fields.Selection(
        related='checkbook_id.issue_check_subtype',
        readonly=True,
    )
    check_bank_id = fields.Many2one(
        'res.bank',
        'Check Bank',
        readonly=True,
        copy=False,
        states={'draft': [('readonly', False)]}
    )
    # check_owner_vat = fields.Char(
    #     'Check Owner Vat',
    #     readonly=True,
    #     copy=False,
    #     states={'draft': [('readonly', False)]}
    # )
    check_owner_name = fields.Char(
        'Check Owner Name',
        readonly=True,
        copy=False,
        states={'draft': [('readonly', False)]}
    )
    # this fields is to help with code and view
    check_type = fields.Char(
        compute='_compute_check_type',
    )
    checkbook_block_manual_number = fields.Boolean(
        related='checkbook_id.block_manual_number',
    )
    '''check_number_readonly = fields.Integer(
        related='check_number',
        readonly=True,
    )'''

    check_count = fields.Integer(compute='compute_count')

    def compute_count(self):
        for record in self:
            record.check_count = self.env['account.check'].search_count(
                [('payment_id', '=', self.id)])

    def get_checks(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Checks',
            'view_mode': 'tree,form',
            'res_model': 'account.check',
            'domain': [('payment_id', '=', self.id)],
            'context': "{'create': False}"
        }

    @api.depends('payment_method_code')
    def _compute_check_type(self):
        for rec in self:
            if rec.payment_method_code:
                if rec.payment_method_code == 'issue_check':
                    rec.check_type = 'issue_check'
                elif rec.payment_method_code in ['received_third_check', 'delivered_third_check']:
                    rec.check_type = 'third_check'
                else:
                    rec.check_type = ''
            else:
                rec.check_type = ''

    # @api.constrains('check_ids')
    @api.onchange('check_ids', 'payment_method_code')
    def onchange_checks(self):
        # we only overwrite if payment method is delivered
        if self.payment_method_code == 'delivered_third_check':
            self.amount = sum(self.check_ids.mapped('amount'))

    # # TODo activar
    @api.model
    @api.onchange('check_number')
    def change_check_number(self):
        # TODO make default padding a parameter
        if self.payment_method_code in ['received_third_check']:
            if not self.check_number:
                check_name = False
            else:
                # TODO make optional
                padding = 8
                if len(str(self.check_number)) > padding:
                    padding = len(str(self.check_number))
                check_name = ('%%0%sd' % padding % int(self.check_number))
            self.check_name = check_name

    @api.onchange('checkbook_id')
    def onchange_checkbook_id(self):
        if self.checkbook_id:
            return {'domain': {'check_number_id': [('checkbook_sequence', '=', self.checkbook_id.id),
                                                   ('state', '=', 'draft')]}}

    # @api.model
    # def create(self, vals):
    #     res= super(AccountPayment, self).create(vals)
    #     check_name = False
    #     if res.checkbook_id:
    #         if not self.check_number:
    #             check = self.env['account.checkbook'].search([('id', '=', res.checkbook_id.id)])
    #             sequence = check.sequence_id
    #             if res.check_number != sequence.number_next_actual:
    #                 sequence.write({'number_next_actual': check.next_number})
    #             if sequence.number_next_actual > check.range_to:
    #                 raise UserError(_(
    #                     "Check number (%s) can't be greater than %s on "
    #                     "checkbook %s (%s)") % (check.next_number, check.range_to,
    #                                             check.name, check.id))
    #             check_name = check.sequence_id.next_by_id()
    #             res.check_number = check_name
    #         res.check_name = check_name
    #     return res

    @api.onchange('check_issue_date', 'check_payment_date')
    def onchange_date(self):
        if (
                self.check_issue_date and self.check_payment_date and
                self.check_issue_date > self.check_payment_date):
            self.check_payment_date = False
            raise UserError(
                _('Check Payment Date must be greater than Issue Date'))

    @api.model
    @api.onchange('partner_id')
    def onchange_partner_check(self):
        commercial_partner = self.partner_id.commercial_partner_id
        self.check_bank_id = (
                commercial_partner.bank_ids and
                commercial_partner.bank_ids[0].bank_id.id or False)
        self.check_owner_name = commercial_partner.name
        # TODO use document number instead of vat?
        # self.check_owner_vat = commercial_partner.vat

    @api.onchange('payment_method_code')
    def _onchange_payment_method_code(self):
        if self.payment_method_code == 'issue_check':
            checkbook = self.env['account.checkbook'].search([
                ('state', '=', 'active'),
                ('journal_id', '=', self.journal_id.id)],
                limit=1)
            self.checkbook_id = checkbook
        elif self.checkbook_id:
            self.checkbook_id = False

    def cancel(self):
        res = super(AccountPayment, self).cancel()
        for rec in self:
            # rec.do_checks_operations(cancel=True) # need to be reviewed..
            rec.checkbook_id.sequence_id.number_next_actual -= 1
            checks = self.env['account.check'].search([('payment_id', '=', rec.id)])
            checks.filtered(lambda check: check.state != 'draft').cancel_action()
            checkbooks_sequence = self.env['checkbook.sequence'].search([('name', '=', rec.check_number_id.name)])
            checkbooks_sequence.write({'state': 'cancel'})
        return res

    def create_check(self, check_type, operation, bank):
        self.ensure_one()
        if self.payment_method_code == 'received_third_check':
            check_number = self.check_number
        else:
            check_number = self.check_number_id.name
        check_vals = {
            'bank_id': self.check_bank_id.id,
            'partner_id': self.partner_id.id,
            'owner_name': self.check_owner_name,
            # 'owner_vat': self.check_owner_vat,
            'number': check_number or self.communication,
            'name': check_number or self.communication,
            'checkbook_id': self.checkbook_id.id,
            'issue_date': self.check_issue_date,
            'type': self.check_type,
            'journal_id': self.journal_id.id,
            'treasury_journal_id': self.treasury_journal_id.id,
            'amount': self.amount,
            'payment_date': self.check_payment_date,
            'currency_id': self.currency_id.id,
            'payment_id': self.id
        }
        check = self.env['account.check'].create(check_vals)
        self.check_ids = [(4, check.id, False)]
        check._add_operation(
            operation, self, self.partner_id, date=self.payment_date)
        return check

    # # override default method
    # def action_draft(self):
    #     res = super(AccountPayment, self).action_draft()
    #     # checks = self.env['account.check'].search([('payment_id', '=', self.id)])
    #     # checks.filtered(lambda check: check.state != 'draft').button_draft()
    #     # checks.with_context(force_delete=True).unlink()
    #     return res

    # override default method
    def _prepare_payment_moves(self):
        all_move_vals = []
        for payment in self:
            company_currency = payment.company_id.currency_id
            move_names = payment.move_name.split(
                payment._get_move_name_transfer_separator()) if payment.move_name else None

            # Compute amounts.
            write_off_amount = payment.payment_difference_handling == 'reconcile' and -payment.payment_difference or 0.0
            if payment.payment_type in ('outbound', 'transfer'):
                counterpart_amount = payment.amount
                if payment.payment_method_code == 'issue_check':
                    liquidity_line_account = payment.journal_id.deferred_check_account_id
                else:
                    liquidity_line_account = payment.journal_id.default_debit_account_id
            else:
                counterpart_amount = -payment.amount
                if payment.payment_method_code == 'received_third_check':
                    liquidity_line_account = payment.journal_id.holding_check_account_id
                else:
                    liquidity_line_account = payment.journal_id.default_credit_account_id

            # Manage currency.
            if payment.currency_id == company_currency:
                # Single-currency.
                balance = counterpart_amount
                write_off_balance = write_off_amount
                counterpart_amount = write_off_amount = 0.0
                currency_id = False
            else:
                # Multi-currencies.
                balance = payment.currency_id._convert(counterpart_amount, company_currency, payment.company_id,
                                                       payment.payment_date)
                write_off_balance = payment.currency_id._convert(write_off_amount, company_currency, payment.company_id,
                                                                 payment.payment_date)
                currency_id = payment.currency_id.id

            # Manage custom currency on journal for liquidity line.
            if payment.journal_id.currency_id and payment.currency_id != payment.journal_id.currency_id:
                # Custom currency on journal.
                if payment.journal_id.currency_id == company_currency:
                    # Single-currency
                    liquidity_line_currency_id = False
                else:
                    liquidity_line_currency_id = payment.journal_id.currency_id.id
                liquidity_amount = company_currency._convert(
                    balance, payment.journal_id.currency_id, payment.company_id, payment.payment_date)
            else:
                # Use the payment currency.
                liquidity_line_currency_id = currency_id
                liquidity_amount = counterpart_amount

            # Compute 'name' to be used in receivable/payable line.
            rec_pay_line_name = ''
            if payment.payment_type == 'transfer':
                rec_pay_line_name = payment.name
            else:
                if payment.partner_type == 'customer':
                    if payment.payment_type == 'inbound':
                        rec_pay_line_name += _("Customer Payment")
                    elif payment.payment_type == 'outbound':
                        rec_pay_line_name += _("Customer Credit Note")
                elif payment.partner_type == 'supplier':
                    if payment.payment_type == 'inbound':
                        rec_pay_line_name += _("Vendor Credit Note")
                    elif payment.payment_type == 'outbound':
                        rec_pay_line_name += _("Vendor Payment")
                if payment.invoice_ids:
                    rec_pay_line_name += ': %s' % ', '.join(payment.invoice_ids.mapped('name'))

            # Compute 'name' to be used in liquidity line.
            if payment.payment_type == 'transfer':
                liquidity_line_name = _('Transfer to %s') % payment.destination_journal_id.name
            else:
                liquidity_line_name = payment.name

            # ==== 'inbound' / 'outbound' ====
            move_vals = {
                'date': payment.payment_date,
                'ref': payment.communication,
                'journal_id': payment.journal_id.id,
                'currency_id': payment.journal_id.currency_id.id or payment.company_id.currency_id.id,
                'partner_id': payment.partner_id.id,
                'line_ids': [
                    # Receivable / Payable / Transfer line.
                    (0, 0, {
                        'name': rec_pay_line_name,
                        'amount_currency': counterpart_amount + write_off_amount if currency_id else 0.0,
                        'currency_id': currency_id,
                        'debit': balance + write_off_balance > 0.0 and balance + write_off_balance or 0.0,
                        'credit': balance + write_off_balance < 0.0 and -balance - write_off_balance or 0.0,
                        'date_maturity': payment.payment_date,
                        'partner_id': payment.partner_id.commercial_partner_id.id,
                        'account_id': payment.destination_account_id.id,
                        'payment_id': payment.id,
                    }),
                    # Liquidity line.
                    (0, 0, {
                        'name': liquidity_line_name,
                        'amount_currency': -liquidity_amount if liquidity_line_currency_id else 0.0,
                        'currency_id': liquidity_line_currency_id,
                        'debit': balance < 0.0 and -balance or 0.0,
                        'credit': balance > 0.0 and balance or 0.0,
                        'date_maturity': payment.payment_date,
                        'partner_id': payment.partner_id.commercial_partner_id.id,
                        'account_id': liquidity_line_account.id,
                        'payment_id': payment.id,
                    }),
                ],
            }
            if write_off_balance:
                # Write-off line.
                move_vals['line_ids'].append((0, 0, {
                    'name': payment.writeoff_label,
                    'amount_currency': -write_off_amount,
                    'currency_id': currency_id,
                    'debit': write_off_balance < 0.0 and -write_off_balance or 0.0,
                    'credit': write_off_balance > 0.0 and write_off_balance or 0.0,
                    'date_maturity': payment.payment_date,
                    'partner_id': payment.partner_id.commercial_partner_id.id,
                    'account_id': payment.writeoff_account_id.id,
                    'payment_id': payment.id,
                }))

            if move_names:
                move_vals['name'] = move_names[0]

            all_move_vals.append(move_vals)

            # ==== 'transfer' ====
            if payment.payment_type == 'transfer':
                journal = payment.destination_journal_id

                # Manage custom currency on journal for liquidity line.
                if journal.currency_id and payment.currency_id != journal.currency_id:
                    # Custom currency on journal.
                    liquidity_line_currency_id = journal.currency_id.id
                    transfer_amount = company_currency._convert(balance, journal.currency_id, payment.company_id,
                                                                payment.payment_date)
                else:
                    # Use the payment currency.
                    liquidity_line_currency_id = currency_id
                    transfer_amount = counterpart_amount

                transfer_move_vals = {
                    'date': payment.payment_date,
                    'ref': payment.communication,
                    'partner_id': payment.partner_id.id,
                    'journal_id': payment.destination_journal_id.id,
                    'line_ids': [
                        # Transfer debit line.
                        (0, 0, {
                            'name': payment.name,
                            'amount_currency': -counterpart_amount if currency_id else 0.0,
                            'currency_id': currency_id,
                            'debit': balance < 0.0 and -balance or 0.0,
                            'credit': balance > 0.0 and balance or 0.0,
                            'date_maturity': payment.payment_date,
                            'partner_id': payment.partner_id.commercial_partner_id.id,
                            'account_id': payment.company_id.transfer_account_id.id,
                            'payment_id': payment.id,
                        }),
                        # Liquidity credit line.
                        (0, 0, {
                            'name': _('Transfer from %s') % payment.journal_id.name,
                            'amount_currency': transfer_amount if liquidity_line_currency_id else 0.0,
                            'currency_id': liquidity_line_currency_id,
                            'debit': balance > 0.0 and balance or 0.0,
                            'credit': balance < 0.0 and -balance or 0.0,
                            'date_maturity': payment.payment_date,
                            'partner_id': payment.partner_id.commercial_partner_id.id,
                            'account_id': payment.destination_journal_id.default_credit_account_id.id,
                            'payment_id': payment.id,
                        }),
                    ],
                }

                if move_names and len(move_names) == 2:
                    transfer_move_vals['name'] = move_names[1]

                all_move_vals.append(transfer_move_vals)
        return all_move_vals

    def post(self):
        res = super(AccountPayment, self).post()
        if self.payment_method_code == 'received_third_check':
            self.create_check('third_check', 'holding', self.check_bank_id)
        elif self.payment_method_code == 'issue_check':
            check = self.create_check('issue_check', 'handed', self.check_bank_id)
            checkbooks_sequence = self.env['checkbook.sequence'].search([('name', '=', check.number)])
            checkbooks_sequence.write({'state': 'issued'})
        return res

    def get_third_check_account(self):
        """
        For third checks, if we use a journal only for third checks, we use
        accounts on journal, if not we use company account
        """
        self.ensure_one()
        if self.payment_type in ('outbound', 'transfer'):
            account = self.journal_id.default_debit_account_id
            methods_field = 'outbound_payment_method_ids'
        else:
            account = self.journal_id.default_credit_account_id
            methods_field = 'inbound_payment_method_ids'
        if len(self.journal_id[methods_field]) > 1 or not account:
            account = self.journal_id._get_check_account('holding')
        return account

    def do_checks_operations(self, vals=None, cancel=False):
        """
        Check attached .ods file on this module to understand checks workflows
        This method is called from:
        * cancellation of payment to execute delete the right operation and
            unlink check if needed
        * from _get_liquidity_move_line_vals to add check operation and, if
            needded, change payment vals and/or create check and
        TODO si queremos todos los del operation podriamos moverlos afuera y
        simplificarlo ya que es el mismo en casi todos
        Tambien podemos simplficiar las distintas opciones y como se recorren
        los if
        """
        self.ensure_one()
        rec = self
        if not rec.check_type:
            # continue
            return vals
        if (
                rec.payment_method_code == 'received_third_check' and
                rec.payment_type == 'inbound'
                # and rec.partner_type == 'customer'
        ):
            operation = 'holding'
            if cancel:
                _logger.info('Cancel Receive Check')
                rec.check_ids._del_operation(self)
                rec.check_ids.unlink()
                return None

            _logger.info('Receive Check')
            self.create_check('third_check', operation, self.check_bank_id)
            vals['date_maturity'] = self.check_payment_date
            vals['account_id'] = self.get_third_check_account().id
        elif (
                rec.payment_method_code == 'delivered_third_check' and
                rec.payment_type == 'transfer'):

            # TODO we should make this method selectable for transfers
            inbound_method = (
                rec.destination_journal_id.inbound_payment_method_ids)
            if len(inbound_method) == 1 and (
                    inbound_method.code == 'received_third_check'):
                if cancel:
                    _logger.info('Cancel Transfer Check')
                    for check in rec.check_ids:
                        check._del_operation(self)
                        check._del_operation(self)
                        receive_op = check._get_operation('holding')
                        if receive_op.origin._name == 'account.payment':
                            check.journal_id = receive_op.origin.journal_id.id
                    return None

                _logger.info('Transfer Check')
                rec.check_ids._add_operation(
                    'transfered', rec, False, date=rec.payment_date)
                rec.check_ids._add_operation(
                    'holding', rec, False, date=rec.payment_date)
                rec.check_ids.write({
                    'journal_id': rec.destination_journal_id.id})
                vals['account_id'] = self.get_third_check_account().id
            elif rec.destination_journal_id.type == 'cash':
                if cancel:
                    _logger.info('Cancel Sell Check')
                    rec.check_ids._del_operation(self)
                    return None

                _logger.info('Sell Check')
                rec.check_ids._add_operation(
                    'selled', rec, False, date=rec.payment_date)
                vals['account_id'] = self.get_third_check_account().id
            else:
                if cancel:
                    _logger.info('Cancel Deposit Check')
                    rec.check_ids._del_operation(self)
                    return None

                _logger.info('Deposit Check')
                rec.check_ids._add_operation(
                    'deposited', rec, False, date=rec.payment_date)
                vals['account_id'] = self.get_third_check_account().id
        elif (
                rec.payment_method_code == 'delivered_third_check' and
                rec.payment_type == 'outbound'
                # and rec.partner_type == 'supplier'
        ):
            if cancel:
                _logger.info('Cancel Deliver Check')
                rec.check_ids._del_operation(self)
                return None

            _logger.info('Deliver Check')
            rec.check_ids._add_operation(
                'delivered', rec, rec.partner_id, date=rec.payment_date)
            vals['account_id'] = self.get_third_check_account().id
        elif (
                rec.payment_method_code == 'issue_check' and
                rec.payment_type == 'outbound'
                # and rec.partner_type == 'supplier'
        ):
            if cancel:
                _logger.info('Cancel Hand Check')
                rec.check_ids._del_operation(self)
                rec.check_ids.unlink()
                return None

            _logger.info('Hand Check')
            self.create_check('issue_check', 'handed', self.check_bank_id)
            vals['date_maturity'] = self.check_payment_date
            # if check is deferred, change account
            if self.check_subtype == 'deferred':
                vals['account_id'] = self.journal_id._get_check_account(
                    'deferred').id
        elif (
                rec.payment_method_code == 'issue_check' and
                rec.payment_type == 'transfer' and
                rec.destination_journal_id.type == 'cash'):
            if cancel:
                _logger.info('Cancel Withdrawal Check')
                rec.check_ids._del_operation(self)
                rec.check_ids.unlink()
                return None

            _logger.info('Hand Check')
            self.create_check('issue_check', 'withdrawed', self.check_bank_id)
            vals['date_maturity'] = self.check_payment_date
            # if check is deferred, change account
            # if self.check_subtype == 'deferred':
            #     vals['account_id'] = self.company_id._get_check_account(
            #         'deferred').id
        else:
            raise UserError(_(
                'This operatios is not implemented for checks:\n'
                '* Payment type: %s\n'
                '* Partner type: %s\n'
                '* Payment method: %s\n'
                '* Destination journal: %s\n' % (
                    rec.payment_type,
                    rec.partner_type,
                    rec.payment_method_code,
                    rec.destination_journal_id.type)))
        return vals

    def _get_liquidity_move_line_vals(self, amount):
        vals = super(AccountPayment, self)._get_liquidity_move_line_vals(
            amount)
        vals = self.do_checks_operations(vals=vals)
        return vals

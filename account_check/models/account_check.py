# -*- coding: utf-8 -*-
import logging

from odoo import fields, models, _, api
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class AccountCheckOperation(models.Model):
    _name = 'account.check.operation'
    _rec_name = 'operation'
    _order = 'date desc, id desc'

    date = fields.Date(
        default=fields.Date.context_today,
        required=True,
    )

    # Relational field
    check_id = fields.Many2one(
        'account.check',
        'Check',
        required=True,
        ondelete='cascade',
        auto_join=True,
    )
    operation = fields.Selection([
        # from payments
        ('holding', 'Receive'),
        ('deposited', 'Deposit'),
        ('selled', 'Sell'),
        ('delivered', 'Deliver'),
        ('transfered', 'Transfer'),
        ('handed', 'Hand'),
        ('withdrawed', 'Withdrawal'),
        # from checks
        ('reclaimed', 'Claim'),
        ('rejected', 'Rejection'),
        ('debited', 'Debit'),
        ('credited', 'Credited'),
        ('inbank', 'Inbank'),
        ('returned', 'Return'),
        ('changed', 'Change'),
        ('cancel', 'Cancel'),
    ], required=True,
    )
    origin_name = fields.Char(
        compute='_compute_origin_name'
    )
    origin = fields.Reference(
        string='Origin Document',
        selection='_reference_models')
    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
    )
    handed_to = fields.Many2one(
        'res.partner',
        string='Handed To', store=True
    )
    notes = fields.Text()

    def unlink(self):
        for rec in self:
            if rec.origin:
                raise ValidationError(_(
                    'You can not delete a check operation that has an origin.'
                    '\nYou can delete the origin reference and unlink after.'))
        return super(AccountCheckOperation, self).unlink()

    @api.depends('origin')
    def _compute_origin_name(self):
        """
        We add this computed method because an error on tree view displaying
        reference field when destiny record is deleted.
        As said in this post (last answer) we should use name_get instead of
        display_name
        https://www.odoo.com/es_ES/forum/ayuda-1/question/
        how-to-override-name-get-method-in-new-api-61228
        """
        for rec in self:
            try:
                if rec.origin:
                    id, name = rec.origin.name_get()[0]
                    origin_name = name
                    # origin_name = rec.origin.display_name
                else:
                    origin_name = False
            except Exception as e:
                _logger.exception(
                    "Compute origin on checks exception: %s" % e)
                # if we can get origin we clean it
                rec.write({'origin': False})
                origin_name = False
            rec.origin_name = origin_name

    @api.model
    def _reference_models(self):
        return [
            ('account.payment', 'Payment'),
            ('account.check', 'Check'),
            ('account.invoice', 'Invoice'),
            ('account.move', 'Journal Entry'),
            ('account.move.line', 'Journal Item'),
        ]


class AccountCheck(models.Model):
    _name = 'account.check'
    _description = 'Account Check'
    _order = "id desc"
    _inherit = ['mail.thread']

    operation_ids = fields.One2many(
        'account.check.operation',
        'check_id',
    )
    name = fields.Char(
        required=True,
        readonly=True,
        copy=False,
        states={'draft': [('readonly', False)]},
    )
    number = fields.Char(
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        copy=False
    )
    checkbook_id = fields.Many2one(
        'account.checkbook',
        'Checkbook',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    sequence_number_id = fields.Many2one(comodel_name='checkbook.sequence', string='Check Number',
                                         states={'draft': [('readonly', False)]})
    type = fields.Selection(
        [('issue_check', 'Issued Check'), ('third_check', 'Collected Checks')],
        readonly=True,
    )
    partner_id = fields.Many2one(comodel_name='res.partner', string="Check Partner",
                                 store=True, force_save=True, compute='get_partner_name', readonly=False)
    inbank_account_id = fields.Many2one('account.account', string='In Bank Account', readonly=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('holding', 'In Treasury'),
        ('deposited', 'Deposited'),
        ('selled', 'Sold'),
        ('delivered', 'Delivered'),
        ('transfered', 'Transfered'),
        ('reclaimed', 'Reclaimed'),
        ('withdrawed', 'Withdrawed'),
        ('handed', 'Handed'),
        ('inbank', 'Deposited in Bank'),
        ('debited', 'Debited'),
        ('credited', 'Credited'),
        ('returned', 'Returned'),
        ('changed', 'Changed'),
        ('rejected', 'Rejected'),
        ('cancel', 'Cancel'),
    ],
        required=True,
        default='draft',
        copy=False,
        compute='_compute_state',
        store=True,
        track_visibility='always',
    )

    issue_date = fields.Date(
        'Issue Date',
        required=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        default=fields.Date.context_today,
    )
    # owner_vat = fields.Char(
    #     'Owner Vat',
    #     readonly=True,
    #     states={'draft': [('readonly', False)]}
    # )
    owner_name = fields.Char(
        'Owner Name',
        readonly=True,
        states={'draft': [('readonly', False)]}
    )
    bank_id = fields.Many2one(
        'res.bank', 'Bank',
        readonly=True,
        states={'draft': [('readonly', False)]}
    )

    amount = fields.Monetary(
        currency_field='company_currency_id',
        readonly=True,
        states={'draft': [('readonly', False)]}
    )
    amount_currency = fields.Monetary(
        currency_field='currency_id',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    currency_id = fields.Many2one(
        'res.currency',
        readonly=True,
        states={'draft': [('readonly', False)]},
    )
    payment_date = fields.Date(
        readonly=True,
        states={'draft': [('readonly', False)]}
    )
    journal_id = fields.Many2one(
        'account.journal',
        string='Journal',
        required=True,
        domain=[('type', 'in', ['cash', 'bank'])],
        readonly=True,
        states={'draft': [('readonly', False)]}
    )
    company_id = fields.Many2one(
        related='journal_id.company_id',
        readonly=True,
        store=True,
    )
    company_currency_id = fields.Many2one(
        related='company_id.currency_id',
        readonly=True,
    )

    debit = fields.Boolean(compute='get_debit_credit')

    payment_id = fields.Many2one(comodel_name='account.payment', string='Payment')

    journal_entry_count = fields.Integer(compute='compute_count')

    # Add by omnya 07/07/2020
    handed_to = fields.Many2one(related='operation_ids.handed_to',
                                readonly=True, string="Handed To", store=True, force_save=True)
    treasury_journal_id = fields.Many2one(comodel_name='account.journal', string='Treasury',
                                          track_visibility='always')

    # Portfolio
    portfolio_id = fields.Many2one(comodel_name="check.portfolio", string="", required=False, )
    port_state = fields.Selection(related='portfolio_id.state')
    portfolio_count = fields.Integer(compute='compute_port_count')

    def compute_port_count(self):
        for record in self:
            record.portfolio_count = self.env['check.portfolio'].search_count(
                [('id', '=', self.portfolio_id.id)])

    def check_portfolio(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Check Portfolio'),
            'res_model': 'check.portfolio',
            'view_mode': 'tree,form',
            'domain': [('id', '=', self.portfolio_id.id)],
        }

    @api.depends('operation_ids')
    def get_partner_name(self):
        for rec in self:
            if rec.operation_ids:
                for line in rec.operation_ids:
                    rec.partner_id = line.partner_id.id
            else:
                rec.partner_id = rec.partner_id.id

    @api.onchange('sequence_number_id')
    def onchange_sequence_number_id(self):
        self.number = self.sequence_number_id.name

    @api.onchange('checkbook_id')
    def onchange_checkbook_id(self):
        if self.checkbook_id:
            return {'domain': {'sequence_number_id': [('checkbook_sequence', '=', self.checkbook_id.id),
                                                      ('state', '!=', 'cancel')]}}

    def transfer_to_treasury(self):
        action = self.env.ref('account_check.action_transfer_treasury_wizard')
        result = action.read()[0]
        res = self.env.ref('account_check.action_transfer_treasury_wizard_view', False)
        result['views'] = [(res and res.id or False, 'form')]
        result['target'] = 'new'
        result['context'] = {'default_check_id': self.id}
        return result

    def compute_count(self):
        for record in self:
            record.journal_entry_count = self.env['account.move'].search_count(
                [('move_check_id', '=', self.id)])

    def get_journals(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Journal Entries',
            'view_mode': 'tree,form',
            'res_model': 'account.move',
            'domain': [('move_check_id', '=', self.id)],
            'context': "{'create': False}"
        }

    @api.depends('type')
    def get_debit_credit(self):
        if self.type == 'third_check':
            self.debit = True
        else:
            self.debit = False

    @api.constrains('issue_date', 'payment_date')
    @api.onchange('issue_date', 'payment_date')
    def onchange_date(self):
        for rec in self:
            if (
                    rec.issue_date and rec.payment_date and
                    rec.issue_date > rec.payment_date):
                raise UserError(
                    _('Check Payment Date must be greater than Issue Date'))

    @api.constrains(
        'type',
        'owner_name',
        'bank_id',
    )
    def _check_unique(self):
        for rec in self:
            if rec.type == 'issue_check':
                same_checks = self.search([
                    ('checkbook_id', '=', rec.checkbook_id.id),
                    ('type', '=', rec.type),
                    ('number', '=', rec.number),
                ])
                same_checks -= self
                if same_checks:
                    raise ValidationError(_(
                        'Check Number (%s) must be unique per Checkbook!\n'
                        '* Check ids: %s') % (
                                              rec.name, same_checks.ids))
            elif self.type == 'third_check':
                same_checks = self.search([
                    ('bank_id', '=', rec.bank_id.id),
                    ('owner_name', '=', rec.owner_name),
                    ('type', '=', rec.type),
                    ('number', '=', rec.number),
                ])
                same_checks -= self
                if same_checks:
                    raise ValidationError(_(
                        'Check Number (%s) must be unique per Owner and Bank!'
                        '\n* Check ids: %s') % (
                                              rec.name, same_checks.ids))
        return True

    def _del_operation(self, origin):
        """
        We check that the operation that is being cancel is the last operation
        done (same as check state)
        """
        for rec in self:
            # if not rec.operation_ids or rec.operation_ids[0].origin != origin:
            #     raise ValidationError(_(
            #         'You can not cancel this operation because this is not '
            #         'the last operation over the check. Check (id): %s (%s)'
            #     ) % (rec.name, rec.id))
            rec.operation_ids[0].origin = False
            rec.operation_ids[0].unlink()

    def _add_operation(
            self, operation, origin, partner=None, date=False):
        for rec in self:
            date = date or fields.Datetime.now().date()
            # if rec.operation_ids and rec.operation_ids[0].date > date:
            #     raise ValidationError(_(
            #         'The date of a new operation can not be minor than last '
            #         'operation date'))
            vals = {
                'operation': operation,
                'date': date,
                'check_id': rec.id,
                'origin': '%s,%i' % (origin._name, origin.id),
                'partner_id': self.partner_id.id or partner and partner.id or False,
                'handed_to': self.handed_to.id or False
            }
            rec.operation_ids.create(vals)

    @api.depends(
        'operation_ids.operation',
        'operation_ids.date',
    )
    def _compute_state(self):
        for rec in self:
            if rec.operation_ids:
                for re in rec.operation_ids:
                    rec.state = re.operation
            #     operation = rec.operation_ids[0].operation
            #     rec.state = operation
            else:
                rec.state = 'draft'

    def unlink(self):
        for rec in self:
            if rec.state not in ('draft', 'cancel'):
                raise ValidationError(
                    _('The Check must be in draft state for unlink !'))
        return super(AccountCheck, self).unlink()

    # checks operations from checks
    def bank_debit(self):
        self.ensure_one()
        if self.state in ['handed']:
            vals = self.get_bank_vals(
                'bank_debit', self.journal_id)
            action_date = self._context.get('action_date')
            vals['date'] = action_date
            move = self.env['account.move'].create(vals)
            move.post()
            self._add_operation('debited', move, date=action_date)

    # add new type to operation credit
    def bank_credit(self):
        self.ensure_one()
        if self.state in ['handed'] and self.type == 'issue_check':
            vals = self.get_bank_vals(
                'bank_credit', self.journal_id)
            action_date = self._context.get('action_date')
            vals['date'] = action_date
            move = self.env['account.move'].create(vals)
            move.post()
            self._add_operation('credited', move, date=action_date)

    def claim(self):
        if self.state in ['rejected'] and self.type == 'third_check':
            operation = self._get_operation('holding', True)
            return self.action_create_debit_note(
                'reclaimed', 'customer', operation.partner_id)

    @api.model
    def _get_checks_to_date_on_state(self, state, date, force_domain=None):
        if not force_domain:
            force_domain = []
        operations = self.operation_ids.search([('date', '<=', date),
                                                ('operation', '=', state)] + force_domain)

        for operation in operations:
            newer_op = operation.search([
                ('date', '<=', date),
                ('id', '>', operation.id),
                ('check_id', '=', operation.check_id.id),
            ])
            if newer_op:
                operations -= operation
        return operations

    def _get_operation(self, operation, partner_required=False):
        self.ensure_one()
        operation = self.operation_ids.search([
            ('check_id', '=', self.id), ('operation', '=', operation)],
            limit=1)
        if partner_required:
            if not operation.partner_id:
                raise ValidationError(('The %s operation has no partner linked.'
                                       'You will need to do it manually.') % operation)
        return operation

    def reject(self):
        self.ensure_one()
        if self.state in ['deposited', 'selled']:
            operation = self._get_operation(self.state)
            if operation.origin._name == 'account.payment':
                journal = operation.origin.destination_journal_id
            # for compatibility with migration from v8
            elif operation.origin._name == 'account.move':
                journal = operation.origin.journal_id
            else:
                raise ValidationError((
                    'The deposit operation is not linked to a payment.'
                    'If you want to reject you need to do it manually.'))
            vals = self.get_bank_vals(
                'bank_reject', journal)
            action_date = self._context.get('action_date')
            vals['date'] = action_date
            move = self.env['account.move'].create(vals)
            move.post()
            self._add_operation('rejected', move, date=action_date)
        elif self.state in ['delivered', 'handed']:
            operation = self._get_operation(self.state, True)
            return self.action_create_debit_note(
                'rejected', 'supplier', operation.partner_id)

    def action_create_debit_note(self, operation, partner_type, partner):
        self.ensure_one()
        action_date = self._context.get('action_date')

        if partner_type == 'supplier':
            invoice_type = 'in_invoice'
            journal_type = 'purchase'
            view_id = self.env.ref('account.invoice_supplier_form').id
        else:
            invoice_type = 'out_invoice'
            journal_type = 'sale'
            view_id = self.env.ref('account.invoice_form').id

        journal = self.env['account.journal'].search([
            ('company_id', '=', self.company_id.id),
            ('type', '=', journal_type),
        ], limit=1)

        name = _('Check "%s" rejection') % (self.name)

        inv_line_vals = {
            # 'product_id': self.product_id.id,
            'name': name,
            'account_id': journal._get_check_account('rejected').id,
            'price_unit': (
                    self.amount_currency and self.amount_currency or self.amount),
            # 'invoice_id': invoice.id,
        }

        inv_vals = {
            # this is the reference that goes on account.move.line of debt line
            # 'name': name,
            # this is the reference that goes on account.move
            'reference': name,
            'date_invoice': action_date,
            'origin': _('Check nbr (id): %s (%s)') % (self.name, self.id),
            'journal_id': journal.id,
            # this is done on multi company fix
            # 'company_id': journal.company_id.id,
            'partner_id': partner.id,
            'type': invoice_type,
            'invoice_line_ids': [(0, 0, inv_line_vals)],
        }
        if self.currency_id:
            inv_vals['currency_id'] = self.currency_id.id
        # we send internal_type for compatibility with account_document
        invoice = self.env['account.invoice'].with_context(
            internal_type='debit_note').create(inv_vals)
        self._add_operation(operation, invoice, partner, date=action_date)

        return {
            'name': name,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice',
            'view_id': view_id,
            'res_id': invoice.id,
            'type': 'ir.actions.act_window',
        }

    def get_bank_vals(self, action, journal):
        self.ensure_one()
        # TODO improove how we get vals, get them in other functions
        if action == 'bank_debit':
            # self.journal_id.default_debit_account_id.id
            credit_account = journal.default_debit_account_id
            debit_account = journal._get_check_account('deferred')
            name = _('Check "%s" debit') % (self.name)
        elif action == 'bank_reject':
            # self.destination_journal_id.default_credit_account_id
            credit_account = journal.default_debit_account_id
            debit_account = journal._get_check_account('rejected')
            name = _('Check "%s" rejection') % (self.name)
        elif action == 'bank_credit':
            credit_account = journal.default_credit_account_id
            debit_account = journal._get_check_account('deferred')
            name = _('Check "%s" credit') % (self.name)
        else:
            raise ValidationError(_(
                'Action %s not implemented for checks!') % action)

        debit_line_vals = {
            'name': name,
            'partner_id': self.partner_id.id,
            'account_id': debit_account.id,
            'debit': self.amount,
            'amount_currency': self.amount_currency,
        }
        credit_line_vals = {
            'name': name,
            'partner_id': self.partner_id.id,
            'account_id': credit_account.id,
            'credit': self.amount,
            'amount_currency': self.amount_currency,
        }
        return {
            'ref': name,
            'journal_id': journal.id,
            'date': fields.Date.today(),
            'partner_id': self.partner_id.id,
            'move_check_id': self.id,
            'line_ids': [
                (0, False, debit_line_vals),
                (0, False, credit_line_vals)],
        }

    def open_wizard_inbank_check(self):
        """
        open wizard to chose account of debit
        :return:
        """
        action = self.env.ref('account_check.action_wizard_inbank')
        result = action.read()[0]
        res = self.env.ref('account_check.check_action_inbank_form_view', False)
        result['views'] = [(res and res.id or False, 'form')]
        result['target'] = 'new'
        result['context'] = {'default_action_type': 'inbank', 'default_journal_id': self.journal_id.id}
        return result

    def bank_debit_action(self):
        """
        open wizard to chose journal for debit account
        :return:
        """
        self.ensure_one()
        action = self.env.ref('account_check.action_wizard_inbank')
        result = action.read()[0]
        res = self.env.ref('account_check.check_action_inbank_form_view', False)
        result['views'] = [(res and res.id or False, 'form')]
        result['target'] = 'new'
        result['context'] = {'default_action_type': 'bank_debit',
                             'default_inbank_account_id': self.inbank_account_id.id if self.inbank_account_id else False}
        return result

    def bank_return_action(self):
        """
        open wizard to chose journal for debit account
        :return:
        """
        self.ensure_one()
        action = self.env.ref('account_check.action_wizard_inbank')
        result = action.read()[0]
        res = self.env.ref('account_check.check_action_inbank_form_view', False)
        result['views'] = [(res and res.id or False, 'form')]
        holding_account = self.journal_id._get_check_account('holding')
        result['target'] = 'new'
        result['context'] = {'default_action_type': 'returned',
                             'default_inbank_account_id': self.inbank_account_id.id if self.inbank_account_id else False,
                             'default_partner_id': self.partner_id and self.partner_id.id or False,
                             'default_account_id': holding_account and holding_account.id or False}
        return result

    # def open_wizard_customer_notes_return(self):
    #     """
    #     open wizard to chose account of debit
    #     :return:
    #     """
    #     action = self.env.ref('account_check.action_wizard_inbank')
    #     result = action.read()[0]
    #     res = self.env.ref('account_check.check_action_inbank_form_view', False)
    #     result['views'] = [(res and res.id or False, 'form')]
    #     result['target'] = 'new'
    #     result['context'] = {
    #         'default_action_type': 'rejected',
    #         'default_inbank_account_id': self.inbank_account_id.id if self.inbank_account_id else False,
    #     }
    #     return result

    def action_to_handed_from_draft(self):
        self._add_operation('handed', self, self.partner_id, self.issue_date)
        self.write({'state': 'handed'})

    def action_to_in_treasury(self):
        self._add_operation('holding', self, self.partner_id, self.issue_date)
        self.write({'state': 'holding'})

    def change_state_handed(self):
        """
        on start show button to hand check
        :return:
        """
        action = self.env.ref('account_check.action_check_handed_wizard')
        result = action.read()[0]
        res = self.env.ref('account_check.action_handed_wizard_view', False)
        result['views'] = [(res and res.id or False, 'form')]
        result['target'] = 'new'
        result['context'] = {
            'default_check_id': self.id
        }
        return result

    def action_to_handed(self):
        if self.state == 'holding' and self.operation_ids:
            for line in self.operation_ids:
                if line.operation == 'holding':
                    line.write({'operation': 'handed'})
        self.write({'state': 'handed'})

    def change_state(self):
        self.write({'state': 'holding'})

    def return_to_treasury(self):
        action = self.env.ref('account_check.action_wizard_return_treasury')
        result = action.read()[0]
        res = self.env.ref('account_check.check_action_treasury_form', False)
        result['views'] = [(res and res.id or False, 'form')]
        result['target'] = 'new'
        result['context'] = {}
        return result

    def button_draft(self):
        self.write({'state': 'draft'})

    def cancel_action(self):
        self.write({'state': 'cancel'})

    def handed_action(self):
        self.write({'state': 'handed'})

    def open_wizard_customer_sell_check(self):
        action = self.env.ref('account_check.action_wizard_sell_check')
        result = action.read()[0]
        res = self.env.ref('account_check.sell_check_action_wizard_view', False)
        result['views'] = [(res and res.id or False, 'form')]
        result['target'] = 'new'
        result['context'] = {
            'default_amount': self.amount if self.amount else False,
            'default_check_id': self.id
        }
        return result


class JournalEntry(models.Model):
    _inherit = 'account.move'

    move_check_id = fields.Many2one(comodel_name='account.check')

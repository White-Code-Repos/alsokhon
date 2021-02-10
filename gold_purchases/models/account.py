# -*- coding: utf-8 -*-
from itertools import groupby
from odoo.osv import expression
from odoo import api, fields, models , _
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split, email_escape_char, email_re
from odoo.tools.misc import formatLang, format_date, get_lang
from datetime import date, timedelta, datetime

MAP_INVOICE_TYPE_PARTNER_TYPE = {
    'out_invoice': 'customer',
    'out_refund': 'customer',
    'out_receipt': 'customer',
    'in_invoice': 'supplier',
    'in_refund': 'supplier',
    'in_receipt': 'supplier',
}

class AccountAccount(models.Model):
    _inherit = 'account.account'

    @api.constrains('current_position')
    def _constrains_current_position(self):
        """
        constrains current_position
        """
        for rec in self:
            account = self.search([('current_position', '=', True),
                                   ('id', '!=', rec.id)])
            if account:
                raise UserError(
                    _('Current Position Already Marked in %s.' % account.name)
                )

    current_position = fields.Boolean()
    gold = fields.Boolean('Gold')


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    gold = fields.Boolean('Gold Journal')


class AccountReport(models.AbstractModel):
    _inherit = 'account.report'

    @api.model
    def _query_get(self, options, domain=None):
        domain = self._get_options_domain(options) + (domain or [])
        self.env['account.move.line'].check_access_rights('read')
        domain = expression.AND([domain, [('journal_id.gold', '=', False)]])
        query = self.env['account.move.line']._where_calc(domain)
        # Wrap the query with 'company_id IN (...)' to avoid bypassing company access rights.
        self.env['account.move.line']._apply_ir_rules(query)
        return query.get_sql()


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.depends('pure_wt', 'purchase_line_id')
    def _compute_pure_wt_in(self):
        """
        Compute pure_wt_in
        """
        for rec in self:
            pure_wt_in = 0
            if rec.pure_wt and rec.purchase_line_id:
                pure_wt_in = rec.pure_wt
            rec.pure_wt_in = pure_wt_in

    @api.depends('pure_wt', 'sale_line_ids')
    def _compute_pure_wt_out(self):
        """
        Compute pure_wt_out
        """
        for rec in self:
            pure_wt_out = 0
            if rec.pure_wt and rec.sale_line_ids:
                pure_wt_out = rec.pure_wt
            rec.pure_wt_out = pure_wt_out

    gross_wt = fields.Float('Gross Wt', digits=(16, 3))
    purity_id = fields.Many2one('gold.purity', 'Purity')
    pure_wt = fields.Float('Pure Wt', digits=(16, 3))
    pure_wt_in = fields.Float(compute=_compute_pure_wt_in, store=True)
    pure_wt_out = fields.Float(compute=_compute_pure_wt_out, store=True)
    purity_diff = fields.Float('Purity +/-', digits=(16, 3))
    total_gross_weight = fields.Float('Total Gross',digits=(16, 3))
    total_pure_weight = fields.Float('Pure Weight', digits=(16, 3))
    make_rate = fields.Monetary('Make Rate/G', digits=(16, 3))
    make_value = fields.Monetary('Make Value', digits=(16, 3))
    gold_rate = fields.Float('Gold Rate/G', digits=(16, 3))
    gold_value = fields.Monetary('Gold Value', digits=(16, 3))
    gold = fields.Boolean(related="account_id.gold", store=True)
    total_ds_value = fields.Float(string="Total Stone Value", digits=(16, 3))


class GoldPayment(models.Model):
    _name = 'gold.payment'

    move_ids = fields.Many2many(comodel_name='stock.move', string='moves')
    flag = fields.Boolean(_('Flag'), default=False)




class AccountMove(models.Model):
    _inherit = 'account.move'


    is_unfixed = fields.Boolean(default=False, compute="_compute_unfixed_state")
    def _compute_unfixed_state(self):
        for this in self:
            this.is_unfixed = False
            if this.purchase_type == 'unfixed' or this.sale_type == 'unfixed':
                this.is_unfixed = True
    diamond = fields.Boolean(string="Stone", compute="_compute_gold_state")
    gold = fields.Boolean(string="Gold", compute="_compute_gold_state")
    assembly = fields.Boolean(string="Assembly")
    def _compute_gold_state(self):
        for this in self:
            if this.journal_id.gold:
                this.gold = True
                this.diamond = False
            else:
                this.gold = False
                this.diamond = True

    def create_gold_unfixing_entry(self,stock_picking,value):
        self.ensure_one()
        # purchase_obj = self.env['purchase.order'].search([('name','=',purchase_order.name)])
        this = stock_picking
        moves = this.move_lines.filtered(lambda x: x._is_in() and
                                                   x.product_id and
                                                   x.product_id.gold and
                                                   x.product_id.categ_id and
                                                   x.product_id.categ_id.is_gold and
                                                   x.product_id.categ_id.gold_on_hand_account and
                                                   x.product_id.categ_id.gold_fixing_account)
        if moves:
            gold_on_hand_account_id = moves[0].product_id.categ_id.gold_on_hand_account.id
            gold_fixing_account_id = moves[0].product_id.categ_id.gold_fixing_account.id
            if not moves[0].product_id.categ_id.gold_journal.id:
                raise ValidationError(_('Please fill gold journal in product Category'))
            journal_id = moves[0].product_id.categ_id.gold_journal.id
            move_lines = self._prepare_account_move_line_unfixing(gold_on_hand_account_id,gold_fixing_account_id,value)
            if move_lines:
                AccountMove = self.env['account.move'].with_context(
                    default_journal_id=journal_id)
                date = self._context.get('force_period_date',
                                         fields.Date.context_today(self))
                new_account_move = AccountMove.sudo().create({
                    'journal_id': journal_id,
                    'line_ids': move_lines,
                    'date': datetime.now().date(),
                    'ref': '%s - Unfixing' % (self.name),
                    'type': 'entry',
                    'type_of_action': 'unfixed',
                })
                new_account_move.post()
                self.unfixing_move = new_account_move.id

    def create_gold_unfixing_entry_sale(self,stock_picking,value):
        self.ensure_one()
        # purchase_obj = self.env['purchase.order'].search([('name','=',purchase_order.name)])
        this = stock_picking
        moves = this.move_lines.filtered(lambda x: x._is_out() and
                                                   x.product_id and
                                                   x.product_id.gold and
                                                   x.product_id.categ_id and
                                                   x.product_id.categ_id.is_gold and
                                                   x.product_id.categ_id.gold_on_hand_account and
                                                   x.product_id.categ_id.gold_fixing_account)
        if moves:
            gold_on_hand_account_id = moves[0].product_id.categ_id.gold_on_hand_account.id
            gold_fixing_account_id = moves[0].product_id.categ_id.gold_fixing_account.id
            if not moves[0].product_id.categ_id.gold_journal.id:
                raise ValidationError(_('Please fill gold journal in product Category'))
            journal_id = moves[0].product_id.categ_id.gold_journal.id
            move_lines = self._prepare_account_move_line_unfixing_sale(gold_on_hand_account_id,gold_fixing_account_id,value)
            if move_lines:
                AccountMove = self.env['account.move'].with_context(
                    default_journal_id=journal_id)
                date = self._context.get('force_period_date',
                                         fields.Date.context_today(self))
                new_account_move = AccountMove.sudo().create({
                    'journal_id': journal_id,
                    'line_ids': move_lines,
                    'date': datetime.now().date(),
                    'ref': '%s - Unfixing' % (self.name),
                    'type': 'entry',
                    'type_of_action': 'unfixed',
                })
                new_account_move.post()
                self.unfixing_move = new_account_move.id


    def _prepare_account_move_line_unfixing(self, gold_on_hand_account_id,gold_fixing_account_id,value):
        if not gold_on_hand_account_id or not gold_fixing_account_id:
            raise ValidationError(_('Please fill gold accounts in product Category'))
        if value <= 0:
            raise ValidationError(_('Please add a value'))
        debit_line = [{
            'name': '%s - Unfixing' % (self.name),
            'ref': '%s - Unfixing' % (self.name),
            'partner_id': self.partner_id.id,
            'debit': round(value, 3),
            'credit': 0,
            'account_id': gold_fixing_account_id,
        }]
        credit_line = [{
            'name': '%s - Unfixing' % (self.name),
            'ref': '%s - Unfixing' % (self.name),
            'partner_id': self.partner_id.id,
            'debit': 0,
            'credit': debit_line[0]['debit'],
            'account_id': gold_on_hand_account_id,
        }]
        res = [(0, 0, x) for x in debit_line + credit_line]
        return res
    def _prepare_account_move_line_unfixing_sale(self, gold_on_hand_account_id,gold_fixing_account_id,value):
        if not gold_on_hand_account_id or not gold_fixing_account_id:
            raise ValidationError(_('Please fill gold accounts in product Category'))
        if value <= 0:
            raise ValidationError(_('Please add a value'))
        debit_line = [{
            'name': '%s - Unfixing' % (self.name),
            'ref': '%s - Unfixing' % (self.name),
            'partner_id': self.partner_id.id,
            'debit': round(value, 3),
            'credit': 0,
            'account_id': gold_fixing_account_id,
        }]
        credit_line = [{
            'name': '%s - Unfixing' % (self.name),
            'ref': '%s - Unfixing' % (self.name),
            'partner_id': self.partner_id.id,
            'debit': 0,
            'credit': debit_line[0]['debit'],
            'account_id': gold_on_hand_account_id,
        }]
        res = [(0, 0, x) for x in debit_line + credit_line]
        return res

    def create_gold_fixing_entry(self,stock_picking,value):
        self.ensure_one()
        # purchase_obj = self.env['purchase.order'].search([('name','=',purchase_order.name)])
        this = stock_picking
        moves = this.move_lines.filtered(lambda x: x._is_in() and
                                                   x.product_id and
                                                   x.product_id.gold and
                                                   x.product_id.categ_id and
                                                   x.product_id.categ_id.is_gold and
                                                   x.product_id.categ_id.gold_on_hand_account and
                                                   x.product_id.categ_id.gold_fixing_account)
        if moves:
            gold_on_hand_account_id = moves[0].product_id.categ_id.gold_on_hand_account.id
            gold_fixing_account_id = moves[0].product_id.categ_id.gold_fixing_account.id
            if not moves[0].product_id.categ_id.gold_journal.id:
                raise ValidationError(_('Please fill gold journal in product Category'))
            journal_id = moves[0].product_id.categ_id.gold_journal.id
            move_lines = self._prepare_account_move_line_fixing(gold_on_hand_account_id,gold_fixing_account_id,value)
            if move_lines:
                AccountMove = self.env['account.move'].with_context(
                    default_journal_id=journal_id)
                date = self._context.get('force_period_date',
                                         fields.Date.context_today(self))
                new_account_move = AccountMove.sudo().create({
                    'journal_id': journal_id,
                    'line_ids': move_lines,
                    'date': datetime.now().date(),
                    'ref': '%s - Fixing-' % (self.name),
                    'type': 'entry',
                    'type_of_action': 'fixed',
                })
                new_account_move.post()
                self.fixing_move = new_account_move.id
    def create_gold_fixing_entry_sale(self,stock_picking,value):
        self.ensure_one()
        # purchase_obj = self.env['purchase.order'].search([('name','=',purchase_order.name)])
        this = stock_picking
        moves = this.move_lines.filtered(lambda x: x._is_out() and
                                                   x.product_id and
                                                   x.product_id.gold and
                                                   x.product_id.categ_id and
                                                   x.product_id.categ_id.is_gold and
                                                   x.product_id.categ_id.gold_on_hand_account and
                                                   x.product_id.categ_id.gold_fixing_account)
        if moves:
            gold_on_hand_account_id = moves[0].product_id.categ_id.gold_on_hand_account.id
            gold_fixing_account_id = moves[0].product_id.categ_id.gold_fixing_account.id
            if not moves[0].product_id.categ_id.gold_journal.id:
                raise ValidationError(_('Please fill gold journal in product Category'))
            journal_id = moves[0].product_id.categ_id.gold_journal.id
            move_lines = self._prepare_account_move_line_fixing_sale(gold_on_hand_account_id,gold_fixing_account_id,value)
            if move_lines:
                AccountMove = self.env['account.move'].with_context(
                    default_journal_id=journal_id)
                date = self._context.get('force_period_date',
                                         fields.Date.context_today(self))
                new_account_move = AccountMove.sudo().create({
                    'journal_id': journal_id,
                    'line_ids': move_lines,
                    'date': datetime.now().date(),
                    'ref': '%s - Fixing-' % (self.name),
                    'type': 'entry',
                    'type_of_action': 'fixed',
                })
                new_account_move.post()
                self.fixing_move = new_account_move.id


    def _prepare_account_move_line_fixing(self, gold_on_hand_account_id,gold_fixing_account_id,value):
        if not gold_on_hand_account_id or not gold_fixing_account_id:
            raise ValidationError(_('Please fill gold accounts in product Category'))
        if value <= 0:
            raise ValidationError(_('Please add a value'))
        debit_line = [{
            'name': '%s - Fixing' % (self.name),
            'ref': '%s - Fixing' % (self.name),
            'partner_id': self.partner_id.id,
            'debit': round(value, 3),
            'credit': 0,
            'account_id': gold_on_hand_account_id,
        }]
        credit_line = [{
            'name': '%s - Fixing' % (self.name),
            'ref': '%s - Fixing' % (self.name),
            'partner_id': self.partner_id.id,
            'debit': 0,
            'credit': debit_line[0]['debit'],
            'account_id': gold_fixing_account_id,
        }]
        res = [(0, 0, x) for x in debit_line + credit_line]
        return res
    def _prepare_account_move_line_fixing_sale(self, gold_on_hand_account_id,gold_fixing_account_id,value):
        if not gold_on_hand_account_id or not gold_fixing_account_id:
            raise ValidationError(_('Please fill gold accounts in product Category'))
        if value <= 0:
            raise ValidationError(_('Please add a value'))
        debit_line = [{
            'name': '%s - Fixing' % (self.name),
            'ref': '%s - Fixing' % (self.name),
            'partner_id': self.partner_id.id,
            'debit': round(value, 3),
            'credit': 0,
            'account_id': gold_on_hand_account_id,
        }]
        credit_line = [{
            'name': '%s - Fixing' % (self.name),
            'ref': '%s - Fixing' % (self.name),
            'partner_id': self.partner_id.id,
            'debit': 0,
            'credit': debit_line[0]['debit'],
            'account_id': gold_fixing_account_id,
        }]
        res = [(0, 0, x) for x in debit_line + credit_line]
        return res

    def convert_fixed_sale(self,value):
        if self.invoice_origin and 'S0'in self.invoice_origin:
            sale_order = self.env['sale.order'].search([('name','=',self.invoice_origin)])
            if sale_order:
                stock_picking = self.env['stock.picking'].search([('origin','=',sale_order.name)])
                if stock_picking:
                    self.create_gold_unfixing_entry_sale(stock_picking,value)
                    self.create_gold_fixing_entry_sale(stock_picking,value)
                    self.pure_wt_value -= value
                    self.write({'unfixed_fixed_gold': self.unfixed_fixed_gold+value})
                    self.write({'unfixed_fixed_remain': self.unfixed_fixed_remain+self.unfixed_fixed_value})
    def convert_fixed(self,value):
        if self.invoice_origin and 'P0'in self.invoice_origin:
            purchase_order = self.env['purchase.order'].search([('name','=',self.invoice_origin)])
            if purchase_order:
                stock_picking = self.env['stock.picking'].search([('origin','=',purchase_order.name)])
                if stock_picking:
                    self.create_gold_unfixing_entry(stock_picking,value)
                    self.create_gold_fixing_entry(stock_picking,value)
                    self.pure_wt_value -= value
                    self.write({'unfixed_fixed_gold': self.unfixed_fixed_gold+value})
                    self.write({'unfixed_fixed_remain': self.unfixed_fixed_remain+self.unfixed_fixed_value})

    unfixed_fixed_gold = fields.Float('Unfixed -> Fixed Gold', digits=(16, 3))
    unfixed_fixed_value = fields.Float('Unfixed -> Fixed Due', compute="compute_unfixed_fixed_value", digits=(16, 3))
    unfixed_fixed_paid = fields.Float('Unfixed -> Fixed Paid', compute="compute_unfixed_fixed_paid", digits=(16, 3))
    def compute_unfixed_fixed_paid(self):
        for this in self:
            this.unfixed_fixed_paid = this.unfixed_fixed_value - this.unfixed_fixed_remain
    unfixed_fixed_remain = fields.Float('Unfixed -> Fixed Remaining', digits=(16, 3))
    fixed_not_paid = fields.Boolean(default=True)
    fixing_move = fields.Many2one('account.move')
    unfixing_move = fields.Many2one('account.move')

    # compute="compute_unfixed_fixed_remain"

    # def compute_unfixed_fixed_remain(self):
    #     for this in self:
    #         if this.unfixed_fixed_paid > 0.00:
    #             this.unfixed_fixed_remain = this.unfixed_fixed_value - this.unfixed_fixed_paid
    #         else:
    #             this.unfixed_fixed_remain = this.unfixed_fixed_value

    def compute_unfixed_fixed_value(self):
        for this in self:
            if this.gold_rate_value and this.unfixed_fixed_gold > 0.00:
                this.unfixed_fixed_value = this.gold_rate_value * this.unfixed_fixed_gold
            else:
                this.unfixed_fixed_value = 0.0


    def open_wizard_for_fixing(self):
        return self.env.ref('gold_purchases.action_fixing_unfixed_bill_wiz')



    is_gold_entry = fields.Boolean(compute="_compute_is_gold_entry")
    def _compute_is_gold_entry(self):
        for this in self:
            if this.journal_id.gold:
                this.is_gold_entry = True
            else:
                this.is_gold_entry = False

    purchase_type = fields.Selection([('fixed', 'Fixed'),
                                        ('unfixed', 'Unfixed')], string='purchase type')
    gold_rate_value = fields.Float( string='Gold Rate/G',compute="_compute_make_value_move",store=True, digits=(16, 3))
    make_value_move = fields.Float( string='Remainning Money',compute="_compute_make_value_move",store=True, digits=(16, 3))
    make_value_move_perm = fields.Float( string='Due Money',store=True, digits=(16, 3))
    make_value_move_paid = fields.Float( string='Paid Money', compute="compute_gold_paid",store=True, digits=(16, 3))
    make_value_move_perm_flag = fields.Boolean(default=False)
    pure_wt_value = fields.Float( string='Remaining Pure Weight',compute="_compute_make_value_move",store=True, digits=(16, 3))
    pure_wt_value_perm = fields.Float( string='Due Pure Weight',store=True, digits=(16, 3))
    pure_wt_value_paid = fields.Float( string='Paid Pure Weight', compute="compute_gold_paid",store=True, digits=(16, 3))
    pure_wt_value_perm_flag = fields.Boolean(default=False)
    # dimaond_value_move = fields.Float( string='Remainning Diamond Value',compute="_compute_make_value_move",store=True, digits=(16, 3))
    # dimaond_value_move_perm = fields.Float( string='Due Diamond Value',store=True, digits=(16, 3))
    # dimaond_value_move_paid = fields.Float( string='Paid Diamond Value', compute="compute_gold_paid",store=True, digits=(16, 3))
    # dimaond_value_move_perm_flag = fields.Boolean(default=False)


    @api.depends('gold_rate_value','make_value_move','make_value_move_perm','make_value_move_paid','make_value_move_perm_flag','pure_wt_value','pure_wt_value_perm','pure_wt_value_paid','pure_wt_value_perm_flag')
    def compute_gold_paid(self):
        for this in self:
            this.make_value_move_paid = this.make_value_move_perm - this.make_value_move
            this.pure_wt_value_paid = this.pure_wt_value_perm - this.pure_wt_value - this.unfixed_fixed_gold
            this.dimaond_value_move_paid = this.dimaond_value_move_perm - this.dimaond_value_move


    unfixed_move_id = fields.Many2one('account.move')
    unfixed_move_id_two = fields.Many2one('account.move')
    unfixed_move_id_three = fields.Many2one('account.move')
    unfixed_stock_picking = fields.Many2one('stock.picking')
    unfixed_stock_picking_two= fields.Many2one('stock.picking')
    unfixed_stock_picking_three= fields.Many2one('stock.picking')

    @api.depends(
        'line_ids.debit',
        'line_ids.credit',
        'line_ids.currency_id',
        'line_ids.amount_currency',
        'line_ids.amount_residual',
        'line_ids.amount_residual_currency',
        'make_value_move',
        'pure_wt_value',
        'line_ids.payment_id.state')
    def _compute_amount(self):
        invoice_ids = [move.id for move in self if move.id and move.is_invoice(include_receipts=True)]
        self.env['account.payment'].flush(['state'])
        if invoice_ids:
            self._cr.execute(
                '''
                    SELECT move.id
                    FROM account_move move
                    JOIN account_move_line line ON line.move_id = move.id
                    JOIN account_partial_reconcile part ON part.debit_move_id = line.id OR part.credit_move_id = line.id
                    JOIN account_move_line rec_line ON
                        (rec_line.id = part.credit_move_id AND line.id = part.debit_move_id)
                        OR
                        (rec_line.id = part.debit_move_id AND line.id = part.credit_move_id)
                    JOIN account_payment payment ON payment.id = rec_line.payment_id
                    JOIN account_journal journal ON journal.id = rec_line.journal_id
                    WHERE payment.state IN ('posted', 'sent')
                    AND journal.post_at = 'bank_rec'
                    AND move.id IN %s
                ''', [tuple(invoice_ids)]
            )
            in_payment_set = set(res[0] for res in self._cr.fetchall())
        else:
            in_payment_set = {}

        for move in self:
            total_untaxed = 0.0
            total_untaxed_currency = 0.0
            total_tax = 0.0
            total_tax_currency = 0.0
            total_residual = 0.0
            total_residual_currency = 0.0
            total = 0.0
            total_currency = 0.0
            currencies = set()

            for line in move.line_ids:
                if line.currency_id:
                    currencies.add(line.currency_id)

                if move.is_invoice(include_receipts=True):
                    # === Invoices ===

                    if not line.exclude_from_invoice_tab:
                        # Untaxed amount.
                        total_untaxed += line.balance
                        total_untaxed_currency += line.amount_currency
                        total += line.balance
                        total_currency += line.amount_currency
                    elif line.tax_line_id:
                        # Tax amount.
                        total_tax += line.balance
                        total_tax_currency += line.amount_currency
                        total += line.balance
                        total_currency += line.amount_currency
                    elif line.account_id.user_type_id.type in ('receivable', 'payable'):
                        # Residual amount.
                        total_residual += line.amount_residual
                        total_residual_currency += line.amount_residual_currency
                else:
                    # === Miscellaneous journal entry ===
                    if line.debit:
                        total += line.balance
                        total_currency += line.amount_currency

            if move.type == 'entry' or move.is_outbound():
                sign = 1
            else:
                sign = -1
            move.amount_untaxed = sign * (total_untaxed_currency if len(currencies) == 1 else total_untaxed)
            move.amount_tax = sign * (total_tax_currency if len(currencies) == 1 else total_tax)
            move.amount_total = sign * (total_currency if len(currencies) == 1 else total)
            if move.purchase_type == "unfixed" or move.sale_type == "unfixed":
                if  move.make_value_move <= 0.00 and move.pure_wt_value <= 0.00 and move.unfixed_fixed_remain <= 0.00:
                    move.amount_residual = 0.00
                else:
                    move.amount_residual = -sign * (total_residual_currency if len(currencies) == 1 else total_residual)
            else:
                print('ELSEEEEEEEEEEEEEEEEEEEEEEE')
                move.amount_residual = -sign * (total_residual_currency if len(currencies) == 1 else total_residual)
                print(move.amount_residual)

            move.amount_untaxed_signed = -total_untaxed
            move.amount_tax_signed = -total_tax
            move.amount_total_signed = abs(total) if move.type == 'entry' else -total
            move.amount_residual_signed = total_residual

            currency = len(currencies) == 1 and currencies.pop() or move.company_id.currency_id
            is_paid = currency and currency.is_zero(move.amount_residual) or not move.amount_residual
            if move.type == 'entry':
                move.invoice_payment_state = False

            elif move.state == 'posted' and is_paid  and move.fixed_not_paid == False:
                print(":ADSLKDSLS")
                print(in_payment_set)
                if move.id in in_payment_set:
                    move.invoice_payment_state = 'in_payment'
                else:
                    print("PAIDDDD")
                    move.invoice_payment_state = 'paid'
            elif move.state == 'posted' and is_paid  and (move.purchase_type == 'fixed' or move.sale_type == "fixed"):
                if move.id in in_payment_set:
                    move.invoice_payment_state = 'in_payment'
                else:
                    move.invoice_payment_state = 'paid'
            elif move.state == 'posted' and is_paid and not move.purchase_type and not move.sale_type:
                if move.id in in_payment_set:
                    move.invoice_payment_state = 'in_payment'
                else:
                    move.invoice_payment_state = 'paid'
            else:
                move.invoice_payment_state = 'not_paid'



    @api.depends('invoice_line_ids')
    def _compute_make_value_move(self):
        for rec in self:
            print("rec")
            print(rec)
            print("rec")
            if rec.purchase_type == "unfixed" or rec.sale_type == "unfixed":
                print("++++++++++++++++++============____________)()")
                make_value = 0.00
                pure = 0.00
                rate = 0.00
                got_rate = False
                for line in rec.invoice_line_ids:
                    print(line)
                    print(line.pure_wt)
                    print(line.make_value)
                    if line.pure_wt == 0.00 and line.make_value == 0.00:
                        make_value += line.price_unit
                    else:
                        make_value += line.total_ds_value
                        pure += line.pure_wt
                        if not got_rate:
                            rate = line.gold_rate
                rec.pure_wt_value = pure
                rec.gold_rate_value = rate
                if rec.amount_by_group:
                    rec.make_value_move = make_value + rec.amount_by_group[0][1]
                else:
                    rec.make_value_move = make_value
                if rec.pure_wt_value > 0 or rec.make_value_move > 0:
                    if rec.pure_wt_value_perm_flag == False:
                        rec.pure_wt_value_perm = rec.pure_wt_value
                        rec.pure_wt_value_perm_flag = True
                    if rec.make_value_move_perm_flag == False:
                        rec.make_value_move_perm = rec.make_value_move
                        rec.make_value_move_perm_flag = True



    def button_draft(self):
        res = super(AccountMove, self).button_draft()
        po_id = self.is_po_related()
        if po_id:
            po_id.bill_move_id.write({'state': 'draft'})
        return res

    def post(self):
        po_id = self.is_po_related()
        if po_id:
            if not po_id.bill_move_id:
                self.create_gold_journal_entry(po_id)
            elif po_id.bill_move_id:
                for acc_move in po_id.bill_move_id:
                    if acc_move.state == "draft":
                        acc_move.action_post()

        for move in self:
            if not move.line_ids.filtered(lambda line: not line.display_type):
                raise UserError(_('You need to add a line before posting.'))
            if move.auto_post and move.date > fields.Date.today():
                date_msg = move.date.strftime(get_lang(self.env).date_format)
                raise UserError(_("This move is configured to be auto-posted on %s" % date_msg))

            if not move.partner_id:
                if move.is_sale_document():
                    raise UserError(_("The field 'Customer' is required, please complete it to validate the Customer Invoice."))
                elif move.is_purchase_document():
                    raise UserError(_("The field 'Vendor' is required, please complete it to validate the Vendor Bill."))

            if move.is_invoice(include_receipts=True) and float_compare(move.amount_total, 0.0, precision_rounding=move.currency_id.rounding) < 0:
                raise UserError(_("You cannot validate an invoice with a negative total amount. You should create a credit note instead. Use the action menu to transform it into a credit note or refund."))

            # Handle case when the invoice_date is not set. In that case, the invoice_date is set at today and then,
            # lines are recomputed accordingly.
            # /!\ 'check_move_validity' must be there since the dynamic lines will be recomputed outside the 'onchange'
            # environment.
            if not move.invoice_date and move.is_invoice(include_receipts=True):
                move.invoice_date = fields.Date.context_today(self)
                move.with_context(check_move_validity=False)._onchange_invoice_date()

            # When the accounting date is prior to the tax lock date, move it automatically to the next available date.
            # /!\ 'check_move_validity' must be there since the dynamic lines will be recomputed outside the 'onchange'
            # environment.
            if (move.company_id.tax_lock_date and move.date <= move.company_id.tax_lock_date) and (move.line_ids.tax_ids or move.line_ids.tag_ids):
                move.date = move.company_id.tax_lock_date + timedelta(days=1)
                move.with_context(check_move_validity=False)._onchange_currency()

        # Create the analytic lines in batch is faster as it leads to less cache invalidation.
        self.mapped('line_ids').create_analytic_lines()
        for move in self:
            if move.auto_post and move.date > fields.Date.today():
                raise UserError(_("This move is configured to be auto-posted on {}".format(move.date.strftime(get_lang(self.env).date_format))))

            move.message_subscribe([p.id for p in [move.partner_id] if p not in move.sudo().message_partner_ids])

            to_write = {'state': 'posted'}

            if move.name == '/':
                # Get the journal's sequence.
                sequence = move._get_sequence()
                if not sequence:
                    raise UserError(_('Please define a sequence on your journal.'))

                # Consume a new number.
                to_write['name'] = sequence.next_by_id(sequence_date=move.date)

            move.write(to_write)

            # Compute 'ref' for 'out_invoice'.
            if move.type == 'out_invoice' and not move.invoice_payment_ref:
                to_write = {
                    'invoice_payment_ref': move._get_invoice_computed_reference(),
                    'line_ids': []
                }
                for line in move.line_ids.filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable')):
                    to_write['line_ids'].append((1, line.id, {'name': to_write['invoice_payment_ref']}))
                move.write(to_write)

            if move == move.company_id.account_opening_move_id and not move.company_id.account_bank_reconciliation_start:
                # For opening moves, we set the reconciliation date threshold
                # to the move's date if it wasn't already set (we don't want
                # to have to reconcile all the older payments -made before
                # installing Accounting- with bank statements)
                move.company_id.account_bank_reconciliation_start = move.date

        po_id = self.is_po_related()
        if po_id:
            po_id.bill_move_id.write({'ref':self.name})

        for move in self:
            if not move.partner_id: continue
            if move.type.startswith('out_'):
                move.partner_id._increase_rank('customer_rank')
            elif move.type.startswith('in_'):
                move.partner_id._increase_rank('supplier_rank')
            else:
                continue

        # Trigger action for paid invoices in amount is zero
        self.filtered(
            lambda m: m.is_invoice(include_receipts=True) and m.currency_id.is_zero(m.amount_total)
        ).action_invoice_paid()




    def is_po_related(self):
        '''
        find's related purchase order, if found check for order type = fixed
        :return: if order type == fixed return po else false
        '''
        po_id = self.env['purchase.order'].search(
            [('invoice_ids', '=', self.id)])
        if po_id and (po_id[0].order_type.is_fixed or po_id[0].order_type.is_unfixed):
            return po_id
        return False

    def create_gold_journal_entry(self, po_id):
        self.ensure_one()
        moves = self.invoice_line_ids.filtered(lambda x: x.product_id and
                                                         x.product_id.gold and
                                                         x.product_id.categ_id and
                                                         x.product_id.categ_id.is_gold and
                                                         x.product_id.categ_id.gold_expense_account)
        if moves:
            total_purity = 0
            product_dict = {}
            description =  self.name
            for product_id, move_list in groupby(moves, lambda x: x.product_id):
                if product_id not in product_dict.keys():
                    product_dict[product_id] = sum(
                        x.pure_wt for x in move_list)
                else:
                    product_dict[product_id] = product_dict[product_id] + sum(
                        x.pure_wt for x in move_list)
            total_purity = sum(value for key, value in product_dict.items())
            if not  self.partner_id.gold_account_payable_id:
                    raise ValidationError(_('Please fill gold payable account for the partner'))
            if total_purity > 0.0 and product_dict and \
                    self.partner_id and self.partner_id.gold_account_payable_id:
                if not next(iter(product_dict)).categ_id.gold_purchase_journal.id:
                    raise ValidationError(_('Please fill gold purchase journal in product Category'))
                journal_id = next(iter(product_dict)).categ_id.gold_purchase_journal.id

                move_lines = self._prepare_account_move_line(product_dict, po_id)
                if move_lines:
                    AccountMove = self.with_context(default_type='entry',
                        default_journal_id=journal_id)
                    date = self._context.get('force_period_date',
                                             fields.Date.context_today(self))
                    new_account_move = AccountMove.sudo().create({
                        'journal_id': journal_id,
                        'line_ids': move_lines,
                        'date': date,
                        'ref': description,
                        'type': 'entry'
                    })
                    new_account_move.post()
                    print ('----------------------', new_account_move)
                    po_id.write({'bill_move_id': new_account_move.id})

    def _prepare_account_move_line(self, product_dict, po_id):
        debit_lines = []
        for product_id, value in product_dict.items():
            debit_lines.append({
                'name': '%s - %s' % (po_id.name, product_id.name),
                'product_id': product_id.id,
                'quantity': 1,
                'product_uom_id': product_id.uom_id.id,
                'ref': '%s - %s' % (po_id.name, product_id.name),
                'partner_id': self.partner_id.id,
                'debit': round(value, 3),
                'credit': 0,
                'account_id': product_id.categ_id.gold_expense_account.id,
            })
        credit_line = [{
            'name': '%s - %s' % (po_id.name, product_id.name),
            'product_id': product_id.id,
            'quantity': 1,
            'product_uom_id': product_id.uom_id.id,
            'ref': '%s - %s' % (po_id.name, product_id.name),
            'partner_id': self.partner_id.id,
            'debit': 0,
            'credit': sum(x['debit'] for x in debit_lines),
            'account_id': self.partner_id.gold_account_payable_id.id,
        }]
        res = [(0, 0, x) for x in debit_lines + credit_line]
        return res



class Account_Payment_Inherit(models.Model):
    _inherit = 'account.payment'

    is_unfixed_wizard = fields.Boolean('is_unfixed')
    unfixed_option = fields.Selection([('make_tax', 'Money (Non Gold Value)'), ('pay_gold_value', 'Pay Fixed Gold Value')],string='Unfixed Option')

    @api.onchange('unfixed_option')
    def _onchange_unfixed_option(self):
        active_ids = self._context.get('active_ids') or self._context.get('active_id')
        account_move = self.env['account.move'].browse(active_ids)
        if self.unfixed_option and self.unfixed_option == 'pay_gold_value':
            if account_move.unfixed_fixed_value == 0.00:
                raise ValidationError(_('You Should Convert This Bill To Fixed Gold First'))
        if self.unfixed_option:
           if self.unfixed_option == "make_tax" :
               self.write({'amount': account_move.make_value_move})
           else:
               self.write({'amount': account_move.unfixed_fixed_remain })


    @api.model
    def default_get(self, default_fields):
        rec = super(Account_Payment_Inherit, self).default_get(default_fields)
        active_ids = self._context.get('active_ids') or self._context.get('active_id')
        active_model = self._context.get('active_model')

        # Check for selected invoices ids
        if not active_ids or active_model != 'account.move':
            return rec

        invoices = self.env['account.move'].browse(active_ids).filtered(lambda move: move.is_invoice(include_receipts=True))

        # Check all invoices are open
        if not invoices or any(invoice.state != 'posted' for invoice in invoices):
            raise UserError(_("You can only register payments for open invoices"))
        # Check if, in batch payments, there are not negative invoices and positive invoices
        dtype = invoices[0].type
        for inv in invoices[1:]:
            if inv.type != dtype:
                if ((dtype == 'in_refund' and inv.type == 'in_invoice') or
                        (dtype == 'in_invoice' and inv.type == 'in_refund')):
                    raise UserError(_("You cannot register payments for vendor bills and supplier refunds at the same time."))
                if ((dtype == 'out_refund' and inv.type == 'out_invoice') or
                        (dtype == 'out_invoice' and inv.type == 'out_refund')):
                    raise UserError(_("You cannot register payments for customer invoices and credit notes at the same time."))

        amount = self._compute_payment_amount(invoices, invoices[0].currency_id, invoices[0].journal_id, rec.get('payment_date') or fields.Date.today())
        if invoices:
            if invoices.purchase_type == "unfixed" or   invoices.sale_type == "unfixed":
                rec.update({
                            'currency_id': invoices[0].currency_id.id,
                            'amount': abs(invoices.make_value_move),
                            'is_unfixed_wizard': True,
                            'payment_type': 'inbound' if amount > 0 else 'outbound',
                            'partner_id': invoices[0].commercial_partner_id.id,
                            'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type],
                            'communication': invoices[0].invoice_payment_ref or invoices[0].ref or invoices[0].name,
                            'invoice_ids': [(6, 0, invoices.ids)],
                            })
            else:
                rec.update({
                    'currency_id': invoices[0].currency_id.id,
                    'amount': abs(amount),
                    'payment_type': 'inbound' if amount > 0 else 'outbound',
                    'partner_id': invoices[0].commercial_partner_id.id,
                    'partner_type': MAP_INVOICE_TYPE_PARTNER_TYPE[invoices[0].type],
                    'communication': invoices[0].invoice_payment_ref or invoices[0].ref or invoices[0].name,
                    'invoice_ids': [(6, 0, invoices.ids)],
                })

        return rec



    def post(self):
        """ Create the journal items for the payment and update the payment's state to 'posted'.
            A journal entry is created containing an item in the source liquidity account (selected journal's default_debit or default_credit)
            and another in the destination reconcilable account (see _compute_destination_account_id).
            If invoice_ids is not empty, there will be one reconcilable move line per invoice to reconcile with.
            If the payment is a transfer, a second journal entry is created in the destination journal to receive money from the transfer account.
        """
        AccountMove = self.env['account.move'].with_context(default_type='entry')
        for rec in self:
            if rec.invoice_ids:
                print("+++++++++++++++++++++++++++++++++++++++++")
                if rec.invoice_ids.purchase_type == 'unfixed' or rec.invoice_ids.sale_type == 'unfixed':
                    print("***********************")
                    if rec.amount > rec.invoice_ids.make_value_move and rec.unfixed_option != "pay_gold_value":
                        raise UserError(_("unfixed bill you can pay" + "" + str(rec.invoice_ids.make_value_move)))
                    if rec.unfixed_option != "pay_gold_value" and rec.invoice_ids.make_value_move == 0.00:
                        raise UserError(_("make value and tax paid !!"))

                    if rec.invoice_ids.make_value_move <= 0.00 and rec.unfixed_option == "pay_gold_value":
                        print("------------------------------")
                        if rec.invoice_ids.pure_wt_value <= (rec.amount / rec.invoice_ids.gold_rate_value ):
                            rec.invoice_ids.write({'pure_wt_value': 0.00})

                    if rec.unfixed_option == "make_tax":
                        rec.invoice_ids.write({'make_value_move':rec.invoice_ids.make_value_move - rec.amount })

                    if rec.unfixed_option == "pay_gold_value":
                        print("*********************************")
                        rec.invoice_ids.write({'unfixed_fixed_remain': rec.invoice_ids.unfixed_fixed_remain - rec.amount,'fixed_not_paid':False })
                        print(rec.invoice_ids.unfixed_fixed_paid)
                        print(rec.invoice_ids.unfixed_fixed_remain)

                    if rec.invoice_ids.pure_wt_value <= 0.00 and rec.invoice_ids.make_value_move <= 0.00 and rec.invoice_ids.unfixed_fixed_remain <= 0.00 and rec.invoice_ids.unfixed_fixed_paid > 0.00:
                        print("paid in payment")
                        rec.invoice_ids.write({'invoice_payment_state': "paid"})





            if rec.state != 'draft':
                raise UserError(_("Only a draft payment can be posted."))

            if any(inv.state != 'posted' for inv in rec.invoice_ids):
                raise ValidationError(_("The payment cannot be processed because the invoice is not open!"))

            # keep the name in case of a payment reset to draft
            if not rec.name:
                # Use the right sequence to set the name
                if rec.payment_type == 'transfer':
                    sequence_code = 'account.payment.transfer'
                else:
                    if rec.partner_type == 'customer':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.customer.invoice'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.customer.refund'
                    if rec.partner_type == 'supplier':
                        if rec.payment_type == 'inbound':
                            sequence_code = 'account.payment.supplier.refund'
                        if rec.payment_type == 'outbound':
                            sequence_code = 'account.payment.supplier.invoice'
                rec.name = self.env['ir.sequence'].next_by_code(sequence_code, sequence_date=rec.payment_date)
                if not rec.name and rec.payment_type != 'transfer':
                    raise UserError(_("You have to define a sequence for %s in your company.") % (sequence_code,))

            moves = AccountMove.create(rec._prepare_payment_moves())
            moves.filtered(lambda move: move.journal_id.post_at != 'bank_rec').post()

            # Update the state / move before performing any reconciliation.
            move_name = self._get_move_name_transfer_separator().join(moves.mapped('name'))
            rec.write({'state': 'posted', 'move_name': move_name})

            if rec.payment_type in ('inbound', 'outbound'):
                # ==== 'inbound' / 'outbound' ====
                if rec.invoice_ids:
                    (moves[0] + rec.invoice_ids).line_ids \
                        .filtered(lambda line: not line.reconciled and line.account_id == rec.destination_account_id)\
                        .reconcile()
            elif rec.payment_type == 'transfer':
                # ==== 'transfer' ====
                moves.mapped('line_ids')\
                    .filtered(lambda line: line.account_id == rec.company_id.transfer_account_id)\
                    .reconcile()

        return True


class Account_report_inherit(models.AbstractModel):
    _inherit = 'account.general.ledger'

    @api.model
    def _do_query(self, options_list, expanded_account=None, fetch_lines=True):
        ''' Execute the queries, perform all the computation and return (accounts_results, taxes_results). Both are
        lists of tuple (record, fetched_values) sorted by the table's model _order:
        - accounts_values: [(record, values), ...] where
            - record is an account.account record.
            - values is a list of dictionaries, one per period containing:
                - sum:                              {'debit': float, 'credit': float, 'balance': float}
                - (optional) initial_balance:       {'debit': float, 'credit': float, 'balance': float}
                - (optional) unaffected_earnings:   {'debit': float, 'credit': float, 'balance': float}
                - (optional) lines:                 [line_vals_1, line_vals_2, ...]
        - taxes_results: [(record, values), ...] where
            - record is an account.tax record.
            - values is a dictionary containing:
                - base_amount:  float
                - tax_amount:   float
        :param options_list:        The report options list, first one being the current dates range, others being the
                                    comparisons.
        :param expanded_account:    An optional account.account record that must be specified when expanding a line
                                    with of without the load more.
        :param fetch_lines:         A flag to fetch the account.move.lines or not (the 'lines' key in accounts_values).
        :return:                    (accounts_values, taxes_results)
        '''
        # Execute the queries and dispatch the results.
        query, params = self._get_query_sums(options_list, expanded_account=expanded_account)

        groupby_accounts = {}
        groupby_companies = {}
        groupby_taxes = {}

        self._cr.execute(query, params)
        for res in self._cr.dictfetchall():
            # No result to aggregate.
            if res['groupby'] is None:
                continue

            i = res['period_number']
            key = res['key']
            if key == 'sum':
                groupby_accounts.setdefault(res['groupby'], [{} for n in range(len(options_list))])
                groupby_accounts[res['groupby']][i][key] = res
            elif key == 'initial_balance':
                groupby_accounts.setdefault(res['groupby'], [{} for n in range(len(options_list))])
                groupby_accounts[res['groupby']][i][key] = res
            elif key == 'unaffected_earnings':
                groupby_companies.setdefault(res['groupby'], [{} for n in range(len(options_list))])
                groupby_companies[res['groupby']][i] = res
            elif key == 'base_amount' and len(options_list) == 1:
                groupby_taxes.setdefault(res['groupby'], {})
                groupby_taxes[res['groupby']][key] = res['balance']
            elif key == 'tax_amount' and len(options_list) == 1:
                groupby_taxes.setdefault(res['groupby'], {})
                groupby_taxes[res['groupby']][key] = res['balance']

        # Fetch the lines of unfolded accounts.
        # /!\ Unfolding lines combined with multiple comparisons is not supported.
        if fetch_lines and len(options_list) == 1:
            options = options_list[0]
            unfold_all = options.get('unfold_all') or (self._context.get('print_mode') and not options['unfolded_lines'])
            if expanded_account or unfold_all or options['unfolded_lines']:
                query, params = self._get_query_amls(options, expanded_account)
                self._cr.execute(query, params)
                for res in self._cr.dictfetchall():
                    groupby_accounts[res['account_id']][0].setdefault('lines', [])
                    groupby_accounts[res['account_id']][0]['lines'].append(res)

        # Affect the unaffected earnings to the first fetched account of type 'account.data_unaffected_earnings'.
        # There is an unaffected earnings for each company but it's less costly to fetch all candidate accounts in
        # a single search and then iterate it.
        if groupby_companies:
            unaffected_earnings_type = self.env.ref('account.data_unaffected_earnings')
            candidates_accounts = self.env['account.account'].search([
                ('user_type_id', '=', unaffected_earnings_type.id), ('company_id', 'in', list(groupby_companies.keys()))
            ])
            for account in candidates_accounts:
                company_unaffected_earnings = groupby_companies.get(account.company_id.id)
                if not company_unaffected_earnings:
                    continue
                for i in range(len(options_list)):
                    unaffected_earnings = company_unaffected_earnings[i]
                    groupby_accounts.setdefault(account.id, [{} for i in range(len(options_list))])
                    groupby_accounts[account.id][i]['unaffected_earnings'] = unaffected_earnings
                del groupby_companies[account.company_id.id]

        # Retrieve the accounts to browse.
        # groupby_accounts.keys() contains all account ids affected by:
        # - the amls in the current period.
        # - the amls affecting the initial balance.
        # - the unaffected earnings allocation.
        # Note a search is done instead of a browse to preserve the table ordering.
        if expanded_account:
            accounts = expanded_account
        elif groupby_accounts:
            if self.env.context.get('gold'):
                accounts = self.env['account.account'].search([('id', 'in', list(groupby_accounts.keys())),('gold','=',True)])
            else:
                accounts = self.env['account.account'].search([('id', 'in', list(groupby_accounts.keys())),('gold','=',False)])
        else:
            accounts = []
        accounts_results = [(account, groupby_accounts[account.id]) for account in accounts]

        # Fetch as well the taxes.
        if groupby_taxes:
            taxes = self.env['account.tax'].search([('id', 'in', list(groupby_taxes.keys()))])
        else:
            taxes = []
        taxes_results = [(tax, groupby_taxes[tax.id]) for tax in taxes]
        return accounts_results, taxes_results

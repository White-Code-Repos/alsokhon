# -*- coding: utf-8 -*-
from itertools import groupby
from odoo.osv import expression
from odoo import api, fields, models , _
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split, email_escape_char, email_re
from odoo.tools.misc import formatLang, format_date, get_lang
from datetime import date, timedelta

class AccountMove(models.Model):
    _inherit = 'account.move'

    type_of_action = fields.Selection([('fixed', 'Fixed'),
                                        ('unfixed', 'Unfixed')])
    sale_type = fields.Selection([('fixed', 'Fixed'),
                                        ('unfixed', 'Unfixed')], string='sale type', compute="_compute_sale_type")
    def _compute_sale_type(self):
        for this in self:
            if this.invoice_origin and 'S0' in this.invoice_origin:
                sale_order = self.env['sale.order'].search([('name','=',this.invoice_origin)])
                if sale_order and len(sale_order)>0:
                    if sale_order.order_type.is_fixed:
                        this.sale_type = 'fixed'
                    elif sale_order.order_type.gold:
                        this.sale_type = 'unfixed'
                    else:
                        this.sale_type = False
                else:
                    this.sale_type = False
            else:
                this.sale_type = False


    # @api.depends(
    #     'line_ids.debit',
    #     'line_ids.credit',
    #     'line_ids.currency_id',
    #     'line_ids.amount_currency',
    #     'line_ids.amount_residual',
    #     'line_ids.amount_residual_currency',
    #     'make_value_move',
    #     'pure_wt_value',
    #     'line_ids.payment_id.state')
    # def _compute_amount(self):
    #     invoice_ids = [move.id for move in self if move.id and move.is_invoice(include_receipts=True)]
    #     self.env['account.payment'].flush(['state'])
    #     if invoice_ids:
    #         self._cr.execute(
    #             '''
    #                 SELECT move.id
    #                 FROM account_move move
    #                 JOIN account_move_line line ON line.move_id = move.id
    #                 JOIN account_partial_reconcile part ON part.debit_move_id = line.id OR part.credit_move_id = line.id
    #                 JOIN account_move_line rec_line ON
    #                     (rec_line.id = part.credit_move_id AND line.id = part.debit_move_id)
    #                     OR
    #                     (rec_line.id = part.debit_move_id AND line.id = part.credit_move_id)
    #                 JOIN account_payment payment ON payment.id = rec_line.payment_id
    #                 JOIN account_journal journal ON journal.id = rec_line.journal_id
    #                 WHERE payment.state IN ('posted', 'sent')
    #                 AND journal.post_at = 'bank_rec'
    #                 AND move.id IN %s
    #             ''', [tuple(invoice_ids)]
    #         )
    #         in_payment_set = set(res[0] for res in self._cr.fetchall())
    #     else:
    #         in_payment_set = {}
    #
    #     for move in self:
    #         total_untaxed = 0.0
    #         total_untaxed_currency = 0.0
    #         total_tax = 0.0
    #         total_tax_currency = 0.0
    #         total_residual = 0.0
    #         total_residual_currency = 0.0
    #         total = 0.0
    #         total_currency = 0.0
    #         currencies = set()
    #
    #         for line in move.line_ids:
    #             if line.currency_id:
    #                 currencies.add(line.currency_id)
    #
    #             if move.is_invoice(include_receipts=True):
    #                 # === Invoices ===
    #
    #                 if not line.exclude_from_invoice_tab:
    #                     # Untaxed amount.
    #                     total_untaxed += line.balance
    #                     total_untaxed_currency += line.amount_currency
    #                     total += line.balance
    #                     total_currency += line.amount_currency
    #                 elif line.tax_line_id:
    #                     # Tax amount.
    #                     total_tax += line.balance
    #                     total_tax_currency += line.amount_currency
    #                     total += line.balance
    #                     total_currency += line.amount_currency
    #                 elif line.account_id.user_type_id.type in ('receivable', 'payable'):
    #                     # Residual amount.
    #                     total_residual += line.amount_residual
    #                     total_residual_currency += line.amount_residual_currency
    #             else:
    #                 # === Miscellaneous journal entry ===
    #                 if line.debit:
    #                     total += line.balance
    #                     total_currency += line.amount_currency
    #
    #         if move.type == 'entry' or move.is_outbound():
    #             sign = 1
    #         else:
    #             sign = -1
    #         move.amount_untaxed = sign * (total_untaxed_currency if len(currencies) == 1 else total_untaxed)
    #         move.amount_tax = sign * (total_tax_currency if len(currencies) == 1 else total_tax)
    #         move.amount_total = sign * (total_currency if len(currencies) == 1 else total)
    #         if move.purchase_type == "unfixed" or move.sale_type == "unfixed":
    #             if  move.make_value_move == 0.00 and move.pure_wt_value <= 0.00:
    #                 move.amount_residual = 0.00
    #             else:
    #                 move.amount_residual = -sign * (total_residual_currency if len(currencies) == 1 else total_residual)
    #         else:
    #             move.amount_residual = -sign * (total_residual_currency if len(currencies) == 1 else total_residual)
    #
    #         move.amount_untaxed_signed = -total_untaxed
    #         move.amount_tax_signed = -total_tax
    #         move.amount_total_signed = abs(total) if move.type == 'entry' else -total
    #         move.amount_residual_signed = total_residual
    #
    #         currency = len(currencies) == 1 and currencies.pop() or move.company_id.currency_id
    #         is_paid = currency and currency.is_zero(move.amount_residual) or not move.amount_residual
    #
    #         # Compute 'invoice_payment_state'.
    #         if move.type == 'entry':
    #             move.invoice_payment_state = False
    #         elif move.state == 'posted' and is_paid:
    #             if move.id in in_payment_set:
    #                 move.invoice_payment_state = 'in_payment'
    #             else:
    #                 move.invoice_payment_state = 'paid'
    #         else:
    #             move.invoice_payment_state = 'not_paid'



    # @api.depends('invoice_line_ids')
    # def _compute_make_value_move(self):
    #     for rec in self:
    #         if rec.purchase_type == "unfixed" or rec.sale_type == "unfixed":
    #             make_value = 0.00
    #             pure = 0.00
    #             rate = 0.00
    #             for line in rec.invoice_line_ids:
    #                 if line.pure_wt == 0.00 and line.make_value == 0.00:
    #                     make_value = line.price_unit
    #                 else:
    #                     pure = line.pure_wt + line.purity_diff
    #                     rate = line.gold_rate
    #
    #             rec.pure_wt_value = pure
    #             rec.gold_rate_value = rate
    #
    #             if rec.amount_by_group:
    #                 rec.make_value_move = make_value + rec.amount_by_group[0][1]
    #             else:
    #                 rec.make_value_move = make_value

    # def button_draft(self):
    #     res = super(AccountMove, self).button_draft()
    #     po_id = self.is_po_related()
    #     if po_id:
    #         po_id.bill_move_id.write({'state': 'draft'})
    #     so_id = self.is_so_related()
    #     if so_id:
    #         so_id.inv_move_id.write({'state': 'draft'})
    #     return res
    #
    # def post(self):
    #     po_id = self.is_po_related()
    #     if po_id:
    #         if not po_id.bill_move_id:
    #             self.create_gold_journal_entry(po_id)
    #         elif po_id.bill_move_id:
    #             if po_id.bill_move_id.state == "draft":
    #                 po_id.bill_move_id.action_post()
    #     so_id = self.is_so_related()
    #     if so_id:
    #         if not so_id.inv_move_id:
    #             self.create_gold_journal_entry(so_id)
    #         elif so_id.inv_move_id:
    #             if so_id.inv_move_id.state == "draft":
    #                 so_id.inv_move_id.action_post()
    #
    #     for move in self:
    #         if not move.line_ids.filtered(lambda line: not line.display_type):
    #             raise UserError(_('You need to add a line before posting.'))
    #         if move.auto_post and move.date > fields.Date.today():
    #             date_msg = move.date.strftime(get_lang(self.env).date_format)
    #             raise UserError(_("This move is configured to be auto-posted on %s" % date_msg))
    #
    #         if not move.partner_id:
    #             if move.is_sale_document():
    #                 raise UserError(_("The field 'Customer' is required, please complete it to validate the Customer Invoice."))
    #             elif move.is_purchase_document():
    #                 raise UserError(_("The field 'Vendor' is required, please complete it to validate the Vendor Bill."))
    #
    #         if move.is_invoice(include_receipts=True) and float_compare(move.amount_total, 0.0, precision_rounding=move.currency_id.rounding) < 0:
    #             raise UserError(_("You cannot validate an invoice with a negative total amount. You should create a credit note instead. Use the action menu to transform it into a credit note or refund."))
    #
    #         # Handle case when the invoice_date is not set. In that case, the invoice_date is set at today and then,
    #         # lines are recomputed accordingly.
    #         # /!\ 'check_move_validity' must be there since the dynamic lines will be recomputed outside the 'onchange'
    #         # environment.
    #         if not move.invoice_date and move.is_invoice(include_receipts=True):
    #             move.invoice_date = fields.Date.context_today(self)
    #             move.with_context(check_move_validity=False)._onchange_invoice_date()
    #
    #         # When the accounting date is prior to the tax lock date, move it automatically to the next available date.
    #         # /!\ 'check_move_validity' must be there since the dynamic lines will be recomputed outside the 'onchange'
    #         # environment.
    #         if (move.company_id.tax_lock_date and move.date <= move.company_id.tax_lock_date) and (move.line_ids.tax_ids or move.line_ids.tag_ids):
    #             move.date = move.company_id.tax_lock_date + timedelta(days=1)
    #             move.with_context(check_move_validity=False)._onchange_currency()
    #
    #     # Create the analytic lines in batch is faster as it leads to less cache invalidation.
    #     self.mapped('line_ids').create_analytic_lines()
    #     for move in self:
    #         if move.auto_post and move.date > fields.Date.today():
    #             raise UserError(_("This move is configured to be auto-posted on {}".format(move.date.strftime(get_lang(self.env).date_format))))
    #
    #         move.message_subscribe([p.id for p in [move.partner_id] if p not in move.sudo().message_partner_ids])
    #
    #         to_write = {'state': 'posted'}
    #
    #         if move.name == '/':
    #             # Get the journal's sequence.
    #             sequence = move._get_sequence()
    #             if not sequence:
    #                 raise UserError(_('Please define a sequence on your journal.'))
    #
    #             # Consume a new number.
    #             to_write['name'] = sequence.next_by_id(sequence_date=move.date)
    #
    #         move.write(to_write)
    #
    #         # Compute 'ref' for 'out_invoice'.
    #         if move.type == 'out_invoice' and not move.invoice_payment_ref:
    #             to_write = {
    #                 'invoice_payment_ref': move._get_invoice_computed_reference(),
    #                 'line_ids': []
    #             }
    #             for line in move.line_ids.filtered(lambda line: line.account_id.user_type_id.type in ('receivable', 'payable')):
    #                 to_write['line_ids'].append((1, line.id, {'name': to_write['invoice_payment_ref']}))
    #             move.write(to_write)
    #
    #         if move == move.company_id.account_opening_move_id and not move.company_id.account_bank_reconciliation_start:
    #             # For opening moves, we set the reconciliation date threshold
    #             # to the move's date if it wasn't already set (we don't want
    #             # to have to reconcile all the older payments -made before
    #             # installing Accounting- with bank statements)
    #             move.company_id.account_bank_reconciliation_start = move.date
    #
    #     po_id = self.is_po_related()
    #     if po_id:
    #         po_id.bill_move_id.write({'ref':move.name})
    #
    #     so_id = self.is_so_related()
    #     if so_id:
    #         so_id.inv_move_id.write({'ref':move.name})
    #
    #     for move in self:
    #         if not move.partner_id: continue
    #         if move.type.startswith('out_'):
    #             move.partner_id._increase_rank('customer_rank')
    #         elif move.type.startswith('in_'):
    #             move.partner_id._increase_rank('supplier_rank')
    #         else:
    #             continue
    #
    #     # Trigger action for paid invoices in amount is zero
    #     self.filtered(
    #         lambda m: m.is_invoice(include_receipts=True) and m.currency_id.is_zero(m.amount_total)
    #     ).action_invoice_paid()
    #
    #
    #
    #
    # def is_so_related(self):
    #     '''
    #     find's related purchase order, if found check for order type = fixed
    #     :return: if order type == fixed return po else false
    #     '''
    #     so_id = self.env['sale.order'].search(
    #         [('invoice_ids', '=', self.id)])
    #     if so_id and so_id.order_type.is_fixed or so_id.order_type.is_unfixed:
    #         return so_id
    #     return False
    #
    # def create_gold_journal_entry(self, po_id):
    #     self.ensure_one()
    #     moves = self.invoice_line_ids.filtered(lambda x: x.product_id and
    #                                                      x.product_id.gold and
    #                                                      x.product_id.categ_id and
    #                                                      x.product_id.categ_id.is_gold and
    #                                                      x.product_id.categ_id.gold_expense_account)
    #     if moves:
    #         total_purity = 0
    #         product_dict = {}
    #         description =  self.name
    #         for product_id, move_list in groupby(moves, lambda x: x.product_id):
    #             if product_id not in product_dict.keys():
    #                 product_dict[product_id] = sum(
    #                     x.pure_wt for x in move_list)
    #             else:
    #                 product_dict[product_id] = product_dict[product_id] + sum(
    #                     x.pure_wt for x in move_list)
    #         total_purity = sum(value for key, value in product_dict.items())
    #         if not  self.partner_id.gold_account_payable_id:
    #                 raise ValidationError(_('Please fill gold payable account for the partner'))
    #         if not  self.partner_id.gold_account_receivable_id:
    #                 raise ValidationError(_('Please fill gold receivable account for the partner'))
    #         sale_temp = self.env['sale.order']
    #         purchase_temp = self.env['purchase.order']
    #         if type(po_id) == type(purchase_temp):
    #             if total_purity > 0.0 and product_dict and \
    #                     self.partner_id and self.partner_id.gold_account_payable_id:
    #                 if not next(iter(product_dict)).categ_id.gold_purchase_journal.id:
    #                     raise ValidationError(_('Please fill gold purchase journal in product Category'))
    #                 journal_id = next(iter(product_dict)).categ_id.gold_purchase_journal.id
    #
    #                 move_lines = self._prepare_account_move_line(product_dict, po_id)
    #                 if move_lines:
    #                     AccountMove = self.with_context(default_type='entry',
    #                         default_journal_id=journal_id)
    #                     date = self._context.get('force_period_date',
    #                                              fields.Date.context_today(self))
    #                     new_account_move = AccountMove.sudo().create({
    #                         'journal_id': journal_id,
    #                         'line_ids': move_lines,
    #                         'date': date,
    #                         'ref': description,
    #                         'type': 'entry'
    #                     })
    #                     new_account_move.post()
    #                     print ('----------------------', new_account_move)
    #                     po_id.write({'bill_move_id': new_account_move.id})
    #         if type(po_id) == type(sale_temp):
    #             if total_purity > 0.0 and product_dict and \
    #                         self.partner_id and self.partner_id.gold_account_receivable_id:
    #                 if not next(iter(product_dict)).categ_id.gold_sale_journal.id:
    #                     raise ValidationError(_('Please fill gold sale journal in product Category'))
    #                 journal_id = next(iter(product_dict)).categ_id.gold_sale_journal.id
    #
    #                 move_lines = self._prepare_account_move_line(product_dict, po_id)
    #                 if move_lines:
    #                     AccountMove = self.with_context(default_type='entry',
    #                         default_journal_id=journal_id)
    #                     date = self._context.get('force_period_date',
    #                                              fields.Date.context_today(self))
    #                     new_account_move = AccountMove.sudo().create({
    #                         'journal_id': journal_id,
    #                         'line_ids': move_lines,
    #                         'date': date,
    #                         'ref': description,
    #                         'type': 'entry'
    #                     })
    #                     new_account_move.post()
    #                     print ('----------------------', new_account_move)
    #                     po_id.write({'inv_move_id': new_account_move.id})
    #
    # def _prepare_account_move_line(self, product_dict, po_id):
    #     sale_temp = self.env['sale.order']
    #     purchase_temp = self.env['purchase.order']
    #     if type(po_id) == type(purchase_temp):
    #         debit_lines = []
    #         for product_id, value in product_dict.items():
    #             debit_lines.append({
    #                 'name': '%s - %s' % (po_id.name, product_id.name),
    #                 'product_id': product_id.id,
    #                 'quantity': 1,
    #                 'product_uom_id': product_id.uom_id.id,
    #                 'ref': '%s - %s' % (po_id.name, product_id.name),
    #                 'partner_id': self.partner_id.id,
    #                 'debit': round(value, 3),
    #                 'credit': 0,
    #                 'account_id': product_id.categ_id.gold_expense_account.id,
    #             })
    #         credit_line = [{
    #             'name': '%s - %s' % (po_id.name, product_id.name),
    #             'product_id': product_id.id,
    #             'quantity': 1,
    #             'product_uom_id': product_id.uom_id.id,
    #             'ref': '%s - %s' % (po_id.name, product_id.name),
    #             'partner_id': self.partner_id.id,
    #             'debit': 0,
    #             'credit': sum(x['debit'] for x in debit_lines),
    #             'account_id': self.partner_id.gold_account_payable_id.id,
    #         }]
    #         res = [(0, 0, x) for x in debit_lines + credit_line]
    #         return res
    #     elif type(po_id) == type(sale_temp):
    #         credit_lines = []
    #         for product_id, value in product_dict.items():
    #             credit_lines.append({
    #                 'name': '%s - %s' % (po_id.name, product_id.name),
    #                 'product_id': product_id.id,
    #                 'quantity': 1,
    #                 'product_uom_id': product_id.uom_id.id,
    #                 'ref': '%s - %s' % (po_id.name, product_id.name),
    #                 'partner_id': self.partner_id.id,
    #                 'debit': 0,
    #                 'credit': round(value, 3),
    #                 'account_id': self.partner_id.gold_account_receivable_id.id,
    #             })
    #         debit_line = [{
    #             'name': '%s - %s' % (po_id.name, product_id.name),
    #             'product_id': product_id.id,
    #             'quantity': 1,
    #             'product_uom_id': product_id.uom_id.id,
    #             'ref': '%s - %s' % (po_id.name, product_id.name),
    #             'partner_id': self.partner_id.id,
    #             'debit': sum(x['credit'] for x in credit_lines),
    #             'credit': 0,
    #             'account_id': product_id.categ_id.gold_expense_account.id,
    #         }]
    #         res = [(0, 0, x) for x in credit_lines + debit_line]
    #         return res

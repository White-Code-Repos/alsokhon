# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, timedelta, date
from odoo.exceptions import ValidationError
from odoo.tools.translate import _
from odoo.tools import config


class CheckPortfolio(models.Model):
    _name = 'check.portfolio'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _rec_name = 'name'
    _description = 'Check Portfolio'

    name = fields.Char(string='Name')
    journal_id = fields.Many2one(comodel_name="account.journal", string="Journal", required=False)
    bank_id = fields.Many2one(comodel_name="res.bank", string="Bank", related='journal_id.bank_id',
                              required=False)
    date = fields.Date(string="Date", required=False)
    notes = fields.Text(string="Notes", required=False)
    portfolio_line_ids = fields.One2many(comodel_name="check.portfolio.lines", inverse_name="portfolio_id",
                                         required=True)
    state = fields.Selection(string="State", default='draft',
                             selection=[('draft', 'Draft'), ('inprogress', 'In Progress'), ('closed', 'Closed'),
                                        ('cancel', 'Cancel')], required=False)
    is_deposit = fields.Boolean()
    is_depit = fields.Boolean()
    inbank_account_id = fields.Many2one(comodel_name="account.account", string="InBank Account",
                                        required=False, readonly=1)

    @api.model
    def create(self, values):
        values['name'] = self.env['ir.sequence'].next_by_code('check.portfolio')
        rec = super(CheckPortfolio, self).create(values)
        if not rec.portfolio_line_ids:
            raise ValidationError(_('Please Select Check First.'))
        else:
            for line in rec.portfolio_line_ids:
                line.check_id.portfolio_id = rec.id
        return rec

    def write(self, values):
        rec = super(CheckPortfolio, self).write(values)
        if not self.portfolio_line_ids:
            raise ValidationError(_('Please Select Check First.'))
        return rec

    def return_to_treasury(self):
        self.state = 'draft'
        self.is_deposit = False
        for check in self.portfolio_line_ids:
            if check.check_id.state == 'handed':
                check.check_id.change_state()
            elif check.check_id.state == 'inbank':
                check.check_id.return_to_treasury()

    def set_to_draft(self):
        self.write({'state': 'draft'})

    def set_to_cancel(self):
        self.write({'state': 'cancel'})
        for check in self.portfolio_line_ids:
            check.check_id.portfolio_id = False
            check.check_id.portfolio_id = False
            if check.check_id.state == 'handed':
                check.check_id.change_state()
            elif check.check_id.state == 'inbank':
                check.check_id.return_to_treasury()

    # Change states of all lines ro handed
    def hand_check_change_state(self):
        self.state = 'inprogress'
        for check in self.portfolio_line_ids:
            check.check_id.change_state_handed()

    def open_wizard_inbank_check_portfolio(self):
        action = self.env.ref('account_check.action_wizard_inbank')
        result = action.read()[0]
        res = self.env.ref('account_check.check_action_inbank_form_view', False)
        result['views'] = [(res and res.id or False, 'form')]
        result['target'] = 'new'
        result['context'] = {'default_action_type': 'inbank', 'default_journal_id': self.journal_id.id,
                             'default_portfolio': True, 'default_portfolio_id': self.id,
                             'default_check_ids': [(6, 0, [check.check_id.id for check in self.portfolio_line_ids])]}
        return result

    def bank_debit_action_portfolio(self):
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
        result['context'] = {'default_action_type': 'bank_debit', 'default_portfolio_id': self.id,
                             'default_portfolio': True,
                             'default_inbank_account_id': self.inbank_account_id.id if self.inbank_account_id else False,
                             'default_check_ids': [(6, 0, [check.check_id.id for check in self.portfolio_line_ids])]}
        return result


class CheckPortfolioLines(models.Model):
    _name = 'check.portfolio.lines'

    check_id = fields.Many2one(comodel_name="account.check", string="", required=False,
                               domain=[('type', '=', 'third_check')])
    check_number = fields.Char(string="number", related='check_id.number', required=False)
    company_id = fields.Many2one(related='check_id.company_id', readonly=True, store=True)
    company_currency_id = fields.Many2one(related='check_id.company_id.currency_id', readonly=True)
    amount = fields.Monetary(string="", currency_field='company_currency_id', related='check_id.amount',
                             required=False)
    payment_date = fields.Date(string="Payment Date", related='check_id.payment_date',
                               required=False)
    partner_id = fields.Many2one(comodel_name="res.partner", related='check_id.partner_id',
                                 string="Customer", required=False)
    state = fields.Selection(string="Status", related='check_id.state', required=False)
    type = fields.Selection(string="Type", related='check_id.type', required=False)

    # Relation Field
    portfolio_id = fields.Many2one(comodel_name="check.portfolio", required=False)

    def return_to_treasury(self):
        for check in self:
            check.check_id.change_state()
            check.unlink()

    # Use in Check Portfolio
    def return_to_treasury_debosit(self):
        for check in self:
            check.check_id.return_to_treasury()
            check.check_id.change_state()
            check.unlink()

    @api.onchange('check_id')
    def get_check(self):
        ids = self.env['account.check'].sudo().search([('portfolio_id', '=', False), ('state', '=', 'holding')])
        # ('journal_id', '=', self.portfolio_id.journal_id.id)
        return {'domain': {'check_id': [('id', 'in', ids.ids),
                                        ('id', 'not in', self.portfolio_id.portfolio_line_ids.mapped('check_id').ids)]}}

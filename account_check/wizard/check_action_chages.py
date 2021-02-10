# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import Warning, ValidationError


class AccountCheckActionInBank(models.TransientModel):
    _name = 'account_check_action'

    @api.model
    def _get_company_id(self):
        active_ids = self._context.get('active_ids', [])
        checks = self.env['account.check'].browse(active_ids)
        company_ids = [x.company_id.id for x in checks]
        if len(set(company_ids)) > 1:
            raise Warning(_('All checks must be from the same company!'))
        return self.env['res.company'].search(
            [('id', 'in', company_ids)], limit=1)

    journal_id = fields.Many2one(
        'account.journal',
        'Journal',
        domain="[('company_id','=',company_id),('type', 'in', ['cash', 'bank', 'general'])]")

    account_id = fields.Many2one(
        'account.account',
        'Account',
        domain="[('company_id','=',company_id),]",
        default=lambda item: item.get_default_account_id())

    debited_account_id = fields.Many2one(
        'account.account',
        'Debited Account',
        domain="[('company_id','=',company_id),]")

    date = fields.Date(
        'Date', required=True, default=fields.Date.context_today
    )
    action_type = fields.Char(
        'Action type passed on the context', required=True
    )
    company_id = fields.Many2one(
        'res.company',
        'Company',
        required=True,
        default=_get_company_id
    )
    inbank_account_id = fields.Many2one('account.account', string='In Bank Account')
    partner_id = fields.Many2one('res.partner', string='Partner')

    sequence = fields.Char(default=lambda item: item.get_default_sequence(), copy=False)

    # Portfolio
    check_ids = fields.Many2many(comodel_name="account.check", relation="check_ids")
    portfolio = fields.Boolean()
    portfolio_id = fields.Many2one(comodel_name="check.portfolio", required=False)

    @api.model
    def validate_inbank_action_port(self, action_type, check):
        inbank_account_id = False
        name = ''
        if not check.journal_id.default_debit_account_id:
            raise ValidationError(
                _('You must selected default debit account on this check Journal.'))

        if action_type == 'inbank':
            if check.type == 'third_check':
                if check.state != 'handed':
                    raise ValidationError(
                        _('The selected checks must be in Handed state.'))

                # Filling data of move vals and lines
                type = 'inbank'
                credit_account = check.journal_id.holding_check_account_id
                debit_account = self.account_id
                name = _('Check "%s" deposited "%s"') % (check.name, self.sequence)
                inbank_account_id = self.account_id

            else:  # issue
                raise ValidationError(_('You can not inbank an Issue Check.'))

        elif action_type == 'bank_debit':
            if check.type == 'third_check':
                if check.state != 'inbank':
                    raise ValidationError(
                        _('The selected checks must be in Inbank state.'))

                # Filling data of move vals and lines

                type = "debited"
                debit_account = self.journal_id.default_debit_account_id
                credit_account = check.journal_id.under_collection_check_account_id
                name = _('Check "%s" debit') % (check.name)
            else:  # third
                raise ValidationError(_('You can not debit an Issue Check.'))

        elif action_type == 'returned':
            if check.type == 'third_check':
                if check.state != 'inbank':
                    raise ValidationError(
                        _('The selected checks must be in bank state.'))
                # TODO implement return issue checks and return handed third checks
                type = "returned"
                debit_account = self.account_id
                credit_account = self.inbank_account_id
                name = _('Check "%s" returned') % (check.name)
            else:  # issue
                raise ValidationError(_('You can not return an Issue Check.'))

        elif action_type == 'rejected':
            if check.type == 'third_check':
                if not check.operation_ids:
                    raise ValidationError('You need to make payment first')
                payment_id = self.env['account.payment'].search([('name', '=', check.operation_ids[-1].origin_name)])
                type = "rejected"
                debit_account = self.env['account.move.line'].search(
                    [('payment_id', '=', payment_id.id), ('credit', '!=', 0.0)], limit=1).account_id
                credit_account = self.env['account.move.line'].search(
                    [('payment_id', '=', payment_id.id), ('debit', '!=', 0.0)], limit=1).account_id
                name = _('Check "%s" rejected') % (check.name)
            else:  # issue
                raise ValidationError(_('You can not reject an Issue Check.'))

        debit_line_vals = {
            'name': name,
            'account_id': debit_account.id,
            'debit': check.amount,
            'amount_currency': check.amount_currency,
            'partner_id': check.partner_id and check.partner_id.id or False
        }
        credit_line_vals = {
            'name': name,
            'account_id': credit_account.id,
            'credit': check.amount,
            'amount_currency': check.amount_currency,
            'partner_id': check.partner_id and check.partner_id.id or False
        }
        move_vals = {
            'name': name,
            'journal_id': check.journal_id.id,
            'date': self.date,
            'ref': name,
            'partner_id': self.partner_id.id,
            'move_check_id': check.id,
            'line_ids': [
                (0, False, debit_line_vals),
                (0, False, credit_line_vals)]
        }
        return {
            'type': type,
            'move_vals': move_vals,
            'inbank_account_id': inbank_account_id}

    def action_confirm_portfolio(self):
        """
        confirm choosen account wizard to create this state move
        :return: True
        """
        # used to get correct ir properties
        self = self.with_context(
            company_id=self.company_id.id,
            force_company=self.company_id.id,
        )
        portfolio = self.env['check.portfolio'].search([('id', '=', self.portfolio_id.id)])
        for c in self.check_ids:
            for check in self.env['account.check'].search([('id', '=', c.id)]):
                # validate check and get move vals
                vals = self.validate_inbank_action_port(self.action_type, check)
                type = vals.get('type', {})
                check.write({'state': type})
                inbank_account_id = vals.get('inbank_account_id')
                move_vals = vals.get('move_vals')
                move = self.env['account.move'].with_context({}).create(move_vals)
                move.post()

                if inbank_account_id:
                    check.write({'inbank_account_id': inbank_account_id.id})
                    portfolio.write({'inbank_account_id': inbank_account_id.id})

                # add operation with move ref
                check._add_operation(type, move, partner=check.partner_id, date=self.date)
        if not self.portfolio_id.is_deposit:
            self.portfolio_id.is_deposit = True

        if self.action_type == 'bank_debit':
            if not self.portfolio_id.is_depit:
                self.portfolio_id.is_depit = True
                self.portfolio_id.state = 'closed'

        return True

    @api.onchange('journal_id')
    def onchange_journal_id(self):
        """
        on choosing journal get his default debit account as choosen account
        :return:
        """
        self.debited_account_id = self.journal_id.default_debit_account_id.id

    def get_default_account_id(self):
        vals = {}
        check = self.env['account.check'].browse(self._context.get('active_id'))
        vals['account_id'] = check.journal_id.under_collection_check_account_id.id
        return vals['account_id']

    def get_default_sequence(self):
        vals = {}
        vals['sequence'] = self.env['ir.sequence'].next_by_code('account_check_action')
        return vals['sequence']

    @api.model
    def validate_inbank_action(self, action_type, check):
        """
        validating check vals and state
        :param action_type:
        :param check:
        :return: move vals , type , inbank_account if exist
        """
        inbank_account_id = False
        if not check.journal_id.default_debit_account_id:
            raise Warning(
                _('You must selected default debit account on this check Journal.'))

        if action_type == 'inbank':
            if check.type == 'third_check':
                if check.state != 'handed':
                    raise Warning(
                        _('The selected checks must be in Handed state.'))

                # Filling data of move vals and lines
                type = 'inbank'
                credit_account = check.journal_id.holding_check_account_id
                debit_account = self.account_id
                name = _('Check "%s" deposited "%s"') % (check.name, self.sequence)
                inbank_account_id = self.account_id

            else:  # issue
                raise Warning(_('You can not inbank an Issue Check.'))

        elif action_type == 'bank_debit':
            if check.type == 'third_check':
                if check.state != 'inbank':
                    raise Warning(
                        _('The selected checks must be in Inbank state.'))

                # Filling data of move vals and lines
                type = "debited"
                debit_account = self.journal_id.default_debit_account_id
                credit_account = check.journal_id.under_collection_check_account_id
                name = _('Check "%s" debit') % (check.name)
            else:  # third
                raise Warning(_('You can not debit an Issue Check.'))

        elif action_type == 'returned':
            if check.type == 'third_check':
                if check.state != 'inbank':
                    raise Warning(
                        _('The selected checks must be in bank state.'))
                # TODO implement return issue checks and return handed third checks
                type = "returned"
                debit_account = self.account_id
                credit_account = self.inbank_account_id
                name = _('Check "%s" returned') % (check.name)
            else:  # issue
                raise Warning(_('You can not return an Issue Check.'))

        elif action_type == 'rejected':
            if check.type == 'third_check':
                if not check.operation_ids:
                    raise Warning('You need to make payment first')
                payment_id = self.env['account.payment'].search([('name', '=', check.operation_ids[-1].origin_name)])
                type = "rejected"
                debit_account = self.env['account.move.line'].search(
                    [('payment_id', '=', payment_id.id), ('credit', '!=', 0.0)], limit=1).account_id
                credit_account = self.env['account.move.line'].search(
                    [('payment_id', '=', payment_id.id), ('debit', '!=', 0.0)], limit=1).account_id
                name = _('Check "%s" rejected') % (check.name)
            else:  # issue
                raise Warning(_('You can not reject an Issue Check.'))

        debit_line_vals = {
            'name': name,
            'account_id': debit_account.id,
            'debit': check.amount,
            'amount_currency': check.amount_currency,
            'partner_id': check.partner_id and check.partner_id.id or False
        }
        credit_line_vals = {
            'name': name,
            'account_id': credit_account.id,
            'credit': check.amount,
            'amount_currency': check.amount_currency,
            'partner_id': check.partner_id and check.partner_id.id or False
        }
        move_vals = {
            'name': name,
            'journal_id': check.journal_id.id,
            'date': self.date,
            'ref': name,
            'partner_id': self.partner_id.id,
            'move_check_id': check.id,
            'line_ids': [
                (0, False, debit_line_vals),
                (0, False, credit_line_vals)]
        }
        return {
            'type': type,
            'move_vals': move_vals,
            'inbank_account_id': inbank_account_id}

    def action_confirm(self):
        """
        confirm choosen account wizard to create this state move
        :return: True
        """
        # used to get correct ir properties
        self = self.with_context(
            company_id=self.company_id.id,
            force_company=self.company_id.id,
        )

        for check in self.env['account.check'].browse(
                self._context.get('active_ids', [])):

            # validate check and get move vals
            vals = self.validate_inbank_action(self.action_type, check)
            type = vals.get('type', {})
            check.write({'state': type})
            inbank_account_id = vals.get('inbank_account_id')
            move_vals = vals.get('move_vals')
            move = self.env['account.move'].with_context({}).create(move_vals)
            move.post()

            if inbank_account_id:
                check.write({'inbank_account_id': inbank_account_id.id})

            # add operation with move ref
            check._add_operation(type, move, partner=check.partner_id, date=self.date)
        return True

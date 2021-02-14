# -*- coding: utf-8 -*-
import logging

from odoo import fields, models, _, api
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class AccountCheckbook(models.Model):
    _name = 'account.checkbook'
    _description = 'Account Checkbook'

    name = fields.Char(
        compute='_compute_name',
    )
    sequence_id = fields.Many2one(
        'ir.sequence',
        'Sequence',
        readonly=True,
        copy=False,
        domain=[('code', '=', 'issue_check')],
        help="Checks numbering sequence.",
        context={'default_code': 'issue_check'}
    )
    next_number = fields.Integer(
        'Next Number',
        related='sequence_id.number_next_actual',
    )
    issue_check_subtype = fields.Selection(
        [('deferred', 'Deferred'), ('currents', 'Currents')],
        string='Issue Check Subtype',
        readonly=True,
        required=True,
        default='deferred',
        help='The only difference bewteen Deferred and Currents is that when '
             'delivering a Deferred check a Payment Date is Require',
        states={'draft': [('readonly', False)]}
    )

    journal_id = fields.Many2one(
        'account.journal', 'Journal',
        help='Journal where it is going to be used',
        readonly=True,
        required=True,
        domain=[('type', '=', 'bank')],
        ondelete='cascade',
        context={'default_type': 'bank'},
        states={'draft': [('readonly', False)]}
    )
    range_from = fields.Integer(
        'From Number',
        readonly=True,
        states={'draft': [('readonly', False)]},
        help='If you set a number here, this checkbook will be automatically'
             ' set as used when this number is set.'
    )
    range_to = fields.Integer(
        'To Number',
        readonly=True,
        states={'draft': [('readonly', False)]},
        help='If you set a number here, this checkbook will be automatically'
             ' set as used when this number is raised.'
    )
    issue_check_ids = fields.One2many(
        'account.check',
        'checkbook_id',
        string='Issue Checks',
        readonly=True,
    )
    state = fields.Selection(
        [('draft', 'Draft'), ('active', 'In Use'), ('used', 'Used')],
        string='State',
        default='draft',
        copy=False
    )
    block_manual_number = fields.Boolean(
        readonly=True,
        default=True,
        string='Block manual number?',
        states={'draft': [('readonly', False)]},
        help='Block user to enter manually another number than the suggested'
    )

    sequence_ids = fields.One2many(comodel_name='checkbook.sequence',
                                   inverse_name='checkbook_sequence',
                                   string='Checkbook Sequence', readonly=True)

    sequence_prefix = fields.Char(string='Prefix',
                                  states={'active': [('readonly', True)],
                                          'used': [('readonly', True)]})
    digit_number = fields.Integer(string='Digit Number', states={'active': [('readonly', True)],
                                                                 'used': [('readonly', True)]})

    # # need to be reviewed if it is effective of checkbook sequence or not
    @api.model
    def create(self, vals):
        padding, no_of_padding, no_of_increment = 0, 0, 0
        rec = super(AccountCheckbook, self).create(vals)
        rec.sequence_id = self.env['ir.sequence'].sudo().create({
            'name': '%s - %s' % (rec.journal_id.name, rec.name),
            'prefix': rec.sequence_prefix,
            'implementation': 'no_gap',
            'padding': rec.digit_number,
            'number_increment': 1,
            'code': 'issue_check',
            'company_id': rec.journal_id.company_id.id,
        })

        for n in range(rec.sequence_id.padding):
            no_of_padding += n

        for i in range(rec.range_from, rec.range_to + 1):
            padding = (no_of_padding - len(str(abs(i)))) * '0'
            vals = {
                'name': str(rec.sequence_id.prefix) + str(padding) + str(i),
                'state': 'draft'
            }
            rec.sequence_ids = [(0, 0, vals)]
        return rec

    # def _create_sequence(self):
    #     """ Create a check sequence for the checkbook """
    #     self.sequence_id = self.env['ir.sequence'].sudo().create({
    #         'name': '%s - %s' % (self.journal_id.name, self.name),
    #         'implementation': 'no_gap',
    #         'padding': 2,
    #         'number_increment': 1,
    #         'code': 'issue_check',
    #         'company_id': self.journal_id.company_id.id,
    #     })

    def _compute_name(self):
        for rec in self:
            if rec.issue_check_subtype == 'deferred':
                name = _('Deferred Checks')
            else:
                name = _('Currents Checks')
            if rec.range_to:
                name += _(' up to %s') % rec.range_to
            rec.name = name

    def unlink(self):
        if self.issue_check_ids:
            raise ValidationError(
                _('You can drop a checkbook if it has been used on checks!'))
        return super(AccountCheckbook, self).unlink()


class CheckBooksSequence(models.Model):
    _name = 'checkbook.sequence'

    name = fields.Char(string='Checkbook Number')
    state = fields.Selection(selection=[('draft', 'Draft'), ('issued', 'Issued'), ('cancel', 'Cancelled')]
                             , default='draft', string='Status')

    checkbook_sequence = fields.Many2one(comodel_name='account.checkbook')

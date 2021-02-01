""" init object gold.position """

from odoo import fields, models, api, _, tools, SUPERUSER_ID
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, date, timedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT as DTF
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DF
from dateutil.relativedelta import relativedelta
from odoo.fields import Datetime as fieldsDatetime
import calendar
from odoo import http
from odoo.http import request
from odoo import tools

import logging

LOGGER = logging.getLogger(__name__)


class GoldPosition(models.Model):
    """ init object gold.position """
    _name = 'gold.position'
    _description = 'gold.position'

    def _compute_value(self):
        """
        Compute Value
        """
        for rec in self:
            gold_capital = 0
            current_position = 0
            gold_capital_id = self.env['gold.capital'].sudo().search(
                [], limit=1)
            if gold_capital_id:
                gold_capital = gold_capital_id.capital
            account = self.env['account.account'].search(
                [('current_position', '=', True)])
            if account:
                debit = credit = 0.0
                for line in self.env['account.move.line'].search(
                        [('account_id', '=', account.id),
                         ('move_id.state', '=', 'posted'),
                         ('move_id.type_of_action', '=', 'fixed')]):
                    if line.debit:
                        debit += abs(line.debit)
                    elif line.credit:
                        credit += abs(line.credit)
                current_position = debit - credit
            rec.gold_capital = gold_capital
            rec.current_position = current_position
            rec.capital_difference = gold_capital - current_position

    name = fields.Char()
    gold_capital = fields.Float(compute=_compute_value)
    current_position = fields.Float(compute=_compute_value)
    capital_difference = fields.Float(compute=_compute_value)

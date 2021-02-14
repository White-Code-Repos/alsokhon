# -*- coding: utf-8 -*-

from odoo import fields, models, api, _ , tools
from odoo.exceptions import Warning
from odoo.exceptions import RedirectWarning, UserError, ValidationError
import random
import psycopg2
import base64
from odoo.http import request
from functools import partial
from odoo.tools import float_is_zero

from datetime import date, datetime
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT, DEFAULT_SERVER_DATE_FORMAT
import logging

_logger = logging.getLogger(__name__)


class PosConfig(models.Model):
    _inherit = "pos.config"

    sequence_id = fields.Many2one('ir.sequence', string='Order IDs Sequence',
        help="This sequence is automatically created by Odoo but you can change it "
        "to customize the reference numbers of your orders.", copy=False, ondelete='restrict')
    sequence_line_id = fields.Many2one('ir.sequence', string='Order Line IDs Sequence',
        help="This sequence is automatically created by Odoo but you can change it "
        "to customize the reference numbers of your orders lines.", copy=False)

    def write(self, vals):
        result = super(PosConfig, self).write(vals)
        IrSequence = self.env['ir.sequence'].sudo()
        # values['sequence_line_id'] = IrSequence.create(val).id
        if vals.get('name'):
            IrSequence.search([('id','=',self.sequence_id.id)]).write({'name':'POS order '+vals.get('name'),'prefix':vals.get('name')+'/%(year)s/'})
            IrSequence.search([('id','=',self.sequence_line_id.id)]).write({'name':'POS orderline '+vals.get('name'),'prefix':vals.get('name')+'/%(year)s/'})

        return result

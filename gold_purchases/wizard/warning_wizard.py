from itertools import groupby
from odoo.osv import expression
from odoo import api, fields, models , _
from odoo.exceptions import RedirectWarning, UserError, ValidationError
from odoo.tools import float_is_zero, float_compare, safe_eval, date_utils, email_split, email_escape_char, email_re
from odoo.tools.misc import formatLang, format_date, get_lang
from datetime import date, timedelta

class process_warning_wizard(models.Model):
    _name = 'process.warning.wizard'
    _description = 'Process !?'

    def process_order(self):
        active_ids = self._context.get('active_ids') or self._context.get('active_id')
        po = self.env['purchase.order'].browse(active_ids)
        return po.process()


class return_warning_wizard(models.Model):
    _name = 'return.warning.wizard'
    _description = 'Receive !?'

    def return_order(self):
        active_ids = self._context.get('active_ids') or self._context.get('active_id')
        po = self.env['purchase.order'].browse(active_ids)
        return po.return_component()

# -*- coding: utf-8 -*-

from datetime import datetime
from lxml import etree
from dateutil.relativedelta import relativedelta
import re
import logging
from pytz import timezone

import requests

from odoo import api, fields, models
from odoo.addons.web.controllers.main import xml2json_from_elementtree
from odoo.exceptions import UserError
from odoo.tools.translate import _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

BANXICO_DATE_FORMAT = '%d/%m/%Y'

_logger = logging.getLogger(__name__)

class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.model
    def run_update_currency(self):
        """ This method is called from a cron job to update currency rates.
        """
        is_manual = False
        records = self.search([('currency_interval_unit', '<=', 'manually')])
        if len(records) > 0:
            is_manual = True
        if is_manual:
            to_update = self.env['res.company'].search([])
            for company in to_update:
                old = self.env['gold.rates'].search([('name', '=', fields.Date.today())])
                old.unlink()
                company.update_currency_rates()
        else:
            records = self.search([('currency_next_execution_date', '<=', fields.Date.today())])
            if records:
                to_update = self.env['res.company']
                for record in records:
                    if record.currency_interval_unit == 'daily':
                        next_update = relativedelta(days=+1)
                    elif record.currency_interval_unit == 'weekly':
                        next_update = relativedelta(weeks=+1)
                    elif record.currency_interval_unit == 'monthly':
                        next_update = relativedelta(months=+1)
                    else:
                        record.currency_next_execution_date = False
                        continue
                    record.currency_next_execution_date = datetime.date.today() + next_update
                    to_update += record
                to_update.update_currency_rates()



class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    gold_rate = fields.Float(string='Gold Rate', digits=(12, 5))

    hide_order_gold_rate = fields.Boolean(compute="_compute_hide_order_gold_rate")
    @api.onchange('currency_id', 'date_order', 'order_type')
    def _compute_hide_order_gold_rate(self):
        for this in self:
            if (this.gold == False and this.assembly == False) or this.is_unfixed == True:
                this.hide_order_gold_rate = True
            else:
                this.hide_order_gold_rate = False

    @api.onchange('currency_id', 'date_order', 'order_type')
    def get_gold_rate(self):
        if self.date_order and self.currency_id and self.currency_id.is_gold \
                and self.order_type and self.order_type.gold or self.order_type.assembly:
            if self.company_id:
                self.company_id.update_currency_rates()
            rates = self.env['gold.rates'].search([
                ('currency_id', '=', self.currency_id.id),
                ('name', '=', self.date_order.date()),
                ('company_id', 'in', [False, self.company_id and
                                      self.company_id.id or False])
            ], limit=1, order='name desc, id desc')
            ozs = self.env.ref('uom.product_uom_oz')
            if rates and ozs:
                self.gold_rate = (1.000/rates[0].rate)*ozs.factor
                self.gold_rate = self.gold_rate + self.currency_id.premium
            else:
                self.gold_rate = 0.00
        else:
            self.gold_rate = 0.00

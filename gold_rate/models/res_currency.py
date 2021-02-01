# -*- coding: utf-8 -*-
import time
from odoo import api, fields, models, _


class ResCurrency(models.Model):
    _inherit = 'res.currency'

    is_gold = fields.Boolean('Is Gold')
    uom_id = fields.Many2one('uom.uom', 'Unit Of Measure')
    gold_rate_ids = fields.One2many('gold.rates', 'currency_id',
                                    string='Gold Rates')
    gold_rate = fields.Float(
        compute='_compute_current_gold_rate', string='Current Rate',
        digits=(12, 12), help='The rate of the currency to the currency of '
                              'rate 1.')
    premium = fields.Float(string="Gold Premium Per Kg")
    @api.onchange('is_gold')
    def onchange_is_gold(self):
        if self.is_gold:
            if self.env.ref('uom.product_uom_oz'):
                self.uom_id = self.env.ref('uom.product_uom_oz').id
        else:
            self.uom_id = False

    def _get_gold_rates(self, company, date):
        self.env['gold.rates'].flush(
            ['rate', 'currency_id', 'company_id', 'name'])
        query = """SELECT c.id,
                          COALESCE((SELECT r.rate FROM gold_rates r
                                  WHERE r.currency_id = c.id AND r.name <= %s
                                    AND (r.company_id IS NULL OR r.company_id = %s)
                               ORDER BY r.company_id, r.name DESC
                                  LIMIT 1), 1.0) AS gold_rate
                   FROM res_currency c
                   WHERE c.id IN %s"""
        self._cr.execute(query, (date, company.id, tuple(self.ids)))
        currency_rates = dict(self._cr.fetchall())
        return currency_rates

    @api.depends('rate_ids.rate')
    def _compute_current_gold_rate(self):
        date = self._context.get('date') or fields.Date.today()
        company = self.env['res.company'].browse(
            self._context.get('company_id')) or self.env.company
        # the subquery selects the last rate before 'date' for the given currency/company
        currency_rates = self._get_gold_rates(company, date)
        for currency in self:
            currency.gold_rate = currency_rates.get(currency.id) or 1.0


class GoldRates(models.Model):
    _name = 'gold.rates'
    _description = 'Gold Rates'
    _order = "name desc"

    name = fields.Date(string='Date', required=True, index=True,
                       default=lambda self: fields.Date.today())
    rate = fields.Float(digits=(12, 12), default=1.0,
                        help='The rate of the currency to the currency of rate 1')
    currency_id = fields.Many2one('res.currency', string='Currency',
                                  readonly=True)
    uom_id = fields.Many2one(related='currency_id.uom_id')
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)

    _sql_constraints = [
        ('unique_name_per_day', 'unique (name,currency_id,company_id)',
         'Only one currency rate per day allowed!'),
        ('currency_rate_check', 'CHECK (rate>0)',
         'The currency rate must be strictly positive.'),
    ]

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100,
                     name_get_uid=None):
        if operator in ['=', '!=']:
            try:
                date_format = '%Y-%m-%d'
                if self._context.get('lang'):
                    lang_id = self.env['res.lang']._search(
                        [('code', '=', self._context['lang'])],
                        access_rights_uid=name_get_uid)
                    if lang_id:
                        date_format = self.browse(lang_id).date_format
                name = time.strftime('%Y-%m-%d',
                                     time.strptime(name, date_format))
            except ValueError:
                try:
                    args.append(('rate', operator, float(name)))
                except ValueError:
                    return []
                name = ''
                operator = 'ilike'
        return super(GoldRates, self)._name_search(name, args=args,
                                                   operator=operator,
                                                   limit=limit,
                                                   name_get_uid=name_get_uid)

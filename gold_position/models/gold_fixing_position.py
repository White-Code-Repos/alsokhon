from odoo import api, fields, models, _


class GoldFixingPositionReport(models.Model):
    _name = 'gold.fixing.position.report'

    name = fields.Char(string='Doc. No.')
    date = fields.Date(string='Doc. Date')
    quantity_in = fields.Float(string='In')
    quantity_out = fields.Float(string='Out')
    rate_kilo = fields.Float(string='Rate/Kg', digits=(12, 3))
    value = fields.Float(string='Value')
    rate_gram = fields.Float(string='Rate/G')
    quantity_balance = fields.Float(string='Balance')
    amount_balance = fields.Float(string='Balance')
    amount_average = fields.Float(string='Average', digits=(12, 3))
    gold_capital = fields.Float(string='')
    current_position = fields.Float(string='')
    capital_difference = fields.Float(string='')

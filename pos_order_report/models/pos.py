# # -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class PosOrder(models.Model):
    _inherit = 'pos.order'

    def print_report(self):
        return self.env.ref('pos_order_report.action_external_report_pos_order').report_action(self)

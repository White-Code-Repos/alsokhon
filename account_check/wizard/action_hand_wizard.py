# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ActionHanded(models.TransientModel):
    _name = 'action.handed.wizard'

    employee_id = fields.Many2one(comodel_name='res.partner', string='Handed To')
    check_id = fields.Many2one(comodel_name='account.check')

    def change_state_to_handed(self):
        if self.check_id:
            for line in self.check_id.operation_ids:
                if line.operation == 'holding':
                    line.handed_to = self.employee_id.id
            self.check_id.action_to_handed()

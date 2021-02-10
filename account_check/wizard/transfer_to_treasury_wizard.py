# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ActionTransferToTreasury(models.TransientModel):
    _name = 'action.transfer.treasury.wizard'

    treasury_journal_id = fields.Many2one(comodel_name='account.journal', string='Treasury To')
    check_id = fields.Many2one(comodel_name='account.check')

    def transfer_to_treasury_wizard(self):
        self.check_id.treasury_journal_id = self.treasury_journal_id.id

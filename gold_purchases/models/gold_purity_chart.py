# -*- coding: utf-8 -*-
from odoo.osv import expression
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class GoldPurity(models.Model):
    _name = 'gold.purity'
    _description = 'Gold Purity Charts'

    karat = fields.Float('Karat')
    parts = fields.Float('Parts Gold')
    out_of_parts = fields.Float('Out Of Parts Gold')
    purity = fields.Float('Purity/Hallmark')
    scrap_purity = fields.Float('Scrap Purity/Hallmark')
    gold_percent = fields.Float('Gold %', digits='Product Price')
    scrap_percent = fields.Float('Scrap %', digits='Product Price')
    allow_delete = fields.Boolean(default=True)
    name = fields.Char('Karat', compute='get_name')
    parts_name = fields.Char('Parts Gold', compute='get_part_name')

    def get_part_name(self):
        for rec in self:
            rec.parts_name = '%s / %s' % (rec.parts, rec.out_of_parts)

    def get_name(self):
        for rec in self:
            rec.name = rec.karat and int(rec.karat) or 0

    @api.constrains('parts')
    def check_parts(self):
        for rec in self:
            if not (0 < rec.parts <= 1000):
                raise UserError(_('Actual gold parts should be between 0 to '
                                  '1000.'))

    @api.constrains('out_of_parts')
    def check_out_of_parts(self):
        for rec in self:
            if not (0 < rec.out_of_parts <= 1000):
                raise UserError(_('Gold Parts should be between 0 to 1000.'))

    @api.constrains('purity')
    def check_purity(self):
        for rec in self:
            if not (0 < rec.purity <= 1000):
                raise UserError(_('Purity should be between 0 to 1000.'))

    @api.constrains('scrap_purity')
    def check_purity_scrap(self):
        for rec in self:
            if not (0 < rec.scrap_purity <= 1000):
                raise UserError(_('Scrap Purity should be between 0 to 1000.'))

    @api.constrains('gold_percent')
    def check_gold_percent(self):
        for rec in self:
            if not (0 < rec.gold_percent <= 100):
                raise UserError(
                    _('Gold Percentage should be between 0 to 100.'))

    @api.constrains('out_of_parts', 'parts')
    def check_parts_with_outof_parts(self):
        for rec in self:
            if rec.parts > rec.out_of_parts:
                raise UserError(_('Total gold parts should be greater than '
                                  'actual gold parts'))

    def unlink(self):
        recs = self.filtered(lambda x: not x.allow_delete)
        if recs:
            raise UserError(_('You are not allowed to delete %s records.' %
                              recs[0].name))
        return super(GoldPurity, self).unlink()

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100,
                     name_get_uid=None):
        if not args:
            args = []
        if name:
            args = expression.AND([args, [('karat', operator, name)]])
        return super(GoldPurity, self)._name_search(
            name, args, operator, limit, name_get_uid)

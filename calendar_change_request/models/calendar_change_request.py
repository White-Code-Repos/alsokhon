from odoo import api,fields,models,_
from datetime import datetime, timedelta, time

class CalendarChangeRequest(models.Model):
    _name = 'working.calendar.change.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    # , 'portal.mixin'
    _description = "Working Calendar Change Request"

    def _get_resource_calendar(self):
        if self.employee_id and self.employee_id.resource_calendar_id:
            return self.employee_id.resource_calendar_id.id

    def _default_user(self):
        user_id = self.env.context.get('user_id', self.env.user.id)
        return self.env['hr.employee'].search([('user_id','=',user_id)],limit=1).id

    employee_id = fields.Many2one('hr.employee', "Employee", default=_default_user)
    current_working_time = fields.Many2one('resource.calendar', 'Current Working Hours',default=_get_resource_calendar)
    new_working_time = fields.Many2one('resource.calendar', 'New Working Hours')
    state = fields.Selection(
        [('draft', 'Draft'), ('in-progress', 'In Progress'),('approved','Approved'),('rejected','Rejected')],
        readonly=True, default='draft', copy=False, string="Status")


    def action_submit(self):
        self.state = 'in-progress'

    def action_reject(self):
        self.state = 'rejected'

    def action_approve(self):
        self.state = 'approved'
        self.employee_id.resource_calendar_id = self.new_working_time.id

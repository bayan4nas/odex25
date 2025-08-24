# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.misc import format_date, formatLang


class OvertimeRejectWizard(models.TransientModel):
    _name = 'overtime.reject.wizard'
    _description = 'Overtime Reject Wizard'

    reason = fields.Text(string='Reason', required=True)
    type = fields.Selection(selection=[('overtime', 'overtime'), ('termination', 'termination')])

    def action_return(self):
        global message
        self.ensure_one()
        if self.type == 'overtime':
            overtime = self.env['employee.overtime.request'].browse(self._context.get('active_id'))
            overtime.write({'state': 'submit'})
            message = _("overtime request moved to submit: {}").format(self.reason)
            overtime.message_post(body=message)
        else:
            termination = self.env['hr.termination'].browse(self._context.get('active_id'))
            termination.write({'state': 'hr_manager'})
            message = _("termination request moved to HR: {}").format(self.reason)
            termination.message_post(body=message)

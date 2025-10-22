## -*- coding: utf-8 -*-
##############################################################################
#
#    Expert
#    Copyright (C) 2020-2021 Expert(Sudan Team A)
#
##############################################################################
from datetime import date
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class AppraisalRefuseWizard(models.TransientModel):
    _name = 'appraisal.refuse.wizard'
    _description = 'Appraisal Refuse Wizard'

    appraisal_id = fields.Many2one('hr.employee.appraisal', string="Appraisal", default=lambda self: self._default_appraisal_id,required=True)
    goal_id = fields.Many2one('years.employee.goals', string="Goal to Refuse")
    skill_id = fields.Many2one('skill.item.employee.table', string="Skill to Refuse")

    def _default_appraisal_id(self):
        return self.env.context.get("active_id")
    def action_confirm_refuse(self):
        self.ensure_one()
        appraisal = self.appraisal_id

        appraisal.write({
            'refused_goal_id': self.goal_id.id,
            'refused_skill_id': self.skill_id.id,
            'state': 'refused'
        })

        return {'type': 'ir.actions.act_window_close'}


class AppraisalCancelWizard(models.TransientModel):
    _name = "appraisal.cancel.wizard"
    _description = "Appraisal Cancel Wizard"

    cancel_reason = fields.Text(string="Reason", required=True)

    def action_confirm_cancel(self):
        appraisal = self.env['hr.employee.appraisal'].browse(self._context.get('active_id'))
        appraisal.write({
            'state': 'cancel',
            'cancel_reason': self.cancel_reason,
        })


class PerformanceEvaluationReport(models.TransientModel):
    _name = 'performance.evaluation.report'
    _description = "Performance Evaluation Report"

    date_from = fields.Date(string='Date From', default=lambda self: date(date.today().year, date.today().month, 1))
    date_to = fields.Date(string='Date To',default=lambda self: date(date.today().year, date.today().month, 1) + relativedelta(months=1, days=-1))
    appraisal_stage_id = fields.Many2one('goals.stages', 'Appraisal Stage')
    employee_ids = fields.Many2many('hr.employee', string='Employees')
    department_ids = fields.Many2many('hr.department', string='Department')

    @api.onchange('department_ids')
    def get_department_employee(self):
        if self.department_ids:
            emps = self.department_ids.mapped('employee_ids').ids
            domain = [('id', 'in', emps)]
            domain += [('state', '=', 'open')]
            return {'domain': {'employee_ids': domain}}
        else:
            domain = [('id', 'in', False)]
            domain += [('state', '=', 'open')]
            return {'domain': {'employee_ids': domain}}

    def check_data(self):
        if self.date_from and not self.date_to or not self.date_from and self.date_to:
            raise UserError(_('Choose Date From and Date To'))
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise UserError(_('Date From must be less than or equal Date To'))
        return {'form': (self.read()[0]), }

    def print_report(self):
        datas = self.check_data()
        return self.env.ref('exp_hr_appraisal_kpi.performance_evaluation_report_action').report_action(self, data=datas)

    def print_report_xlsx(self):
        datas = self.check_data()
        return self.env.ref('exp_hr_appraisal_kpi.performance_evaluation_report_xlsx_action').report_action(self, data=datas)


# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ProjectMetrics(models.Model):
    _name = "project.project.metrics"
    _description = "Project Metrics"
    _order = "week_id"

    project_id = fields.Many2one('project.project', string="Project")
    # weight = fields.Float(related='project_id.weight', string="Weight", store=True)
    week_id = fields.Many2one('time.plan.details', string="Week")
    plan_line_ids = fields.Many2many('project.time.plan.line', compute="_get_time_plan", string="Time plan lines")
    total_time_plan = fields.Float(related="project_id.total_time_plan", string="Total Time Plan")
    week_time_plan = fields.Float(compute="_compute_progress", string="Week cumulative distributed budge(PV)",
                                  store=True)
    week_consumed_hours = fields.Float(compute="_compute_progress", string="Week accumulative Consumed Hours(AC)",
                                       store=True)
    progress = fields.Float(string="Progress%", compute="_compute_progress", store=True)
    ev = fields.Float(string="Earned value", compute="_compute_progress", store=True,
                      help="Earned value (EV) = Progress% * Total Hours")
    cpi = fields.Float(string="Cost Performance Index", compute="_compute_progress", store=True,
                       help="Cost Performance Index (CPI = EV/AC) \n *EV Earned Value \n *AC  accumulative Consumed Hours")
    spi = fields.Float(string="Schedule Performance Index", compute="_compute_progress", store=True,
                       help="Schedule Performance Index (SPI = EV/PV) \n *PV  cumulative distributed budge \n *EV Earned Value")
    cv = fields.Float(string="Cost Variance", compute="_compute_progress", store=True,
                      help="Cost Variance (CV = EV - AC)")
    sv = fields.Float(string="Schedule Variance", compute="_compute_progress", store=True,
                      help="Schedule Variance (SV = EV - PV)")
    eac = fields.Float(string="Estimated Cost at Completion", compute="_compute_progress", store=True,
                       help="Estimated Cost at Completion (EAC) = (BAC / CPI) \n *BAC Planned Budget \n *CPI Cost Performance Index")
    etc = fields.Float(string="Estimated To Completion (ETC)", compute="_compute_progress", store=True,
                       help="Estimated To Completion (ETC) = (BAC - EV) / CPI \n *BAC Planned Budget \n *CPI Cost Performance Index \n *EV Earned Value")
    vac = fields.Float(string="Variance at Completion (VAC)", compute="_compute_progress", store=True,
                       help="Variance at Completion (VAC) = BAC - EAC \n *BAC Planned Budget \n *EAC Estimated Cost at Completion")
    tcpi = fields.Float(string="To Complete Performance Index(TCPI)", compute="_compute_progress", store=True,
                        help="To Complete Performance Index(TCPI) = (BAC - EV) / (BAC - AC) \n *BAC Planned Budget \n *EV Earned Value \n *AC Accumulative Consumed Hours")

    def _compute_progress(self):
        for rec in self:
            # 1 Compute Progress
            print("===================================",rec.project_id.tasks.filtered(lambda task: not task.parent_id))
            progress = 0.0
            for dept in rec.project_id.tasks.filtered(lambda task: not task.parent_id).mapped('task_progress_ids').filtered(lambda p: p.week_id.id == rec.week_id.id):
                progress += (dept.task_progress * (dept.weight / 100))
            rec.progress = round(progress)
            # for dept in rec.project_id.tasks.filtered(lambda task: not task.parent_id).mapped(
            #         'task_progress_ids').filtered(lambda p: p.week_id.id == rec.week_id.id):
            #     progress += (dept.task_progress * (dept.weight / 100))
            # rec.progress = round(progress)

            # 2 Compute ev
            rec.ev = (rec.progress / 100) * rec.total_time_plan
            # 3 cpi
            rec.week_consumed_hours = sum(self.env['account.analytic.line'].search(
                [('project_id', '=', rec.project_id.id), ('date', '<=', rec.week_id.date_to)]).mapped('unit_amount'))
            if rec.week_consumed_hours:
                rec.cpi = rec.ev / rec.week_consumed_hours
            else:
                rec.cpi = 0.0
            # 4 spi
            rec.week_time_plan = sum(self.env['project.time.plan.line'].search(
                [('project_id', '=', rec.project_id.id), ('time_plan_id.date_to', '<=', rec.week_id.date_to)]).mapped(
                'time_plan'))
            if rec.week_time_plan:
                rec.spi = rec.ev / rec.week_time_plan
            else:
                rec.spi = 0.0
            # 5 cv
            if rec.ev:
                rec.cv = rec.ev - rec.week_consumed_hours
            else:
                rec.cv = 0.0
            # 6 sv
            if rec.ev:
                rec.sv = rec.ev - rec.week_time_plan
            else:
                rec.sv = 0.0
            # 7 eac
            if rec.cpi:
                rec.eac = rec.total_time_plan / rec.cpi
            else:
                rec.eac = 0.0
            # 8 etc
            if rec.cpi:
                rec.etc = (rec.total_time_plan - rec.ev) / rec.cpi
            else:
                rec.etc = 0.0
            # 9 VAC = BAC - EAC
            rec.vac = rec.total_time_plan - rec.eac
            # 10 TCPI = (BAC - EV) / (BAC - AC)
            if rec.total_time_plan - rec.week_consumed_hours > 0:
                rec.tcpi = (rec.total_time_plan - rec.ev) / (rec.total_time_plan - rec.week_consumed_hours)
            else:
                rec.tcpi = 0.0

    def _get_time_plan(self):
        for rec in self:
            rec.plan_line_ids = []
            plan_line_ids = self.env['project.time.plan.line'].search(
                [('project_id', '=', rec.project_id.id), ('time_plan_id', '=', rec.week_id.id)])
            if plan_line_ids:
                rec.plan_line_ids = plan_line_ids.ids

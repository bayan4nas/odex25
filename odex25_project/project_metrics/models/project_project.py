
# -*- coding: utf-8 -*-
import ast
import calendar
from datetime import datetime, time, timedelta
from dateutil import relativedelta
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY
from odoo.osv import expression
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class Project(models.Model):
    _inherit = "project.project"

    total_time_plan = fields.Float("Total Time Plan", compute="_compute_total_time", store=True)
    week_ids = fields.Many2many('time.plan.details', compute="_get_project_weeks", string="Week")
    project_metrics_ids = fields.One2many("project.project.metrics", 'project_id', string="Project Metrics")



    @api.depends("time_plan_ids", "time_plan_ids.time_plan")
    def _compute_total_time(self):
        for rec in self:
            rec.total_time_plan = 0.0
            if rec.time_plan_ids:
                rec.total_time_plan = sum(rec.time_plan_ids.mapped("time_plan"))

    @api.depends("time_plan_ids", "time_plan_ids.line_ids")
    def _get_project_weeks(self):
        for rec in self:
            rec.week_ids = []
            weeks = rec.time_plan_ids.mapped("line_ids").mapped("time_plan_id")
            if weeks:
                rec.week_ids = weeks.ids
                # rec.get_project_metrics()

    def get_project_metrics(self):
        for rec in self:
            vals_list = []
            ProjectMetrics = self.env['project.project.metrics']
            metrics_weeks = rec.project_metrics_ids.mapped("week_id").ids
            for week in rec.week_ids:
                if week.id not in metrics_weeks:
                    vals_list.append({'project_id': rec.id, 'week_id': week.id})
            if vals_list:
                ProjectMetrics.create(vals_list)





    def action_view_project_metrics(self):
        self.ensure_one()
        self.get_project_metrics()
        self.mapped("project_metrics_ids")._get_time_plan()
        self.mapped("project_metrics_ids")._compute_progress()
        self.project_metrics_ids._get_time_plan()
        self.project_metrics_ids._compute_progress()
        action_window = {
            "type": "ir.actions.act_window",
            "res_model": "project.project.metrics",
            "name": "Project Metrics",
            'view_type': 'form',
            'view_mode': 'tree,pivot,graph',
            "context": {"create": False},
            "domain": [('project_id', '=', self.id)]
        }
        return action_window
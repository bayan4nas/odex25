# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError



class ProjectTimePlan(models.Model):
    _inherit = "project.time.plan"

    task_ids = fields.One2many('project.task', 'time_plan_id', string="Tasks")



    @api.model
    def create(self, vals):
        res = super().create(vals)
        if vals.get('time_plan_ids', False):
            res.task_ids.get_progress_ids()
        return res

    def write(self, vals):
        res = super().write(vals)
        if vals.get('time_plan_ids', False):
            self.task_ids.get_progress_ids()
        return res

class ProjectTask(models.Model):
    _inherit = "project.task"

    phase_id = fields.Many2one('project.phase', string='Project Phase', domain="[('project_id','=',project_id)]")
    department_id = fields.Many2one('hr.department', string="Department")
    department_ids = fields.Many2many('hr.department', related="phase_id.department_ids", string="All stage Departments")
    task_progress_ids = fields.One2many('project.task.progress', 'task_id', string="Task Progress")
    time_plan_id = fields.Many2one('project.time.plan', compute="_get_time_plan", string="Time plan", store=True)
    plan_details_ids = fields.Many2many('time.plan.details', related="time_plan_id.time_plan_ids")
    weight = fields.Float(string="Weight", compute="_compute_weight" ,store=True)
    plan_by_departments = fields.Boolean(related='company_id.plan_by_departments')

    @api.depends('planned_hours', 'time_plan_id', 'time_plan_id.time_plan')
    def _compute_weight(self):
        for rec in self:
            rec.weight = 0
            if rec.child_ids:
                rec.weight = sum(rec.child_ids.mapped('weight'))
            else:
                if rec.planned_hours and rec.time_plan_id.time_plan:
                    rec.weight = round((rec.planned_hours / rec.time_plan_id.time_plan) * 100, 1)

    @api.depends('project_id', 'department_id', 'phase_id')
    def _get_time_plan(self):
        for rec in self:
            rec.time_plan_id = False
            if rec.project_id and rec.department_id and rec.phase_id:
                rec.time_plan_id = self.env['project.time.plan'].search(
                    [('project_id', '=', rec.project_id.id), ('department_id', '=', rec.department_id.id),
                     ('phase_id', '=', rec.phase_id.id)])

    def _get_same_week(self, week):
        weeks = self.env['project.task.progress']
        weeks = self.mapped('task_progress_ids').filtered(lambda l: l.week_id.id == week.id)
        return weeks




    @api.onchange('phase_id')
    def _onchange_phase_id(self):
        for task in self:
            task.department_id=False



    def get_progress_ids(self):
        TaskLine = self.env["project.task.progress"]
        for rec in self:
            vals_list = []
            lines_week = rec.task_progress_ids.mapped('week_id')
            for week in rec.time_plan_id.time_plan_ids:
                if week.id not in lines_week.ids:
                    vals_list.append({'task_id': rec.id, 'week_id': week.id, })
            rec.task_progress_ids = [(6, 0, TaskLine.create(vals_list).ids)]

    def action_task_progress(self):
        action_window = {
            "type": "ir.actions.act_window",
            "res_model": "project.task.progress",
            "name": "Task Progress",
            'view_type': 'form',
            'view_mode': 'tree,form',
            "context": {"create": False},
            "domain": [('task_id', '=', self.id)]
        }
        return action_window


    def write(self, vals):
        res = super().write(vals)
        if vals.get('project_id', False) or vals.get('department_id', False) or vals.get('phase_id', False) or vals.get('time_plan_id', False):
            self.get_progress_ids()
        return res

    @api.model
    def create(self, vals):
        res = super().create(vals)
        if res.project_id.status not in ['open']:
            raise ValidationError(_("You cannot create Tasks for Project that is not in Open status!"))
        res.get_progress_ids()
        return res






class ProjectTaskProgress(models.Model):
    _name = "project.task.progress"
    _description = "Task Progress"
    _rec_name = 'task_id'

    task_id = fields.Many2one('project.task', string="Task",ondelete="cascade")
    weight = fields.Float(related="task_id.weight", string="Weight")
    project_id = fields.Many2one('project.project', related="task_id.project_id", string="Project", store=True)
    week_id = fields.Many2one('time.plan.details', string="Plan Details")
    date_from = fields.Date(related="week_id.date_from")
    date_to = fields.Date(related="week_id.date_to")
    department_id = fields.Many2one('hr.department', related="task_id.department_id", store=True)
    task_progress = fields.Float(string="Progress%", compute='_compute_progress', readonly=False, store=True,copy=False)


    @api.depends('task_id.child_ids', 'task_id.project_id', 'task_id.child_ids.task_progress_ids',
                 'task_id.child_ids.task_progress_ids.task_progress')
    def _compute_progress(self):
        for record in self:
            if record.task_id.child_ids and record.task_id.weight:
                task_progress = 0.0
                progress_rec = record.task_id.child_ids._get_same_week(record.week_id)
                for t in progress_rec:
                    task_progress += (t.task_progress * t.task_id.weight)

                record.task_progress = round(task_progress / record.task_id.weight, 1)
            project_metrics = record.project_id.project_metrics_ids.filtered(lambda x: x.week_id.id == record.week_id.id)
            project_metrics._compute_progress()

# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class TimePlanDetails(models.Model):
    _name = "time.plan.details"
    _description = "Time Plan Details"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char("Code")
    date_from = fields.Date(string="From")
    date_to = fields.Date(string="To")


class ProjectTimePlan(models.Model):
    _name = "project.time.plan"
    _description = "Time Plan"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    department_id = fields.Many2one('hr.department', string="Department", tracking=True)
    project_id = fields.Many2one('project.project', string='Project', ondelete="restrict", tracking=True)
    project_status = fields.Selection([
        ('open', 'Open'),
        ('pending', 'Closed Pending Payment'),
        ('hold', 'Hold'),
        ('close', 'Closed')], string='Status', related="project_id.status")
    company_id = fields.Many2one('res.company', related="project_id.company_id", string='Company')
    plan_by_departments = fields.Boolean(string="Plan By Departments", related='company_id.plan_by_departments',readonly=False)
    project_user_id = fields.Many2one("res.users", related="project_id.user_id", string="Project Manager", store=True)
    phase_id = fields.Many2one('project.phase', ondelete="restrict", string='Project Stage', tracking=True)
    start_date = fields.Date(string="From", related='phase_id.start_date')
    end_date = fields.Date(string="To", related='phase_id.end_date')
    origin_plan = fields.Float(string="Stage Total Hours", related="phase_id.estimated_hours")
    time_plan = fields.Float(string="Dept Allocated Hrs")
    remaining_hours = fields.Float()
    consumed_hours = fields.Float()
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('close', 'Closed')], string='Status',
        copy=False, default='draft', required=True, tracking=True)
    time_plan_ids = fields.Many2many('time.plan.details', string="Time Plan")
    line_ids = fields.One2many('project.time.plan.line', 'plan_id')

    def action_view_time_plan(self):
        self.ensure_one()
        action_window = {
            "type": "ir.actions.act_window",
            "res_model": "project.time.plan.line",
            "name": "Time Plan",
            'view_type': 'tree',
            'view_mode': 'pivot,tree',
            "context": {"create": False},
            "domain": [('plan_id', '=', self.id)]
        }
        return action_window

    @api.constrains('phase_id', 'time_plan')
    def _check_hours(self):
        for rec in self:
            if rec.plan_by_departments:
                time_plan = sum(rec.phase_id.time_plan_ids.mapped('time_plan'))
            else:
                time_plan = sum(rec.phase_id.time_plan_ids.mapped('origin_plan'))
            if time_plan > rec.phase_id.estimated_hours and not rec._context.get('edit', False):
                raise ValidationError(_('Sum of Time Plans Hours must not exceed stage Allocated Hours.'))

    @api.constrains('time_plan', 'line_ids', 'line_ids.time_plan')
    def _check_weeks_time(self):
        line_time_plan = sum(self.line_ids.mapped('time_plan'))
        for rec in self:
            if rec.plan_by_departments:
                if line_time_plan > rec.time_plan:
                    raise ValidationError(_('Sum of time plan Details must not exceed %s.' % rec.time_plan))
            else:
                if line_time_plan > rec.origin_plan:
                    raise ValidationError(_('Sum of time plan Details must not exceed %s.' % rec.origin_plan))

    def name_get(self):
        result = []
        for rec in self:
            name = rec.department_id.name or '' + '-' + rec.project_id.name or ''
            result.append((rec.id, name))
        return result

    @api.onchange('phase_id')
    def _onchange_phase_id(self):
        plan_details = []
        if self.phase_id:
            plan_details = self._get_time_plan_details(self.phase_id.start_date, self.phase_id.end_date)
        self.time_plan_ids = [(6, 0, plan_details)]

    def unlink(self):
        for rec in self:
            if rec.state not in ['draft']:
                raise UserError(_('You cannot delete a confirmed Time plan.'))
            rec.line_ids.unlink()
        super(ProjectTimePlan, self).unlink()

    def _get_time_plan_details(self, start_date, end_date):
        WEEK_OBJ = self.env['time.plan.details']
        self.env.cr.execute("""
                        SELECT id
                        FROM time_plan_details
                        WHERE (date_from between %s AND %s) OR (date_to between %s AND %s)""",
                            (fields.Date.to_string(start_date), fields.Date.to_string(end_date),
                             fields.Date.to_string(start_date), fields.Date.to_string(end_date)))
        plan_details = list(w[0] for w in self.env.cr.fetchall())
        if not plan_details and not self.line_ids:
            raise ValidationError(_("Kindly check time plan details configration with your admin"))
        return plan_details

    def get_line_ids(self):
        PlanLine = self.env["project.time.plan.line"]
        for plan in self:
            vals_list = []
            for time_plan in plan.time_plan_ids:
                vals_list.append({'plan_id': plan.id, 'project_id': plan.project_id.id, 'time_plan_id': time_plan.id,
                                  'department_id': plan.department_id.id})
            plan.line_ids = [(6, 0, PlanLine.create(vals_list).ids)]

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_confirm(self):
        self.write({'state': 'confirm'})

    def action_close(self):
        self.write({'state': 'close'})


class ProjectTimePlanLine(models.Model):
    _name = "project.time.plan.line"
    _description = "Time Plan Details"

    plan_id = fields.Many2one('project.time.plan', ondelete="cascade")
    company_id = fields.Many2one('res.company', related="project_id.company_id", string='Company')
    phase_id = fields.Many2one('project.phase', related='plan_id.phase_id', store=True)
    time_plan_id = fields.Many2one('time.plan.details', string="Time Plan")
    time_plan_date_from = fields.Date(related="time_plan_id.date_from", store=True)
    time_plan_date_to = fields.Date(related="time_plan_id.date_to", store=True)
    project_id = fields.Many2one('project.project', string="Project", store=True)
    department_id = fields.Many2one("hr.department", related='plan_id.department_id', string="Department", store=True)
    time_plan = fields.Float(string="Hours", default=0.0)
    hr_plan = fields.Float(string="HR Plan", compute="_compute_hr_plan", store=True)
    plan_by_departments = fields.Boolean(related='plan_id.plan_by_departments')


    @api.depends('time_plan')
    def _compute_hr_plan(self):
        for rec in self:
            if rec.time_plan:
                rec.hr_plan = rec.time_plan / 45
            else:
                rec.hr_plan = 0.0


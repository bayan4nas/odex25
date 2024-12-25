from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProjectProject(models.Model):
    _inherit = 'project.project'
    plan_by_departments = fields.Boolean(string="Plan By Departments", related='company_id.plan_by_departments',readonly=True)
    plan_by = fields.Selection(string='Plan By',related='company_id.plan_by', readonly=False)
    time_plan_ids = fields.One2many('project.time.plan', 'project_id', string="Project Time Plans")







class ProjectPhase(models.Model):
    _inherit = 'project.phase'

    department_ids = fields.Many2many('hr.department', string="Departments")
    plan_by_departments = fields.Boolean(string="Plan By Departments", related='company_id.plan_by_departments')
    plan_by = fields.Selection(string='Plan By', related='project_id.plan_by', readonly=True)
    time_plan_ids = fields.One2many('project.time.plan', 'phase_id', string="Time plans")
    estimated_hours = fields.Float(compute="_compute_estimated_hours", store=True)
    plan_by_hour = fields.Float()
    plan_by_day = fields.Float()
    phase_id = fields.Many2one('project.phase', string='Project Phase', domain="[('project_id','=',project_id)]")


    @api.depends('plan_by', 'plan_by_hour','plan_by_day')
    def _compute_estimated_hours(self):
        for rec in self:
           if rec.plan_by == 'man_hours':
               rec.estimated_hours = rec.plan_by_hour
           else:
                if rec.project_id.resource_calendar_id:
                    rec.estimated_hours = rec.plan_by_day * rec.project_id.resource_calendar_id.hours_per_day
                else:
                    rec.estimated_hours = rec.plan_by_day * 8

    def create_plans(self):
        self._create_time_plan()
        self.time_plan_ids._onchange_phase_id()
        self.time_plan_ids.get_line_ids()
        plan_total = sum(self.time_plan_ids.mapped('time_plan'))
        if plan_total > self.estimated_hours:
            raise ValidationError(_('Time Plans Hours for stage %s Exceed Stage Estimated Hours.') % (self.name))

    def action_confirm(self):
        res = super(ProjectPhase, self).action_confirm()
        for rec in self:
            if not rec.start_date or not rec.end_date:
                raise ValidationError(_('Make sure that stage dates is set.'))
            rec.create_plans()
        return self.write({'state': 'open'})

    def action_get_phase(self):
        self.ensure_one()
        action_window = {
            "type": "ir.actions.act_window",
            "res_model": "project.time.plan",
            "name": "%s (%s Hours)"%(self.display_name,self.estimated_hours),
            'view_mode': 'tree',
            "view_id": self.env.ref('project_time_plan.project_time_plan_tree_project').id,
            "context": {"create": False},
            "target": 'new',
            "domain": [('project_id', '=', self.project_id.id),('phase_id', '=', self.id)]
        }
        return action_window


    def _create_time_plan(self):
        for rec in self:
            if rec.plan_by_departments:
                values = []
                exist_dept = rec.time_plan_ids.mapped('department_id').ids
                for dept in rec.department_ids:
                    if dept.id not in exist_dept:
                        values.append({
                            'project_id': rec.project_id.id,
                            'department_id': dept.id,
                            'phase_id': rec.id,
                        })
                self.env['project.time.plan'].create(values)
            else:
                values = [{
                    'project_id': rec.project_id.id,
                    'phase_id': rec.id,
                }]
                self.env['project.time.plan'].create(values)

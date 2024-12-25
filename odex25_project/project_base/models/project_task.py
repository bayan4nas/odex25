# -*- coding: utf-8 -*-
from datetime import datetime, time, timedelta
from dateutil import relativedelta
from odoo.addons.resource.models.resource import float_to_time, HOURS_PER_DAY
from odoo.osv import expression
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, Warning


class ProjectTask(models.Model):
    _inherit = "project.task"

    phase_id = fields.Many2one('project.phase', string='Project Phase', domain="[('project_id','=',project_id)]")
    phase_hours = fields.Float("phase total hours", related="phase_id.estimated_hours")
    user_ids = fields.Many2many('res.users', 'project_task_users',
                                'task_id', 'users_id', string="Employees")
    weight = fields.Float(string='Weight', )
    task_progress = fields.Float(string='Task Progress')
    maximum_rate = fields.Float(string='Maximum Rate', default=1)

    allowed_internal_user_ids = fields.Many2many('res.users', 'project_task_allowed_internal_users_rel',
                                                 string="Allowed Internal Users", default=lambda self: self.env.user,
                                                 domain=[('share', '=', False)])
    allowed_portal_user_ids = fields.Many2many('res.users', 'project_task_allowed_portal_users_rel',
                                               string="Allowed Portal Users", domain=[('share', '=', True)])

    @api.constrains('task_progress', 'weight')
    def _check_task_weight_progress(self):
        for record in self:
            if record.task_progress < 0 or record.task_progress > 100:
                raise ValidationError(_("The task progress must be between 0 and 100."))
            if record.weight < 0 or record.weight > 100:
                raise ValidationError(_("The weight must be between 0 and 100."))

    def write(self, vals):
        res = super(ProjectTask, self).write(vals)
        if 'stage_id' in vals and vals.get('stage_id'):
            manager_users = self.env.ref('project.group_project_manager').users
            department_manager_users = self.env.ref('project_base.group_project_department_manager').users
            # Combine both user sets
            user_ids = manager_users | department_manager_users
            for task in self:
                if task.stage_id.is_closed:
                    task.env['mail.message'].create({
                        'message_type': "notification",
                        'body': _("Task %s is done for project %s and needs your action") % (
                            task.name, task.project_id.name or ""),
                        'subject': _("Done Task"),
                        'partner_ids': [(6, 0, user_ids.mapped('partner_id').ids)],
                        'notification_ids': [
                            (0, 0, {'res_partner_id': user.partner_id.id, 'notification_type': 'inbox'})
                            for user in user_ids if user_ids],
                        'model': task._name,
                        'res_id': task.id,
                        'author_id': self.env.user.partner_id and self.env.user.partner_id.id
                    })
        return res

    @api.onchange('weight')
    def _onchange_weight(self):
        done_task = self.env['project.task'].search(
            [('phase_id', '=', self.phase_id.id), ('id', '!=', self._origin.id)])
        weight_done = done_task.mapped('weight')
        sum_weight = sum(weight_done) + self.weight
        if sum_weight > 100:
            raise ValidationError(_("The total weights of the tasks for the stage must not exceed 100"))

    @api.onchange('project_id')
    def _onchange_project_id(self):
        for task in self:
            self.phase_id = False

    @api.constrains("phase_hours", "planned_hours")
    def _check_dept_hours(self):
        for record in self:
            plan_hours = sum(record.phase_id.mapped("task_ids").mapped("planned_hours"))
            if plan_hours > record.phase_hours:
                raise ValidationError(
                    _("Total planned hours for all tasks in stage %s must not exceed Total stage hours %s") % (
                        record.phase_id.display_name, record.phase_hours))



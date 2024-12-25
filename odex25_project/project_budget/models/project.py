# -*- coding: utf-8 -*-
from odoo import api, models, fields, tools, _
from odoo.exceptions import UserError, ValidationError


class ProjectProject(models.Model):
    _inherit = "project.project"

    budget_id = fields.One2many('crossovered.budget', 'project_id', string="Project Budget")
    project_cost = fields.Float('Cost',compute="_get_project_costs",help="Project Cost to date")
    project_hours_cost = fields.Float('Man-Hours Cost',compute="_get_project_costs",help="Project Man Hours Cost to date")
    project_total_cost = fields.Float('Total Cost',compute="_get_project_costs",help="Project Cost +  Project Man Hours Cost")
    gross_amount = fields.Float('Gross Margin',compute="_get_project_costs",help="Billed amount - Total Cost")
    ready_budget = fields.Boolean('project budget is ready',compute="_get_budget_status")
    estimated_hours = fields.Float("Budget Hours",compute="_get_project_hours",copy=False)


    def _get_project_hours(self):
        for rec in self:
            estimated_hours = 0
            for budget in rec.budget_id:
                estimated_hours = sum(budget.hour_line_ids.mapped("qty"))
            rec.estimated_hours = estimated_hours

    # @api.depends('budget_id','budget_id.crossovered_budget_line','budget_id.crossovered_budget_line.practical_amount','total_invoiced_amount')
    def _get_project_costs(self):
        for rec in self:
            project_cost = 0.0
            project_hours_cost = 0.0
            project_total_cost = 0.0
            gross_amount = 0.0
            for budget in rec.budget_id:
                project_hours_cost = abs(sum(budget.mapped('crossovered_budget_line').filtered(lambda l:l.general_budget_id.is_timesheet_hours).mapped('practical_amount')))
                project_cost = abs(sum(budget.mapped('crossovered_budget_line').filtered(lambda l:not l.general_budget_id.is_timesheet_hours).mapped('practical_amount')))
                project_total_cost = project_hours_cost + project_cost
            rec.project_cost = project_cost
            rec.project_hours_cost = project_hours_cost
            rec.project_total_cost = project_total_cost
            rec.gross_amount = rec.total_invoiced_amount - rec.project_total_cost

    def _get_budget_status(self):
        for rec in self:
            ready_budget = False
            for budget in rec.budget_id:
                if budget.state == 'done':
                    ready_budget = True
            rec.ready_budget = ready_budget


    def _check_hour_budget(self, to_add_hours):
        for rec in self:
            for budget in rec.budget_id:
                for line in budget.hour_line_ids:
                    add_amount = to_add_hours * line.amount
                    if add_amount > line.project_remaining_amount:
                        raise ValidationError(
                            _("There is No enough Man-Hours in project budget %s , please contact your manager") % (
                                rec.display_name))

    def _check_project_budget(self):
        for rec in self:
            if not rec.budget_id:
                raise ValidationError(_("There is no budget created yet for this project."))
            for budget in rec.budget_id:
                if budget.state != 'done':
                    raise ValidationError(_("The Budget must approved from accounting first!"))
                budget_hours = sum(budget.hour_line_ids.mapped("qty"))
                project_hours = sum(rec.project_phase_ids.mapped("estimated_hours"))
                if project_hours > budget_hours:
                    raise ValidationError(_("Project Allocated hours must not be more than Man-Hours in budget!"))

    def action_done(self):
        for record in self:
            record._check_project_budget()
        return super().action_done()

    def action_view_budget(self):
        self.ensure_one()
        action_window = {
            "type": "ir.actions.act_window",
            "res_model": "crossovered.budget",
            "name": "Budget",
            'view_type': 'form',
            'view_mode': 'tree,form',
            "context": {"default_project_id": self.id,"create": False,"edit": False,
                        'form_view_ref': 'project_budget.project_budget_custom_form',
                        'tree_view_ref': 'project_budget.project_budget_view_tree'},
            "domain": [('project_id', '=', self.id)]
        }
        return action_window


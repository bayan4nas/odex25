# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models, api, exceptions, _


class YearEmployeeGoals(models.Model):
    _name = 'years.employee.goals'
    _inherit = ['mail.thread']
    _description = 'years employee goals'
    _rec_name = 'kpi_id'

    kpi_id = fields.Many2one(comodel_name='kpi.item', string='KPI')
    description = fields.Text(string="Description")
    result_type = fields.Selection(related='kpi_id.result_type', string="KPI Type")
    result_appearance = fields.Selection(related='kpi_id.result_appearance', string="Measurement Standard")
    year_target = fields.Float(string='Target')
    done = fields.Float(string='Achieved')
    weight = fields.Float(string='Weight')
    self_assessment = fields.Float(string='Self Assessment')
    approved = fields.Float(string='Approved')
    result = fields.Float(string='Result', compute="_compute_goal_result", store=True)
    kpi_result = fields.Float(string='KPI Result', compute="_compute_goal_result", store=True)
    exceeds = fields.Float(string='Exceeds Expectations', compute="_compute_goal_result", store=True)
    employee_apprisal_id = fields.Many2one(comodel_name='hr.employee.appraisal')
    employee_id = fields.Many2one(related='employee_apprisal_id.employee_id')
    appraisal_stage_id = fields.Many2one(related='employee_apprisal_id.appraisal_stage_id')
    year_id = fields.Many2one(related='employee_apprisal_id.year_id')
    state = fields.Selection(related='employee_apprisal_id.state')
    appraisal_date = fields.Date(related='employee_apprisal_id.appraisal_date')
    goals_mark = fields.Float(related='employee_apprisal_id.goals_mark')
    is_last_stage = fields.Boolean(related='employee_apprisal_id.is_last_stage')
    is_direct_manager = fields.Boolean(related='employee_apprisal_id.is_direct_manager')
    is_appraisal_employee = fields.Boolean(related='employee_apprisal_id.is_appraisal_employee')
    can_see_appraisal_result = fields.Boolean(related='employee_apprisal_id.can_see_appraisal_result')
    last_stage = fields.Boolean(default=False)
    show_goal_result = fields.Boolean(compute="_compute_show_goal_result", store=True)
    Individual_kpi = fields.Char('Individual Indicator')
    remarks = fields.Text(string="Apprisal Remarks")
    comments = fields.Text(string="General Comments")
    appraiser_comments = fields.Selection([
        ('achieved', 'Achieved The Target"'),
        ('remedied', 'Below target can be remedied'),
        ('below', 'Below Target')], string='Appraiser Comments')

    change_justification = fields.Text(string="Change Justification")
    change_details = fields.Text(string="Change Details")

    @api.onchange('kpi_id')
    def _onchange_kpi_id(self):
        selected_kpis = self.employee_apprisal_id.goal_ids.mapped('kpi_id.id')
        return {'domain': {'kpi_id': [('id', 'not in', selected_kpis)]}}

    @api.depends('year_target', 'weight', 'done')
    def _compute_goal_result(self):
        for record in self:
            result = 0.0
            kpi_result = 0.0
            exceeds = 0.0
            if record.year_target:
                result = min(round((record.done / record.year_target) * 100, 0), 100)
                if record.done > record.year_target:
                    exceeds = round(((record.done - record.year_target) / record.year_target) * 100, 0)
                if record.result_type == 'less':
                    if record.done > record.year_target:
                        result = result - exceeds
                        exceeds = 0
                    else:
                        exceeds = round(((record.year_target - record.done) / record.year_target) * 100, 0)
                        result = 100 + exceeds
                        if record.done < record.year_target:
                            result = 100
                kpi_result = result * record.weight / 100

            record.result = result
            record.kpi_result = kpi_result
            record.exceeds = exceeds

    @api.onchange('kpi_id')
    def _onchange_kpi(self):
        for rec in self:
            rec.description = rec.kpi_id.description

    # def unlink(self):
    #     for record in self:
    #         if record.is_appraisal_employee:
    #             raise exceptions.ValidationError(_("Sorry, you are not allowed to delete indicators"))
    #     return super(YearEmployeeGoals, self).unlink()

    # @api.onchange('kpi_id')
    # def _compute_domain_kpi_id(self):
    #     """Restricts KPI selection to prevent duplicates within the same appraisal."""
    #     if self.employee_apprisal_id:
    #         selected_kpi_ids = self.employee_apprisal_id.goal_ids.mapped('kpi_id.id')
    #         return {'domain': {'kpi_id': [('id', 'not in', selected_kpi_ids)]}}
    #     return {'domain': {'kpi_id': []}}

    @api.constrains('year_target')
    def _check_year_target(self):
        for record in self:
            if record.year_target < 0:
                raise exceptions.ValidationError(
                    _("Year Target cannot be negative. Please enter a valid positive value."))

    @api.depends('employee_apprisal_id.goals_mark')
    def _compute_show_goal_result(self):
        for rec in self:
            rec.show_goal_result = bool(
                rec.employee_apprisal_id and rec.employee_apprisal_id.goals_mark > 0 and rec.employee_apprisal_id.goal_ids)

    @api.depends('year_target')
    def _compute_year_target(self):
        for rec in self:
            rec.balance_number3 = rec.year_target





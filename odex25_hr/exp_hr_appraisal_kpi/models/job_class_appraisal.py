from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class AppraisalPercentage(models.Model):
    _name = 'job.class.apprisal'
    _description = 'Appraisal Percentage'

    name = fields.Char('Name')
    percentage_kpi = fields.Float("Percentage of indicator Appraisal%")
    percentage_skills = fields.Float("Percentage of Skills Appraisal%")
    job_ids = fields.Many2many('hr.job', string='Jobs')
    skill_percentage_ids = fields.One2many('skill.percentage', 'class_id')
    max_no_goals = fields.Integer('Max no of Goals', tracking=True)
    min_no_goals = fields.Integer('Min no of Goals', tracking=True)
    max_goal_weight = fields.Integer('Max Goal Weight', tracking=True)
    min_goal_weight = fields.Integer('Min Goal Weight', tracking=True)

    @api.constrains('percentage_kpi', 'percentage_skills')
    def _check_percentage_total(self):
        for record in self:
            total_percentage = record.percentage_kpi + record.percentage_skills
            if total_percentage != 1:
                raise ValidationError(_("Total percentage should be 100."))
        if self.job_ids:
            for rec in self.job_ids:
                rec.appraisal_percentages_id = self.id


class SkillPercentage(models.Model):
    _name = 'skill.percentage'

    class_id = fields.Many2one('job.class.apprisal')
    skill_type_ids = fields.Many2many('skill.type', string='Skill Type')
    skill_percentage = fields.Float("skill Percentage %")

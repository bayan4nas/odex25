from odoo import api, fields, models, exceptions, _

class ProjectTaskSurvey(models.Model):
    _inherit = 'project.task'

    survey_id = fields.Many2one(
        comodel_name='survey.survey',
        string='Survey',
        required=False)
    response_id = fields.Many2one('survey.user_input', "Response", ondelete='set null', oldname="response")
    answer_count = fields.Integer("Registered", compute='_compute_answer_count')

    def _compute_answer_count(self):
        '''
            Count total answers Per Task
        '''
        for task in self:
            task.answer_count = self.env['survey.user_input'].search_count([('task_id', '=', task.id)])
    def action_start_survey(self):
        self.ensure_one()
        response = self.survey_id._create_answer(user=self.env.user, partner=self.env.user.partner_id, email=False, test_entry=False, check_attempts=True, task_id=  self.id )
        self.response_id = response.id
        return self.survey_id.action_start_survey(answer=response)
   
        # return self.survey_id.with_context(survey_token=response.access_token).action_start_survey()

    def action_survey_user_input_task(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Survey Responses'),
            'view_mode': 'tree,form',
            'res_model': 'survey.user_input',
            'domain': [('task_id', '=', self.id)],
            'context': {'create': False}
        }

class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    task_id = fields.Many2one('project.task', string='Project Task')

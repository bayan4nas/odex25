from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
from smtplib import SMTPRecipientsRefused
from email.utils import parseaddr
import logging
_logger = logging.getLogger(__name__)


class KPIPeriod(models.Model):
    _inherit = 'kpi.period'

    goals_stage_ids = fields.One2many('goals.stages', 'period_id')
    

    @api.constrains('date_start', 'date_end')
    def _check_overlapping_periods(self):
        for record in self:
            overlapping = self.search([
                ('id', '!=', record.id),
                ('date_start', '<=', record.date_end),
                ('date_end', '>=', record.date_start),
            ])
            if overlapping:
                raise ValidationError(_("This period overlaps with an existing period!"))

    def unlink(self):
        for item in self.goals_stage_ids:
            if item.status != 'not_start':
                raise ValidationError(_('You can not delete record in state not start'))
        return super(KPIPeriod, self).unlink()

    def name_get(self):
         """
         Overloading the method to remove period start and end ino the names
         """
         result = []
         for period in self:
             result.append((period.id, period.name))
         return result
         
class StagesGoals(models.Model):
    _name = 'goals.stages'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Name')
    sequence = fields.Integer('Sequence')
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    status = fields.Selection([
        ('not_start', 'Not Start'),
        ('running', 'Running'),
        ('closed', 'Closed')
    ], 'Status', default='not_start')
    period_id = fields.Many2one('kpi.period', ondelete='cascade')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    last_stage = fields.Boolean()

    @api.model
    def create(self, vals):
        if vals.get('period_id'):
            last_sequence = self.search([('period_id', '=', vals['period_id'])], order="sequence desc",
                                        limit=1).sequence
            vals['sequence'] = last_sequence + 1
        else:
            vals['sequence'] = 0
        return super(StagesGoals, self).create(vals)

    @api.onchange('period_id')
    def _onchange_period_id(self):
        if self.period_id:
            last_sequence = self.search([('period_id', '=', self.period_id.id)], order="sequence desc",
                                        limit=1).sequence
            self.sequence = last_sequence + 1

    @api.onchange("end_date")
    def onchange_data_from(self):
        if self.start_date and self.start_date > self.end_date:
            raise ValidationError(_("The Start Date must be less than the End Date"))

    @api.constrains('start_date', 'end_date', 'period_id')
    def _check_dates_within_period(self):
        for record in self:
            if record.period_id:
                if not (record.period_id.date_start <= record.start_date <= record.period_id.date_end):
                    raise ValidationError(_("The start date must be within the period's date range!"))
                if not (record.period_id.date_start <= record.end_date <= record.period_id.date_end):
                    raise ValidationError(_("The end date must be within the period's date range!"))
                if record.start_date > record.end_date:
                    raise ValidationError(_("The start date cannot be after the end date!"))

    @api.constrains('start_date', 'end_date')
    def _check_overlapping_periods(self):
        for record in self:
            overlapping = self.search([
                ('id', '!=', record.id),
                ('start_date', '<=', record.end_date),
                ('end_date', '>=', record.start_date),
            ])
            if overlapping:
                raise ValidationError(_("This period overlaps with an existing period!"))

    def send_appraisal_notification(self):
        template = self.env.ref('exp_hr_appraisal_kpi.email_template_appraisal_stage_notification')
        group = self.env.ref('hr_base.group_division_manager')

        if group:
            users = group.users.filtered(lambda u: u.partner_id.email)

            for partner in users.mapped('partner_id'):
                email = partner.email
                if not email or parseaddr(email)[1] != email:
                    # Skip invalid email addresses
                    _logger.warning(f"Skipping invalid email address: {email}")
                    continue

                if template:
                    try:
                        template.with_context(recipient_name=partner.name).sudo().send_mail(
                            self.id,
                            force_send=True,
                            email_values={
                                'email_from': self.env.user.partner_id.email or 'no-reply@yourdomain.com',
                                'email_to': email,
                                'partner_ids': [partner.id]
                            })
                    except SMTPRecipientsRefused as e:
                        # Skip this recipient and log the error
                        _logger.error(f"Failed to send email to {email}: {e}")
                    except Exception as e:
                        # Handle other possible errors
                        _logger.error(f"An error occurred while sending email to {email}: {e}")

    def create_appraisal_for_all_employees(self):
        employees = self.env['hr.employee'].search([('state', '=', 'open')])
        appraisal_records = []

        for employee in employees:
            appraisal = self.env['hr.employee.appraisal'].create({
                'employee_id': employee.id,
                'year_id': self.period_id.id,
                'appraisal_stage_id': self.id,
                'appraisal_date': fields.Date.today(),
                'state': 'draft',
            })
            appraisal.onchange_emp_job()
            appraisal.onchange_emp()
            appraisal_records.append(appraisal)

        return appraisal_records

    def start(self):
        self.ensure_one()
        previous_stages = self.search([
            ('sequence', '<', self.sequence),
            ('period_id', '=', self.period_id.id)
        ])
        incomplete_stages = previous_stages.filtered(lambda stage: stage.status == 'not_start')
        if incomplete_stages:
            raise ValidationError(_("You cannot start this stage until all previous stages are completed."))

        last_stage_record = self.search([
            ('period_id', '=', self.period_id.id)
        ], order="sequence desc", limit=1)

        self.last_stage = self.id == last_stage_record.id
        if self.last_stage and self.period_id:
            if self.end_date != self.period_id.date_end:
                raise ValidationError(_("The end date of the last stage must match the end date of the associated KPI period"))
        if self.sequence == 1:
            self.create_appraisal_for_all_employees()
        else:
            previous_stage = self.search([
                ('sequence', '=', self.sequence - 1),
                ('period_id', '=', self.period_id.id)
            ], limit=1)

            if previous_stage:
                self._copy_appraisals_from_previous_stage(previous_stage)

        # self.sudo().send_appraisal_notification()
        self.status = 'running'

    def _copy_appraisals_from_previous_stage(self, previous_stage):
        appraisal_model = self.env['hr.employee.appraisal']
        appraisals = appraisal_model.search([
            ('appraisal_stage_id', '=', previous_stage.id),
            ('year_id', '=', self.period_id.id)
        ])
        #  to be use in production evn
        # unapproved_appraisals = appraisals.filtered(lambda a: a.state != 'approved')
        # if unapproved_appraisals:
        #     raise ValidationError(_("All appraisals in the previous stage must be approved before copying."))

        for appraisal in appraisals:
            new_job_id = appraisal.employee_id.job_id.id
            if new_job_id == appraisal.job_id.id:
                self._copy_appraisal_with_same_job(appraisal)
            else:
                self._copy_appraisal_with_same_job(appraisal)

    def _copy_appraisal_with_same_job(self, appraisal):
        
        new_appraisal = appraisal.with_context(tracking_disable=True).copy({
            'appraisal_stage_id': self.id,
            'appraisal_date': fields.Date.today(),
            'state': 'draft',
            'job_id': appraisal.employee_id.job_id.id,
            
            })
        message = (_("Employee Appraisal Created"))
        new_appraisal.message_post(body=message, subtype_xmlid="mail.mt_note")

    def _copy_appraisal_with_new_job(self, appraisal, new_job_id):
        new_skill_ids = []
        new_skill_results = []
        new_skill_type_ids = []

        for line in appraisal.employee_id.job_id.item_job_ids:
            new_skill_ids.append((0, 0, {
                'item_id': line.item_id.id if line.item_id else False,
                'name': line.name,
                'skill_id': line.skill_id.id,
                'target': line.target or 0.0,
                'skill_type_id': line.skill_type_id.id if line.skill_type_id else False
            }))

            if line.skill_id:
                new_skill_results.append((0, 0, {
                    'skill_id': line.skill_id.id,
                    'skill_weight': 0.0,
                    'skill_result': 0.0
                }))

        if appraisal.appraisal_percentage_id:
            unique_skill_types = set()
            skill_type_lines = []

            for skill_percentage in appraisal.appraisal_percentage_id.skill_percentage_ids:
                skill_type_list = []

                for skill_type in skill_percentage.skill_type_ids:
                    if skill_type.id not in unique_skill_types and skill_type.id in [
                        line.skill_type_id.id for line in appraisal.employee_id.job_id.item_job_ids if
                        line.skill_type_id
                    ]:
                        unique_skill_types.add(skill_type.id)
                        skill_type_list.append(skill_type.id)

                if skill_type_list:
                    skill_type_lines.append((0, 0, {
                        'type_ids': [(6, 0, skill_type_list)],
                        'type_result': 0.00
                    }))

            new_skill_type_ids = skill_type_lines

        new_appraisal = appraisal.with_context(tracking_disable=True).copy({
            'appraisal_stage_id': self.id,
            'appraisal_date': fields.Date.today(),
            'state': 'draft',
            'job_id': new_job_id,
            'skill_ids': new_skill_ids,
            'skill_result_ids': new_skill_results,
            'skill_type_ids': new_skill_type_ids
        })
        message = (_("Employee Appraisal Created"))
        new_appraisal.message_post(body=message, subtype_xmlid="mail.mt_note")

    def close(self):
        self.status = 'closed'

    def unlink(self):
        for item in self:
            if item.status != 'not_start':
                raise ValidationError(_('You cannot delete a record in a state other than "not start"'))
        return super(StagesGoals, self).unlink()

    def name_get(self):
        """
        Overloading the method to include period start and end into the names
        with fixed date format: dd/mm/YYYY
        """
        result = []
        lang_date_format = "%d/%m/%Y"
        for period in self:
            date_start = period.start_date.strftime(lang_date_format) if period.start_date else ""
            date_end = period.end_date.strftime(lang_date_format) if period.end_date else ""
            name = "{} ({} - {})".format(period.name, date_start, date_end)
            result.append((period.id, name))
        return result
    #
    # def name_get(self):
    #      """
    #      Overloading the method to include period start and end ino the names
    #      """
    #      result = []
    #      lang = self._context.get("lang")
    #      lang_date_format = "%m/%d/%Y"
    #      if lang:
    #          record_lang = self.env['res.lang'].search([("code", "=", lang)], limit=1)
    #          lang_date_format = record_lang.date_format
    #      for period in self:
    #          date_start = period.start_date.strftime(lang_date_format)
    #          date_end = period.end_date.strftime(lang_date_format)
    #          name = "{} ({} - {})".format(period.name, date_start, date_end)
    #          result.append((period.id, name))
    #      return result

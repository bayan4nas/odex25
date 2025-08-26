from odoo import models, fields, api,_
from odoo.tools import mute_logger
from odoo.tools.translate import html_translate
from datetime import date, datetime, timedelta, time
from odoo.exceptions import ValidationError


class CustomJob(models.Model):
    _inherit = 'hr.job'  # assuming the original class name is 'hr.job'

    # @mute_logger('odoo.addons.base.models.ir_qweb')
    # def _get_default_website_description(self):
    #     # Custom implementation of _get_default_website_description
    #     return self.env['ir.qweb']._render("odex25_hr_recruitment_nafaz.default_website_description", raise_if_not_found=False)

    website_description = fields.Html(
        'Website description', translate=html_translate,
        default="", prefetch=False,
        sanitize_overridable=True,
        sanitize_attributes=False, sanitize_form=False)

    job_description = fields.Char(string='Job Summry')
    job_advantages = fields.Html(string='Job Advantages')
    job_location = fields.Char(string='Job Location')
    responspility = fields.Html(string='Responspilities')
    skill = fields.Html(string='Skills')
    experience = fields.Html(string='Experiences')
    close_date = fields.Date(string='Close Date',store=True, force_save=1)

    @api.constrains('close_date')
    def _check_close_date(self):
        for record in self:
            if record.close_date and record.close_date < date.today():
                raise ValidationError(_("The Close Date cannot be earlier than today"))

    @api.onchange('is_published')
    def _onchange_is_published(self):
        """ Prevent toggling 'is_published' when Job Description is empty """
        for job in self:
            if job.is_published and not job.job_description:
                # Reset toggle operation
                job.is_published = False
                raise ValidationError(_("You cannot publish a job without filling the Job Description"))

    @api.constrains('is_published', 'description')
    def _check_job_description(self):
        """ Additional backend check for job description """
        for job in self:
            if job.is_published and not job.job_description:
                raise ValidationError(_("You cannot publish a job without filling the Job Description"))







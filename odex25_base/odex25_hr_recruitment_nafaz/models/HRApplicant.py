# -*- coding: utf-8 -*-
from odoo import models, fields, api,_
from odoo.exceptions import ValidationError
from datetime import timedelta
import re
import logging

_logger = logging.getLogger(__name__)
SAUDI_MOBILE_PATTERN = r"^(009665|9665|\+9665|05|5)(5|0|3|6|4|9|1|8|7)([0-9]{7})$"


class Applicant(models.Model):
    _inherit = 'hr.applicant'

    user_number_id = fields.Char('ID Number')
    nationality = fields.Char('Nationality')
    gender = fields.Char('Gender')
    idExpiryDateHijri = fields.Char('ID Expiry Date Hijri')
    cardIssueDateGregorian = fields.Date('Card Issue Date Gregorian')
    dob = fields.Date('DOB')
    postOfficeBox = fields.Char('Post Office Box')
    localityName = fields.Char('Locality Name')
    buildingNumber = fields.Char('Building Number')
    street = fields.Char('Street')
    dobHijri = fields.Char('DOBHijri')
    englishName = fields.Char('English Name')

    @api.constrains('user_number_id', 'job_id','email_from','name')
    def _check_existing_application(self):
        for rec in self:
            existing_application = self.env['hr.applicant'].sudo().search([
                ('id', '!=', rec.id),  # Exclude the current record
                ('job_id', '=', rec.job_id.id),  # Same job
                '|',  # OR condition for user_number_id OR email OR partner_name
                ('user_number_id', '=', rec.user_number_id),  # Same user number
                '|',  # OR condition
                ('email_from', '=ilike', rec.email_from),  # Same email (case insensitive)
                ('name', '=ilike', rec.name)  # Same name (case insensitive)
            ], limit=1)
            # Check for existing application for the same job

            if existing_application:
                raise ValidationError(_('You have already applied for this job'))

    @api.constrains('create_date','user_number_id')
    def _check_recent_application(self):
        for rec in self:
            rate_limit_hours = 6
            rate_limit_period = fields.Datetime.now() - timedelta(hours=rate_limit_hours)
            recent_application = self.env['hr.applicant'].sudo().search(
                [('id', '!=', rec.id),('create_date', '>=', rate_limit_period),
                 '|',
                 ('user_number_id', '=', rec.user_number_id),
                 '|',
                 ('email_from', '=ilike', rec.email_from),
                 ('name', '=ilike', rec.name)  # Same name (case insensitive)
                 ],
                limit=1)
            if recent_application:
                raise ValidationError(_('Sorry, we have received too many applications forms recently. Please retry in after %s hours') % rate_limit_hours)

    @api.constrains("partner_phone")
    def check_mobile_value(self):
        if self.partner_phone:
            if re.match(SAUDI_MOBILE_PATTERN, self.partner_phone) is None:
                raise ValidationError(_("Enter a valid Saudi mobile number"))

    @api.constrains('user_number_id')
    def _check_user_number_id_format(self):
        for rec in self:
            if not rec.user_number_id.isdigit():
                raise ValidationError(_('User Number must contain only digits.'))
            if len(rec.user_number_id) != 10:
                raise ValidationError(_('User Number must be exactly 10 digits long.'))




# -*- coding: utf-8 -*-

from ..TaqnyatSms import client, make_http_response
from odoo import models, fields, api, _
from datetime import datetime, date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from dateutil.relativedelta import relativedelta as rd

from odoo.exceptions import UserError, ValidationError, Warning

import re

SAUDI_MOBILE_PATTERN = "(^(05|5)(5|0|3|6|4|9|1|8|7)([0-9]{7})$)"


class Partner(models.Model):
    _inherit = 'res.partner'

    def get_default_country(self):
        country = self.env["res.country"].search([('code','=','SA')],limit=1)
        return country.id
    def get_default_state(self):
        country = self.env["res.country.state"].search([('code','=','001')],limit=1)
        return country.id

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if not args:
            args = []

            # Extend the domain filter with custom search conditions
        domain = ['|', ('name', operator, name),('identification_number', operator, name)]

        # Combine domain filter with any existing args (domain filter in Many2one)
        partners = self.search(domain + args, limit=limit)

        return partners.name_get()

    account_type = fields.Selection(
        string='',
        selection=[ ('family','Family'),
                    ('sponsor', 'sponsor'),
                   ('benefit', 'Benefit')],
        required=False, )
    code = fields.Char(string="Code", copy=False)

    company_type = fields.Selection(selection_add=[('charity', _('Charity'))])
    first_name = fields.Char(string="First Name", tracking=True)
    second_name = fields.Char(string="Second Name", tracking=True)
    middle_name = fields.Char(string="Third Name", tracking=True)
    family_name = fields.Char(string="Family Name", tracking=True)
    name = fields.Char(string="Name", compute='get_partner_name', store=True,readonly = False)
    father_name = fields.Char(string="Father First Name", tracking=True)
    father_second_name = fields.Char(string="Father Second Name", tracking=True)
    father_third_name = fields.Char(string="Father Third Name", tracking=True)
    father_family_name = fields.Char(string="Father Family Name")
    birth_date = fields.Date()
    age = fields.Integer(string="Age", compute='_compute_get_age_date', store=True)
    iban = fields.Char("IBAN")
    bank_id = fields.Many2one('res.bank')
    id_number = fields.Char(string="Id Number", tracking=True)
    id_expiry = fields.Date(string="Id Expiry Date")
    gender = fields.Selection(selection=[('male', 'Male'), ('female', 'Female')], string="Gender")
    id_number_attach = fields.Binary(string="Id Number Attachment")
    health_status = fields.Selection(string='Health Status', selection=[('healthy', 'Healthy'), ('sick', 'Sick')])
    education_level = fields.Selection(
        string='Educational level',
        selection=[
            ('illiterate', 'Illiterate'),
            ('kindergarten', 'Kindergarten'),
            ('primary', 'Primary'),
            ('middle', 'Middle'),
            ('secondary', 'Secondary'),
            ('university', 'University'),
            ('postgraduate', 'Postgraduate'),
        ])
    education_institution = fields.Char()
    country_id = fields.Many2one('res.country',default=get_default_country)
    state_id = fields.Many2one('res.country.state',default=get_default_state)
    city_id = fields.Many2one('res.country.city',domain=[('state_id.code','=','001')])
    marital_status = fields.Selection(
        [('single', _('Single')), ('married', _('Married')), ('widower', _('Widower')), ('divorced', _('Divorced'))],
        _('Marital Status'))
    activation_mode = fields.Selection([
        ('sms', 'SMS'),
        ('email', 'Email')])
    user_type = fields.Selection([
        ('person', 'Person'),
        ('company', 'Company'),
        ('charity', 'Charity'),
    ])

    _sql_constraints = [
        ('mobile_uniq', 'unique (mobile)', 'The Mobile Already Exist!'),
        ('phone_uniq', 'unique (phone)', 'The Phone Already Exist!'),
        ('user_id_uniq', 'unique (user_id)', 'The User Already Exist!'),
    ]

    # @api.depends('father_family_name')
    # def get_partner_name(self):
    #     for rec in self:
    #         if rec.father_family_name:
    #             rec.name = rec.father_family_name
    @api.depends('company_type', 'first_name', 'second_name', 'middle_name', 'family_name', 'father_name',
                 'father_second_name', 'father_third_name', 'father_family_name')
    def get_partner_name(self):
        for rec in self:
            if rec.company_type == 'person':
                rec.name = ''
                if all([rec.second_name, rec.first_name, rec.middle_name, rec.family_name]):
                    rec.name = rec.first_name + " " + rec.second_name + " " + rec.middle_name + " " + rec.family_name
                elif all([rec.father_name, rec.father_second_name, rec.father_third_name, rec.father_family_name]):
                    rec.name = rec.father_name + " " + rec.father_second_name + " " + rec.father_third_name + " " + rec.father_family_name
            else:
                rec.second_name = ''
                rec.first_name = ''
                rec.middle_name = ''
                rec.family_name = ''

    # Function Get age by birthdate
    @api.depends('birth_date')
    def _compute_get_age_date(self):
        for rec in self:
            if rec.birth_date:
                today = date.today()
                day = datetime.strptime(str(rec.birth_date), DEFAULT_SERVER_DATE_FORMAT)
                age = rd(today, day)
                rec.age = age.years

    # Validate mobile ..
    # @api.constrains('mobile')
    # def check_mobile_value(self):
    #     if self.mobile:
    #         if re.match(SAUDI_MOBILE_PATTERN, self.mobile) == None:
    #             raise ValidationError(
    #                 _('Enter a valid Saudi mobile number'))

    @api.onchange('mobile', 'country_id', 'company_id')
    def _onchange_mobile_validation(self):
        if self.mobile:
            if self.mobile.startswith('+966'):
                mobile = self.mobile[4:]
                self.mobile = mobile
            if re.match(SAUDI_MOBILE_PATTERN, self.mobile) == None:
                raise ValidationError(
                    _('Enter a valid Saudi mobile number'))

    # @api.multi
    def send_sms_notification(self, body=None, phone=None):
        self.ensure_one()

        if not phone:
            phone = self.mobile

        if not all([phone, body]):
            return False

        if re.match(SAUDI_MOBILE_PATTERN, str(phone)) == None:
            return False

        company_id = self.env.user.company_id or self.env['res.company'].sudo().search([('id', '=', 1)])

        if company_id and company_id.use_sms_notification:
            token = company_id.sms_provider_token or ''
            sender = company_id.sms_sender_name or ''
            if token and sender:

                taqnyt = client(token)
                mobile = '966' + str(phone).lstrip('0')

                recipients = [mobile]
                scheduled = ''
                # Sending a SMS for a Notification
                message = taqnyt.sendMsg(body, recipients, sender, scheduled)

                result = make_http_response(message)

                code = int(result['statusCode'])
                total_count = int(result['totalCount'])
                msg = result['message']

                if code == 201 and total_count >= 1:
                    return True
                else:
                    return False
            else:
                return False
        else:
            return False

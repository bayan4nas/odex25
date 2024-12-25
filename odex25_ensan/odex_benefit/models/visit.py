from odoo import fields, models,api,_
import math, random
from odoo.exceptions import UserError, ValidationError

class Visit(models.Model):
    _name = 'visit.location'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    benefit_type = fields.Selection([
        ('benefit', 'Benefit'),
        ('family', 'Family'),
    ], string='Type', default="benefit")
    benefit_id = fields.Many2one(
        'grant.benefit',string='Family file',domain="[('state', '=', 'second_approve')]")
    benefit_name = fields.Char(related="benefit_id.name")
    benefit_code= fields.Char(related="benefit_id.code")
    researcher_team = fields.Many2one("committees.line", string="Researcher Team",related="benefit_id.researcher_id")
    researcher_ids = fields.Many2many("hr.employee", string="Researcher",compute="get_researcher_ids",readonly=False)
    visit_date = fields.Datetime(string='Visit Date')
    description = fields.Char(string='Description')
    message = fields.Text(string='Message')
    visit_objective = fields.Selection([
        ('inform_visit', 'Inform Visit'),
        ('objective_visit', 'Objective Visit'),
        ], string='Visit Objective')
    visit_types = fields.Many2one(
        'visits.types',
        string='Visits Types')
    contact_type = fields.Selection([
        ('email', 'Email'),
        ('sms', 'SMS'),
        ], string='Contact Type')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('contact', 'Contact'),
        ('schedule_a_visit', 'Schedule a visit'),
        ('done', 'Done'),
        ('cancel', 'Cancel'),
        ('close', 'Close'),
    ], string='State',default="draft")
    family_id = fields.Many2one('benefit.family')
    reason = fields.Text(string='Reason/Justification')
    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, index=True,
                       default=lambda self: _('New'))
    def unlink(self):
        for order in self:
            if order.state not in ['draft']:
                raise UserError(_('You cannot delete this record'))
        return super(Visit, self).unlink()
    @api.model
    def create(self, vals):
        # If the 'name' field is 'New', generate a new sequence number
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('visit.location.sequence') or _('New')
        return super(Visit, self).create(vals)

    def get_researchers_email(self):
        email_ids = ''
        for rec in self.researcher_ids:
            if email_ids:
                email_ids = email_ids + ',' + str(rec.work_email)
            else:
                email_ids = str(rec.work_email)
        return email_ids
    def action_draft(self):
        self.state = 'draft'

    def action_contact(self):
        self.state = 'contact'
        if self.contact_type == 'email':
            template = self.env.ref('odex_benefit.schedule_a_visit_email_template', False)
            if not template:
                return
            template.with_context(lang=self.env.user.lang).send_mail(self.id, force_send=True,
                                                                     raise_exception=False)
        elif self.contact_type == 'sms':
             self.benefit_id.partner_id.send_sms_notification(self.message, self.benefit_id.sms_phone)

    def action_schedule_a_visit(self):
        self.state = 'schedule_a_visit'
    def action_cancel(self):
        for rec in self:
            rec.state = 'cancel'
    def action_done(self):
        self.state = 'done'
        self.benefit_id.last_visit_date = self.visit_date
        if self.contact_type == 'email':
            body = self.generateOTP()
            mail = self.env['mail.mail'].create({
                'body_html': body,
                'subject': "Visit Confirmation",
                'email_to': self.benefit_id.email,
                # 'email_cc': self.benefit_id.email,
            })
            mail.send()
        elif self.contact_type == 'sms':
             self.benefit_id.user_id.sudo().request_otp(self.benefit_id.sms_phone)
    def action_close(self):
        survey_url = ''
        survey_conf = self.env['survey.setting'].search([],limit=1)
        if survey_conf:
            survey_url = survey_conf.survey_url
            survey_url = ' <a href=#survey link>%s</a>' % (survey_url)
        self.state = 'close'
        if self.contact_type == 'email':
            body = survey_url
            mail = self.env['mail.mail'].create({
                'body_html':survey_url ,
                'subject': "Visit Close",
                'email_to': self.benefit_id.email,
                # 'email_cc': self.researcher_id.work_email,
            })
            mail.send()
        elif self.contact_type == 'sms':
             self.benefit_id.partner_id.send_sms_notification(survey_url , self.benefit_id.sms_phone)
    @api.depends("researcher_team")
    def get_researcher_ids(self):
        for rec in self:
            rec.researcher_ids = rec.researcher_team.employee_id
    def send_visit_date_email(self):
        template = self.env.ref('odex_benefit.visit_date_email', False)
        if not template:
            return
        template.with_context(lang=self.env.user.lang).send_mail(self.id, force_send=True, raise_exception=False)

    # function to generate OTP
    def generateOTP(self):
        digits = "0123456789"
        OTP = ""

        # length of password can be changed
        # by changing value in range
        for i in range(4):
            OTP += digits[math.floor(random.random() * 10)]

        return OTP

    def geo_localize(self):
        for visit in self:
            if visit.benefit_id:
                url = "http://maps.google.com/maps/search/?api=1&query=%s,%s" % (visit.benefit_id.lat,visit.benefit_id.lon),
                return {
                    'type': 'ir.actions.act_url',
                    'target': 'new',
                    'url': url
                }

    def get_url_local(self):
        for visit in self:
            if visit.benefit_id:
                url = "http://maps.google.com/maps/search/?api=1&query=%s,%s" % (visit.benefit_id.lat,visit.benefit_id.lon)
                return url
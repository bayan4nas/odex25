# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError

class TakafulMessageTemplate(models.Model):
    _name = "takaful.message.template"
    _description = "Message Template"
    _rec_name = 'title'

    title = fields.Char(string='Subject')
    body = fields.Text(string='Message', required=True)
    template_name = fields.Char('Template Name', readonly=True, copy=False)

    _sql_constraints = [
        ('template_name_uniq', 'unique (template_name)', 'Template Name Is Already Exist!')
    ]


class TakafulPushNotification(models.Model):
    _name = 'takaful.push.notification'
    _description = 'Push Notification'

    user_id = fields.Many2one('res.users', string="Sponsor User", required=True)
    email = fields.Char(string='Email', related='user_id.login',store=True)
    mobile = fields.Char(string='Mobile', related='user_id.phone',store=True)

    title = fields.Char(string='Subject')
    body = fields.Text(string='Message', required=True)
    sent_on = fields.Datetime(string="Sent On", default=fields.Datetime.now)

    is_read = fields.Boolean(string="Seen", default=False)

    # @api.multi
    def send_sms_notification(self):
        self.ensure_one()
        return self.user_id.partner_id.sudo().send_sms_notification(body=self.body, phone=self.mobile)

    # @api.multi
    def send_email_notification(self):
        self.ensure_one()
        if not all([self.email, self.body]):
            # Missing email message information"
            return False
        
        email_from = self.env.user.company_id.email
        company_name = self.env.user.company_id.name

        template_id = self.env.ref('odex_takaful.push_notification_email_template').id
        context = {
           'email_from': email_from,
           'email_to': self.email,
           'partner_name': self.user_id.partner_id.name,
           'body': self.body,
           'title': self.title or _("Notification"),
           'company_name': company_name
        }
        try:
            # Start to SEND Email
            self.env['mail.template'].browse(template_id).with_context(context).send_mail(self.id, force_send=True)
        except Exception as e:
            return False
        
        """
        And getting the values (context) in email template 
        ${ctx.get('your_key')}
        """
        # Email is SENT ...
        return True

    # @api.multi
    def send_all(self):
        self.ensure_one()
        for tool in self.notification_type_ids:
            if tool.tool_type == "sms":
                sms = self.send_sms_notification()
                if sms:
                    print("SMS is sent.")

            elif tool.tool_type == "app":
                print("App message is sent.")
       
            elif tool.tool_type == "email":
                email= self.send_email_notification()
                if email:
                    print("Email is sent.")

            






from odoo import models, api
import re


class MailActivity(models.Model):
    _inherit = 'mail.activity'


    @api.model
    def create(self, values):
        activity_ids = super(MailActivity, self).create(values)
        for activity_id in activity_ids:
            # Build message content
            # Ensure activity_id.note is valid and avoid errors
            note = activity_id.note or ''
            notification_body = re.sub(r'<[^>]+>', '', note.replace('<br>', '\n'))

            # Send notifications
            employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', activity_id.user_id.id)])
            if employee_id:
                push_notify = employee_id.user_push_notification_web({
                    "title": activity_id.summary or activity_id.create_uid.name,
                    "body": notification_body
                })
        return activity_ids

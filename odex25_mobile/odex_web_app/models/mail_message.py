from odoo import models, api
import re


class Message(models.Model):
    _inherit = 'mail.message'


    @api.model_create_multi
    def create(self, values_list):

        mt_comment = self.env.ref('mail.mt_comment')
        mt_note = self.env.ref('mail.mt_note')
        messages = super(Message, self).create(values_list)
        for message in messages.filtered(lambda r: r.subtype_id.id in (mt_comment.id, mt_note.id) and r.model != 'mail.channel' and r.message_type != 'user_notification'):
            # Get partners that should receive the message
            if message.subtype_id.id == mt_comment.id:
                partner_ids = self.env['mail.followers'].sudo().search([
                    ('res_model', '=', message.model), 
                    ('res_id', '=', message.res_id),
                    ('partner_id', '!=', message.author_id.id)
                ]).partner_id
            elif message.subtype_id.id == mt_note.id:
                partner_ids = message.partner_ids
            else:
                partner_ids = []
            
            if len(partner_ids):
                # Build message content
                notification_body = re.sub(r'<[^>]+>', '', message.body.replace('<br>', '\n'))
                attachments = len(message.attachment_ids)
                if notification_body and attachments:
                    notification_body += '\n{} File(s)'.format(attachments)
                elif attachments:
                    notification_body = '{} File(s)'.format(attachments)
                
                # Send notifications
                for employee_id in self.env['hr.employee'].sudo().search([('user_id', 'in', partner_ids.user_ids.ids)]):
                    push_notify = employee_id.user_push_notification_web({
                        "title": message.author_id.name,
                        "body": notification_body
                    })
        return messages
from odoo import fields, models, api


class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'


    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, *, message_type='notification', **kwargs):
        if self._name in ['mail.channel']:
            notification_body = kwargs.get('body', '')
            attachments = len(kwargs.get('attachment_ids', []))
            if notification_body and attachments:
                notification_body += '\n{} File(s)'.format(attachments)
            elif attachments:
                notification_body = '{} File(s)'.format(attachments)
                
            partners_to_notify = self.channel_partner_ids.filtered(lambda r: r.id != self.env.user.partner_id.id)
            if self.public == 'private':
                for employee_id in self.env['hr.employee'].sudo().search([('user_id', 'in', partners_to_notify.user_ids.ids)]):
                    custom_title = self.channel_last_seen_partner_ids.filtered(lambda r: r.partner_id.id == employee_id.user_id.partner_id.id)
                    push_notify = employee_id.user_push_notification_web({
                        "title": custom_title.custom_channel_name or self.env.user.partner_id.name,
                        "body": notification_body
                    })
            else:
                for employee_id in self.env['hr.employee'].sudo().search([('user_id', 'in', partners_to_notify.user_ids.ids)]):
                    push_notify = employee_id.user_push_notification_web({
                        "title": self.display_name,
                        "body": notification_body
                    })
                
        return super(MailThread, self).message_post(message_type=message_type, **kwargs)
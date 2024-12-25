import json
import requests
import logging

from odoo import models, fields, api
_logger = logging.getLogger(__name__)

class Partner(models.Model):
    _inherit = 'res.partner'

    firebase_registration_ids = fields.One2many(
        "firebase.registration", "partner_id", readonly=True
    )

    def send_msg(self, partner_ids, msg, subject):
        emp = self.env['hr.employee'].sudo().search([('user_id', 'in', partner_ids.user_ids.ids)])
        if emp.user_id.partner_id:
            partner_id = emp.user_id.partner_id
            # partner_id.send_notification(subject, msg, data=None, all_device=True)
            data = {
                'title':subject,
                'body':msg,
            }
            emp.user_push_notification(data)
    def send_notification(self, message_title, message_body, data=None, all_device=True):
        notification_data = {
            "title": str(message_title),
            "body": str(message_body),
            "meta": json.dumps(data) if data else None,
            "partner_ids": [(4, self.id)],
            "is_system": True,
            "sent": True,
        }
        notification = self.env['firebase.notification'].sudo().create(notification_data)
        
        if all_device:
            self.send_msg(notification.partner_ids,str(message_title),str(message_body))
            for reg in self.firebase_registration_ids:
                reg.with_context(lang=self.lang).send_message(
                    message_title, 
                    message_body, 
                    data={
                        "title": str(message_title),
                        "body": str(message_body),
                        "meta": json.dumps(data) if data else None,
                        "is_system": "true",
                        'viewed': "false",
                        "sent": "true",
                        "data": str(notification.create_date),
                        "id": str(notification.id)
                    }
                )
        else:
            if self.firebase_registration_ids:
                self.firebase_registration_ids[0].with_context(lang=self.lang).send_message(
                    message_title, 
                    message_body, 
                    data=data
                )

    def user_push_notification(self, fcm_token):
        url = "https://fcm.googleapis.com/fcm/send"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'key={self.env.user.company_id.fcm_server_key}'
        }
        body = json.dumps({
            "to": fcm_token,
            "direct_boot_ok": True,
            "notification": {
                "title": "Test",
                "body": "test"
            }
        })
        try:
            response = requests.post(url=url, data=body, headers=headers)
            response.raise_for_status()
            return True
        except requests.exceptions.RequestException as e:
            _logger.error(f"Failed to send push notification: {e}")
            return False

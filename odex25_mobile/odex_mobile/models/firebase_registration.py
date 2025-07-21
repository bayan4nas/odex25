import logging

from odoo import api, models, fields
from odoo.tools import config

import datetime

_logger = logging.getLogger(__name__)

try:
    import firebase_admin
    from firebase_admin import credentials
    from firebase_admin import messaging
except ImportError as e:
    _logger.warning("Please install the PIP package firebase_admin")

try:
    firebase_credentials = credentials.Certificate(
        {
            "type": "service_account",
            "project_id": "odex-ss",
            "private_key_id": "c8b14f9b17b7e1ec33dc34dc0b0842f0e8d1dd9e",
            "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvAIBADANBgkqhkiG9w0BAQEFAASCBKYwggSiAgEAAoIBAQC/jbxf2zxxxD+t\nDTT1joFiI0n7MccnpbeEv22c0Aaro8ZBE3oiBCUkfpF2K5Rww01jfY+dbRMuZOFy\nQwzFZtV6KLrVjq2298TFeExqI8ryaLz3ymOGY8QgwBQdN/7BFGXtgwg4z3zHGToi\nbSaWa8AM55/ayFUA+WLjcmytdp+29x8WagFatj24bVfmHRCvxHGP1/6/CNkbg/g1\nW2MzpJkvt5VK5R+o+oXP+w+NEnq8NuZgwOlUw9yJ0bL0uQA24CaqrBCljSERGGIU\nvrosi0BFAsnuY/bROy7iDAT2Z8u9B3k3izbDplNBgaPYI9jisTyODR9M78rvfs/I\n1hyjDqaHAgMBAAECggEAScDXamr902n2AHnozbFQVMp0lkC8xyGxzu1r1WhtYRHe\naDkJGebRrEMFW+P8tAwmlGuIa9tO+tqByV5SoQDuqinbghV9AklU3JlshqOAZSR5\nuciV2G06W0fJltR0BMCHXFNKy6DsELbAYPf41wrmt7FJJdJjlEvxTNTGTmWxqh7C\nk+pqrevRY/+dawrNZXjEviOLygCVgWzKAKVZk24vdAgcwYECj5K+z4KNP2Lx0kNL\nmBuMz9PHi2cP//TAQPlwous2AhMs5kUv1qhONcGPoKXb24w2L517hWEj9g+9hH+3\n6L9Bmgn/pE9TW8hSJXSQAyWtzoOqmbbBQNUvIJ3PvQKBgQDmQE4dbTdDsHHbBz6X\nmsxCOHpwCU9dFsgMJEsxhhOLQAHKte0BCt42WCQlc7Utn2jIWKKJdvMJ1v8v4Y2x\n/U7WDEu9/N6mkromLLrL+LR5n0py3d1eqlcWQLG1Cwx5zcPk3qxn5XHyG0JLWmIC\nQJN3707xXNtL9XhEEaYweNaDOwKBgQDU+ZZAS/allYN3Hyg+pxWsyxBfiLOE2ttJ\ncbK9KDMdoPzI6rq1tG6daVQAsCa5B8sMwV6MjWyDZCzgbmSEfU9/HFS83dc8vXXi\n9FM8uJJOkO1zTLoYJBgihfbMkmlMpYK/8Q1paum9NZPFzh2nUXBui7QR9yWA2tCw\nqJlWSpAdJQKBgBHxQuUSJLNWpZiu2NbRjkc+xXPDlfaoFtCzZ1SloRJB26HjSWPC\naAyOE8sDWEQE3xJ1rbzOkyPaKCqgBf2vwpv1e1WDxgnu9yiQZcINUGsF2bRXy69b\n0MuAIRj9kmxPd4t3OrIh9B4st57NnUOVqqg28szmMoSZzVRol63BTN4PAoGAYmGR\nOM5ed4sjmal468g/SPzc6WS6mMqItdqh2KNzSWKOozlbWoio+Gopdc/pc1vYPmIt\nDPxffiqOWHZmVJWWXX923XAU92gFxvtaYBha7ZQhPDvbUz+JLpl3snSH0/I4/fWa\nXnIW22Keiqd2J06Fg2thmVLzrhxmftTDUItNG0kCgYB5svHGa/cY+peyzBxaXkOg\n4l5yxV2h96nyrO/HSD3FQVywGlUCdVyec/j0PPolyXM/qb1gKkvICqKs+R9cy46R\nqzTpS6aD7sa/z4mC0eXlKM7vpUqb9g3VNt4PerrLbSzrfDe5oxHQIg0gQJ5O0e82\nND/ZMssVB29xPKFBP5nbbg==\n-----END PRIVATE KEY-----\n",
            "client_email": "firebase-adminsdk-ij0mq@odex-ss.iam.gserviceaccount.com",
            "client_id": "113036549506173208284",
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-ij0mq%40odex-ss.iam.gserviceaccount.com"
        }
    )
    firebase_app = firebase_admin.initialize_app(
        credential=firebase_credentials)
except (KeyError, ValueError) as e:
    firebase_app = None
    _logger.warning(
        "google_application_credentials is not correctly configured "
    )


class FirebaseRegistration(models.Model):

    _name = "firebase.registration"
    _description = "Device registered with FCM"
    _rec_name = "topic_id"

    topic_id = fields.Char(required=True, string="Firebase Topic",
                           compute='_generate_topic_id', readonly=True)
    partner_id = fields.Many2one(
        "res.partner", string="Partner", readonly=False)
    partner_name = fields.Char(related="partner_id.name", readonly=True)

    def _generate_topic_id(self):
        for notif in self:
            notif.topic_id = "ch_{}".format(notif.partner_id.id)

    def send_message_from_interface(self):
        self.send_message(
            self.env.context.get(
                "message_title"), self.env.context.get("message_body")
        )


    #@api.multi
    def send_message(self, message_title, message_body, data=None):
        if data is None:
            data = {}
        if not firebase_app:
            _logger.error(
                "google_application_credentials is not correctly "
                "configured in odoo.conf or invalid. Skipping "
                "sending notifications"
            )
            return False

        notif = messaging.Notification()
        for firebase_id in self:
            
            data.update({"title": message_title, "body": message_body, "click_action":"FLUTTER_NOTIFICATION_CLICK"})
            message = messaging.Message(
                data=data,
                topic=firebase_id.topic_id,
                android=messaging.AndroidConfig(
                    ttl=datetime.timedelta(seconds=3600),
                    priority='high',
                    notification=messaging.AndroidNotification(
                        click_action="FLUTTER_NOTIFICATION_CLICK",
                        title=message_title,
                        body=message_body
                    ),
                ),
                # apns=messaging.APNSConfig(
                #     headers={'apns-priority': '10'},
                #     payload=messaging.APNSPayload(
                #         aps=messaging.Aps(
                #             alert=messaging.ApsAlert(
                #                 title=message_title,
                #                 body=message_body,
                #             ),
                #             badge=42,
                #         ),
                #     ),
                # ),
            )
            try:
                messaging.send(message=message)
            except (
                    messaging.QuotaExceededError,
                    messaging.SenderIdMismatchError,
                    messaging.ThirdPartyAuthError,
                    messaging.UnregisteredError,
            ) as ex:
                _logger.error(ex)
                self.env["ir.logging"].create(
                    {
                        "name": "Firebase " + ex.__class__.__name__,
                        "type": "server",
                        "message": ex,
                        "path": "/rest_api/models/firebase_regitration.py",
                        "line": "100",
                        "func": "send_message",
                    }
                )
                if ex.code == "NOT_FOUND":
                    _logger.debug(
                        "A Topic is not avaliable from Firebase."
                        "Firebase Topic: %s" % firebase_id
                    )
        return True

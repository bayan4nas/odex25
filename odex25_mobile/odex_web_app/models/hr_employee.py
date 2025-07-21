# -*- coding: utf-8 -*-
from odoo import models, fields
import json, requests, base64
import google.auth.transport.requests
from google.oauth2 import service_account
import io
import tempfile
import os


BASE_URL = 'https://fcm.googleapis.com'
SCOPES = ['https://www.googleapis.com/auth/firebase.messaging']


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    device_id = fields.Char(string="Employee Device ")
    fcm_token_web = fields.Char(string='FCM Web Token')


    def user_push_notification_web(self, notification):

        def _get_access_token(json_file):
            """Retrieve a valid access token that can be used to authorize requests.

            :return: Access token.
            """
            credentials = service_account.Credentials.from_service_account_file(
                json_file, scopes=SCOPES)
            request = google.auth.transport.requests.Request()
            credentials.refresh(request)
            return credentials.token
        
        try:
            json_file_name = 'service-account'
            base64_service_account = base64.decodebytes(self.env.user.company_id.service_account)
            service_account_json = json.loads(base64_service_account)
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_file_path = os.path.join(temp_dir, json_file_name)
                with open(temp_file_path, 'w') as temp_file:
                    temp_file.write(base64_service_account.decode('UTF-8'))
                header = {
                    'Content-Type': 'application/json',
                    'Authorization': 'Bearer %s' % (_get_access_token(temp_file_path))
                }
                body = json.dumps({
                    "message": {
                        "token": self.fcm_token_web,
                        "notification": notification,
                        "android": {
                            "notification": {
                                "sound": "default"
                            }
                        },
                        "apns": {
                            "payload": {
                                "aps": {
                                    "sound": "default"
                                }
                            }
                        }
                    }
                })
                FCM_ENDPOINT = 'v1/projects/' + service_account_json['project_id'] + '/messages:send'
                FCM_URL = BASE_URL + '/' + FCM_ENDPOINT
                respons = requests.post(url=FCM_URL, data=body, headers=header)
            return True
        except Exception as e:
            return False



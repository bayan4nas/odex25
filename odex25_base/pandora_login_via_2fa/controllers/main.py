import odoo
import json
import logging
import urllib.parse
from datetime import datetime, timedelta
import requests
import werkzeug

from odoo import http
from odoo.http import request
import random
import re

from werkzeug.urls import url_encode

from odoo import http
from odoo.modules import module
from odoo.http import request
from odoo.tools.translate import _

import smtplib
import ssl
from email.message import EmailMessage

_logger = logging.getLogger(__name__)

class ApiMain(http.Controller):
    
    def get_api_config(self, mobile='', otp=''):
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        config_model = request.env['login.api.config'].sudo().search([('default','=',True)], limit=1)
        replaced_config = config_model.get_config_with_replacements(base_url, mobile, otp)
        return replaced_config
    
    def remove_special_characters(self, number):
        # Remove all non-digit characters from the number
        return re.sub(r'\D', '', number)
    
    def hide_phone_number(self, phone_number):
        """Hide sensitive information in phone number."""
        if len(phone_number) < 2:
            return phone_number
        else:
            return '*' * (len(phone_number) - 2) + phone_number[-2:]

    def hide_email(self, email):
        """Hide sensitive information in email address."""
        if '@' in email:
            username, domain = email.split('@')
            if len(username) < 2:
                hidden_username = '*' * len(username)
            else:
                hidden_username = username[:2] + '*' * (len(username) - 2)
            return f"{hidden_username}@{domain}"
        else:
            return email  # Not a valid email address

    def send_sms(self, number, otp):
        config = self.get_api_config(number, otp)
        api_url = config.get('url')
        headers = config.get('headers')
        payload = None
        if config.get('method') == 'post':
            payload = config.get('body')
        # elif config.get('method') == 'get':
        try:
            response = requests.post(api_url, headers=headers, data=json.dumps(payload))
            return response.text  # Return failure status and error message
        except Exception as e:
            return [False, str(e)]  # Return failure status and exception message

    def send_mail(self, send_to, otp):
        try:
            config = self.get_api_config('', otp)
            params = {
                "MAIL_FROM": config.get('mail_from'),
                "MAIL_SERVER": config.get('mail_server'),
                "MAIL_PORT": config.get('mail_port'),
                "MAIL_PASSWORD": config.get('mail_pwd'),
            }
            msg = EmailMessage()
            msg.set_content(config.get('mail_otp_msg'))
            msg['Subject'] = f"{config.get('mail_subject_start_with')} - OTP"
            msg['From'] = f"{config.get('mail_subject_start_with')} <{params['MAIL_FROM']}>"
            msg['To'] = send_to

            context = ssl.create_default_context()
            with smtplib.SMTP(params["MAIL_SERVER"], params["MAIL_PORT"]) as smtpObj:
                smtpObj.starttls(context=context)
                smtpObj.login(params["MAIL_FROM"], params["MAIL_PASSWORD"])
                smtpObj.send_message(msg)
            
            return [True, "Your mail was sent successfully!"]
        except Exception as e:
            print("\n\n\n *********************** \n\n\n", str(e) , "\n\n\n *********************** \n\n\n")
            return [False, str(e)]

    def get_req_user_agent(self, user_agent):

        # Define patterns to match browser and device names
        browser_patterns = {
            'Chrome': re.compile(r'Chrome'),
            'Safari': re.compile(r'Safari'),
            'Firefox': re.compile(r'Firefox'),
            'Edge': re.compile(r'Edge'),
            'IE': re.compile(r'Trident'),
            'Opera': re.compile(r'OPR'),
        }

        device_patterns = {
            'iPhone': re.compile(r'iPhone'),
            'iPad': re.compile(r'iPad'),
            'Android': re.compile(r'Android'),
            'WindowsPhone': re.compile(r'Windows Phone'),
            'BlackBerry': re.compile(r'BlackBerry'),
            'Mac': re.compile(r'Macintosh|Mac OS'),
            'Windows': re.compile(r'Windows NT'),
            'Linux': re.compile(r'Linux'),
        }

        # Function to find the match from the given pattern
        def find_match(patterns):
            for name, pattern in patterns.items():
                if pattern.search(user_agent):
                    return name
            return 'Unknown'

        # Get browser and device names
        browser = find_match(browser_patterns)
        device = find_match(device_patterns)

        # Return browser, device, and user agent information
        return {
            'browser': browser,
            'device': device,
            'user_agent': user_agent,
            'name': f"{device} {browser}"
        }
        
    @http.route('/api/auth/login', type='json', auth='public', methods=['POST'], csrf=False)
    def auth_login(self, email, password, auth_token):
        try:
            uid = request.session.authenticate(request.session.db, email, password)
            if uid is not False:
                user = request.env['res.users'].sudo().browse(uid)
                user_tokens = [td.token for td in user.truested_devices_ids]
                if user and (auth_token in user_tokens or (user.ask_for_email_otp == False and user.ask_for_phone_otp == False)):
                # if user and (user.remember_me_token == auth_token or (user.ask_for_email_otp == False and user.ask_for_phone_otp == False)):
                    return { 'success': True, 'message': 'logged in successfully!', 'skip_otp':True }
                request.session.logout()
                otp_sources = []
                
                employee_id = request.env['hr.employee'].sudo().search([('user_id','=',user.id)], limit=1)
                
                if user and employee_id:
                    phone1 = self.remove_special_characters((employee_id.mobile_phone or ''))
                    phone2 = self.remove_special_characters((employee_id.work_phone or ''))
                    email = (employee_id.work_email or '')
                    if phone1 not in ('',False,None) and user.ask_for_phone_otp:
                        otp_sources.append({ "method":"mobile_phone", "source":self.hide_phone_number(phone1) })
                        
                    if phone2 not in ('',False,None) and user.ask_for_phone_otp:
                        otp_sources.append({ "method":"work_phone", "source":self.hide_phone_number(phone2) })
                        
                    if email not in ('',False,None) and user.ask_for_email_otp:
                        otp_sources.append({ "method":"work_email", "source":self.hide_email(email)})
                        
                    if len(otp_sources)>0:
                        return { 'success': True, 'message': 'Please Choose OTP Source!', 'otp_sources':otp_sources }
                    else:
                        return { 'success': False, 'message': "No OTP source found please contact your administrator!" }
                else:
                    return {'success': False, 'message': 'Phone Number doesn\'t exist!'}
            return {'success': False, 'message': 'Invalid credentials!'}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    @http.route('/api/auth/send/otp', type='json', auth='public', methods=['POST'], csrf=False)
    def auth_send_otp(self, email, password, otp_type):
        try:
            uid = request.session.authenticate(request.session.db, email, password)
            if uid is not False:
                user = request.env['res.users'].sudo().browse(uid)
                request.session.logout()
                employee_id = request.env['hr.employee'].sudo().search([('user_id','=',user.id)], limit=1)
                
                if user and employee_id:
                    
                    otp = str(random.randint(1000, 9999))  # Implement a function to generate OTP
                    request.session['otp'] = otp  # Store the OTP in session for verification
                    res = [False,'']
                    
                    phone = None
                    if otp_type == 'mobile_phone':
                        phone = self.remove_special_characters(employee_id.mobile_phone)
                    if otp_type == 'work_phone':
                        phone = self.remove_special_characters(employee_id.mobile_phone)
                    
                    email = None
                    if otp_type == 'work_email':
                        email = employee_id.work_email
                        
                    if phone is not None and email is None:
                        res = self.send_sms(phone, otp)  # Implement a function to send OTP to the user
                        
                    
                    if phone is None and email is not None:
                        res = self.send_mail(email, otp)
                    if res[0]:
                        return { 'success': True, 'message': 'OTP sent successfully, please check your inbox!', 'otp':otp }
                    else:
                        return { 'success': res[0], 'message': res[1] }
                else:
                    return {'success': False, 'message': 'User employee doesn\'t mapped please contact Administrator!'}
            return {'success': False, 'message': 'Invalid credentials!'}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    @http.route('/api/auth/verify/otp', type='json', auth='public', methods=['POST'], csrf=False)
    def auth_verify_otp(self, email, password, otp, remember_me=False):
        try:
            user = request.env['res.users'].sudo().search([('login', '=', email)], limit=1)
            if user:
                uid = request.session.authenticate(request.session.db, email, password)
                if 'otp' in request.session and request.session['otp'] == otp and uid:
                    del request.session['otp']
                    user = request.env['res.users'].sudo().browse(uid)
                    response = {'success': True, 'message': 'OTP verified successfully', 'user_id': uid }
                    if remember_me:
                        user_agent = request.httprequest.headers.get('User-Agent', '')
                        response['auth_token'] = user.set_remember_me_token(self.get_req_user_agent(user_agent))
                    return response
                else:
                    return {'success': False, 'message': 'Invalid OTP'}
            else:
                return {'success': False, 'message': 'User not found'}
        except Exception as e:
            return {'success': False, 'message': str(e), "debug": e }
        
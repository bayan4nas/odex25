# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
import random
import string

class APIsConfiguration(models.Model):
    _name = 'login.api.config'
    _description = "Login Api Configuration"

    default = fields.Boolean(string="Is Default")
    name = fields.Char(string="App Name")
    url = fields.Char(string="Api Url")
    method = fields.Selection([("post", "POST"),("get", "GET")], default="post", string="Api Method")
    headers = fields.One2many('login.api.headers', 'api_config_id', 'Api Headers')
    body = fields.One2many('login.api.body', 'api_config_id', 'Api Body')
    
    mail_from = fields.Char(string="Mail From")
    mail_server = fields.Char(string="Mail Server")
    mail_port = fields.Char(string="Mail Port")
    mail_pwd = fields.Char(string="Mail Password")
    mail_subject_start_with = fields.Char(string="Mail Subject Start With")
    mail_otp_msg = fields.Char(string="Mail OTP Message")
    
    def get_config_with_replacements(self, base_url, mobile, otp):
        config = self.read()[0]
        replacements = { '{base_url}': base_url, '{mobile}': mobile, '{otp}': otp }

        def replace_placeholders(value):
            if isinstance(value, str):
                for placeholder, replacement in replacements.items():
                    value = value.replace(placeholder, replacement)
            return value

        for key in config:
            if isinstance(config[key], str):
                config[key] = replace_placeholders(config[key])

        # Process headers
        headers = {}
        for header in self.headers:
            value = replace_placeholders(header.value)
            headers[header.key] = value
        config['headers'] = headers

        # Process body
        body = {}
        for item in self.body:
            value = replace_placeholders(item.value)
            body[item.key] = value
        config['body'] = body
        
        return config
    
class ApiHeaders(models.Model):
    _name = 'login.api.headers'
    _description = "Api Headers"
    
    api_config_id = fields.Many2one('login.api.config', 'Setting')
    name = fields.Char(string="Name", default="/")
    key = fields.Char(string="Key")
    value = fields.Char(string="Value")

class ApiBody(models.Model):
    _name = 'login.api.body'
    _description = "Api Body"
    
    api_config_id = fields.Many2one('login.api.config', 'Setting')
    name = fields.Char(string="Name", default="/")
    key = fields.Char(string="Key")
    value = fields.Char(string="Value")


class TrustedDevices(models.Model):
    _name = 'trusted.devices.2fa'
    _description = "Trusted Devices"
    
    user_id = fields.Many2one('res.users', 'User')
    device = fields.Char(string="Device")
    user_agent = fields.Char(string="User Agent")
    token = fields.Char(string="Token")
    date = fields.Date(string='Date', default=fields.Date.today)

class ResUsers(models.Model):
    _inherit = 'res.users'

    truested_devices_ids = fields.One2many('trusted.devices.2fa', 'user_id', 'Trusted Devices')
    # remember_me_token = fields.Char(string="Remember Me Token", copy=False)
    ask_for_phone_otp = fields.Boolean(string="Allow Phone For 2FA", default=True)
    ask_for_email_otp = fields.Boolean(string="Allow Email For 2FA", default=True)
    employee_id = fields.Many2one('hr.employee', string='Related Employee', ondelete='restrict', auto_join=True, help='Employee-related data of the user')
    
    def generate_remember_me_token(self):
        """Generate a random and secure token for 'Remember Me' functionality."""
        token_length = 32
        token_characters = string.ascii_letters + string.digits
        return ''.join(random.choice(token_characters) for i in range(token_length))


    def set_remember_me_token(self, data):
        """Set a new 'Remember Me' token for the user."""
        # Check if there's already a trusted device with a token for the user
        token = self.generate_remember_me_token()
        # If no trusted device with a token exists, generate a new token and create a trusted device record
        self.env['trusted.devices.2fa'].create({
            'user_id': self.id,
            'device': data['name'],  # You can set the device to a default value or update it based on the actual device later
            'user_agent': data['user_agent'],
            'token': token,
        })
        return token
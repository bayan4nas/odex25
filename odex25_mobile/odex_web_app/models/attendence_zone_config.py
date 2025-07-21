# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import datetime


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'
    
    web_fcm_server_key = fields.Char(string='Server Key:', related="company_id.web_fcm_server_key", readonly=False)
    service_account = fields.Binary(string='Service Account:', related="company_id.service_account", readonly=False)
    web_sender_id = fields.Char(string='Sender ID:', related="company_id.web_sender_id", readonly=False)


class ResCompany(models.Model):
    _inherit = 'res.company'

    web_fcm_server_key = fields.Char(string='Server Key')
    service_account = fields.Binary(string='Service Account', attachment=True)
    web_sender_id = fields.Char(string='Sender ID')

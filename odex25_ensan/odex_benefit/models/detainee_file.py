# -*- coding: utf-8 -*-
import logging
from datetime import datetime, date
from dateutil.relativedelta import relativedelta as rd
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import qrcode
import base64
from io import BytesIO
import re



class DetaineeFile(models.Model):
    _name = 'detainee.file'
    _description = 'Detainee File'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="code", readonly=True, copy=False, default=lambda self: _('New'))
    beneficiary_category = fields.Selection([('gust', 'Gust'), ('released', 'Released')], string='Beneficiary Category')

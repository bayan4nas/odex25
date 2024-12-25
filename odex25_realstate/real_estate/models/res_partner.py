# -*- coding: utf-8 -*-
##############################################################################
#
#   Expert (LCT, Life Connection Technology)
#    Copyright (C) 2021-2022 LCT
#
##############################################################################

import base64
import re
from odoo import models, fields, api, exceptions, tools, _
from odoo.modules.module import get_module_resource

class ResPartner(models.Model):
    _inherit = 'res.partner'

    identification_type = fields.Selection([('id', 'National ID'),
                                            ('iqama', 'Iqama'),
                                            ('passport', 'Passport'),
                                            ('other', 'Other')], string='Identification Type')
    identification_number = fields.Char(string='Identification NUmber')
    identification_issue_date = fields.Date(string='Identification Issue Date')
    identification_expiry_date = fields.Date(string='Identification Expiry Date')
    issuer = fields.Char(string='Issuer')
    copy_no = fields.Integer(string='Copy No')

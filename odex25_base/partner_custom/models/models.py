import base64
import re
from odoo import models, fields, api, exceptions, tools, _
from datetime import datetime, date, timedelta
from odoo.exceptions import Warning

from odoo.modules.module import get_module_resource

class ResPartner(models.Model):
    _inherit = 'res.partner'

    identification_type = fields.Selection([('id', 'National ID'),
                                            ('iqama', 'Iqama'),
                                            ('passport', 'Passport'),
                                            ('other', 'Other')], default='id',string='Identification Type')
    identification_number = fields.Char(string='Identification NUmber')
    identification_issue_date = fields.Date(string='Identification Issue Date')
    identification_expiry_date = fields.Date(string='Identification Expiry Date')
    issuer = fields.Char(string='Issuer')
    copy_no = fields.Integer(string='Copy No')

    @api.constrains('identification_expiry_date', 'identification_type', 'identification_number', 'identification_issue_date')
    def check_expr_date(self):
        for each in self:
            if each.identification_expiry_date:
                exp_date = fields.Date.from_string(each.identification_expiry_date)
                if exp_date < date.today():
                    raise Warning(_('Your Document Is Expired.'))

            if each.identification_type == 'id':
                if each.identification_number and len(each.identification_number) != 10:
                    raise Warning(_('Saudi ID must be 10 digits'))
                if each.identification_number and each.identification_number[0] != '1':
                    raise Warning(_('The Saudi ID number should begin with 1'))

            if each.identification_type == 'iqama':
                if each.identification_number and len(each.identification_number) != 10:
                    raise Warning(_('Identity must be 10 digits'))
                if each.identification_number and each.identification_number[0] not in ['2', '3', '4']:
                    raise Warning(_('Identity must begin with 2 or 3 or 4'))

            if each.identification_expiry_date and each.identification_issue_date:
                if each.identification_expiry_date <= each.identification_issue_date:
                    raise Warning(_('Error, date of issue must be less than expiry date'))

                if date.today() >= each.identification_expiry_date:
                    raise Warning(_("Error, the expiry date must be greater than the date of the day"))

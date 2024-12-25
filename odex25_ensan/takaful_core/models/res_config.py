# Customize settings for Takaful configrations.

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from ast import literal_eval

class ResCompany(models.Model):
    _inherit = 'res.company'
    
    use_otp_login = fields.Boolean(string="Use Otp Login")
    otp_provider_token = fields.Char(string="OTP Provider Token")
    otp_sender_name = fields.Char(string="OTP Sender Name")

    use_sms_notification = fields.Boolean(string="Use SMS Notifications")
    sms_provider_token = fields.Char(string="SMS Provider Token")
    sms_sender_name = fields.Char(string="SMS Sender Name")

    # Moyaser
    moyaser_public_key = fields.Char(string='Moyaser Public Key')
    vat_default_percent=fields.Float(string='Vat Percent')

    bank_account_count = fields.Integer(compute='_compute_bank_count', string="Bank Accounts")
    company_name=fields.Char(string='Company Name',translate=True)

    # @api.multi
    def _compute_bank_count(self):
        bank_data = self.env['res.partner.bank'].read_group([('company_id', 'in', self.ids)], ['company_id'],
                                                            ['company_id'])
        mapped_data = dict([(bank['company_id'][0], bank['company_id_count']) for bank in bank_data])

        for company in self:
            company.bank_account_count = mapped_data.get(company.id, 0)
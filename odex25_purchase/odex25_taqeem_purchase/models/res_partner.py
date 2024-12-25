from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _


class ResPartner(models.Model):
    _inherit = 'res.partner'
    # purchase_request_id = fields.Many2one('purchase.request')

    @api.constrains('vat', 'company_type', 'commercial_register')
    def _check_unique_tax_id_commercial_register(self):
        for record in self:
            if record.vat:
                domain = [('vat', '=', record.vat), ('company_type', '=', 'company'), ]
                existing_records = self.env['res.partner'].search_count(domain)
                if existing_records > 1:
                    raise ValidationError("Tax ID must be unique per company")
            if record.commercial_register:
                domain = [('commercial_register', '=', record.commercial_register), ('company_type', '=', 'company'), ]
                existing_records = self.env['res.partner'].search_count(domain)
                if existing_records > 1:
                    raise ValidationError("Commercial Register must be unique per company")

    @api.constrains('id_number', 'company_type')
    def _check_unique_id_number(self):
        for record in self:
            if record.id_number:
                domain = [('id_number', '=', record.id_number), ('company_type', '=', 'person')]
                existing_records = self.env['res.partner'].search_count(domain)
                if existing_records > 1:
                    raise ValidationError("Identity Number must be unique")

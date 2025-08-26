from odoo import fields, models, api, _


class BenefitsPath(models.Model):
    _name = 'beneficiary.categories'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Beneficiary Categories'

    name = fields.Char(string='Name', required=False)
    code = fields.Char(string='Code')
    descriptions = fields.Char(string='Descriptions')
    service_title = fields.Many2one('benefits.service',string='Service Title')

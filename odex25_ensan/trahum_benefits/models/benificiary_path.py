from odoo import fields, models, api, _


class BenefitsPath(models.Model):
    _name = 'beneficiary.path'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Beneficiary Path'

    name = fields.Char(string='Name', required=False)
    code = fields.Char(string='Code')
    descriptions = fields.Char(string='Descriptions')
    category_types = fields.Many2one('benefits.service.classification', string='Category types')

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Path code must be unique!'),
    ]

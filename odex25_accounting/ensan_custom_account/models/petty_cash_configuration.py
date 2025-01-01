from odoo import fields, models, api


class PettyCashConfiguration(models.Model):
    _inherit = 'petty.cash.configuration'
    account_id = fields.Many2one(domain=[('type', '!=', 'view')])

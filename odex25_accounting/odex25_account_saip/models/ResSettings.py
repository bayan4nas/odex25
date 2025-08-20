from odoo import fields, models


class ResSetting(models.TransientModel):
    _inherit = 'res.config.settings'

    payment_approved = fields.Float(string='Payment Approve', related="company_id.payment_approved",readonly=False)
    
    
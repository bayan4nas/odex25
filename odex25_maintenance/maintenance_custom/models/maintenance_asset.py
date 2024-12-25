from odoo import api, fields, models

class MaintenanceAsset(models.Model):
    _inherit = 'maintenance.request'

    asset_id = fields.Many2one(string="Asset",
                               comodel_name='account.asset',
                               required=False)

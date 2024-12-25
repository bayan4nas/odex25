from odoo import models, fields

class ResCompany(models.Model):
    _inherit = 'res.company'

    # Modify the selection field to include the new font option
    font = fields.Selection(selection_add=[('DroidNaskh','DroidNaskh'),('DroidKufi', 'DroidKufi'),('Bukra','Bukra')])
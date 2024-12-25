from odoo import api, fields, models

class MaintenanceChecklist(models.Model):
    _inherit = 'maintenance.request'

    checklist_lines = fields.One2many(
        comodel_name='checklist.line',
        inverse_name='checklist_id',
        string='Checklist',
        required=False)


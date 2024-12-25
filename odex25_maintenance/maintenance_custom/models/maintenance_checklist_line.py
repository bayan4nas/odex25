from odoo import api, fields, models


class MaintenanceChecklistLines(models.Model):
    _name = 'checklist.line'
    _description = 'Inspection Checklist For Maintenance Lines'


    name = fields.Char(
        string='Name',
        required=True)
    description = fields.Char(
        string='Description',
        required=False)
    checklist_id = fields.Many2one(
        comodel_name='maintenance.request',
        string='',
        required=False)


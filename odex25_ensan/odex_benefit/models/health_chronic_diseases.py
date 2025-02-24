from odoo import fields, models,api


class HealthChronicDiseases(models.Model):
    _name = 'health.chronic.diseases'

    name = fields.Char(string='Name')
from odoo import fields, models,api


class HealthGeneticDiseases(models.Model):
    _name = 'health.genetic.diseases'

    name = fields.Char(string='Name')
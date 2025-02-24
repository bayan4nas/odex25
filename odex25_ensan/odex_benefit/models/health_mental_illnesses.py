from odoo import fields, models,api


class HealthMentalIllnesses(models.Model):
    _name = 'health.mental.illnesses'

    name = fields.Char(string='Name')
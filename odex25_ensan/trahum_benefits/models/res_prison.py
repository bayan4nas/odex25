from odoo import models, fields, api

class ResPrisonCountry(models.Model):
    _name = 'res.prison.country'
    _description = 'Prison Country'

    name = fields.Char(string='Country Name', required=True)
    prison_ids = fields.One2many('res.prison', 'country_id', string='Prisons')

class ResPrison(models.Model):
    _name = 'res.prison'
    _description = 'Prison'

    name = fields.Char(string='Prison Name', required=True)
    country_id = fields.Many2one('res.prison.country', string='Country', required=False)
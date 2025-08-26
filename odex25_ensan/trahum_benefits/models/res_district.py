



from odoo import models, fields, api, _

class ResDistrict(models.Model):
    _name = 'res.district'
    _description = 'District'

    name = fields.Char(string='District Name', required=True)
    city_id = fields.Many2one('res.country.city', string='City', required=True)


from odoo import fields, models

class MainService(models.Model):
    _name = 'main.service'

    name = fields.Char(string='Name')
    service_type = fields.Selection([
        ('service', 'Service'),
        ('exception', 'Exception'),
        ], string='Service Type')
    services = fields.Selection([
        ('experimental_services', 'Experimental Services'),
        ('exceptional_services', 'Exceptional Services'),
        ('emergency_services', 'Emergency Services'),
        ('seasonal_services', 'Seasonal Services'),
        ('permanent_services', 'Permanent Services'),
        ], string='Services')

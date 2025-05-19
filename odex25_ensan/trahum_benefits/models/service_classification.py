from odoo import models, fields

class ServiceClassification(models.Model):
    _name = 'benefits.service.classification'
    _description = 'Service Classification'
    _order = 'name asc'
    
    name = fields.Char(string='Name', required=True)
    code = fields.Char(string='Code', required=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
    
    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Classification code must be unique!'),
    ]
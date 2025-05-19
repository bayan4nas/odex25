from odoo import models, fields, api, _

class CaseTypes(models.Model):
    _name = 'cases.type'

    name = fields.Char('Name')

class CaseInformation(models.Model):
    _name = 'case.information'

    name = fields.Char('Name')
    type = fields.Many2one('cases.type', 'Case Type')



from odoo import fields, models, api


class BranchDetails(models.Model):
    _name = 'branch.details'

    name = fields.Char()
    code = fields.Char()

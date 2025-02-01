from odoo import fields, models, api


class IdentityProof(models.Model):
    _name = 'identity.proof'

    name = fields.Char()

class WorkType(models.Model):
    _name = 'work.type'

    name = fields.Char()

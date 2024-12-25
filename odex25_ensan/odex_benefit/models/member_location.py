from odoo import fields, models

class MemberLocation(models.Model):
    _name = 'member.location'

    name = fields.Char(string="Name")
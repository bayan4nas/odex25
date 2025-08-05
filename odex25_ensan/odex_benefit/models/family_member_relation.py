from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

class FamilyMemberRelation(models.Model):
    _name = 'family.member.relation'
    _description = 'Family Member Relation'

    name = fields.Char(string='Relation', required=True)
    gender = fields.Selection(selection=[('male', _('Male')), ('female', _('Female'))], string="Gender")


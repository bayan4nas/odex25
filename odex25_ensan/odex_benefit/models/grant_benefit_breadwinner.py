from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

class GrantBenefitBreadwinner(models.Model):
    _name = 'grant.benefit.breadwinner'
    _description = 'Grant Benefit Breadwinner'

    grant_benefit_ids = fields.Many2one('grant.benefit', string="Grant Benefit", ondelete="cascade")
    member_name = fields.Many2one('family.member', string="Member name", domain=[('state', '=', 'confirmed')])

    relation_id = fields.Many2one('family.member.relation', string='Relation with res')
    breadwinner = fields.Char(string='Breadwinner', default=lambda self: _('Breadwinner'))

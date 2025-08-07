from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT

class GrantBenefitMember(models.Model):
    _name = 'grant.benefit.member'
    _description = 'Grant Benefit Member'

    grant_benefit_id = fields.Many2one('grant.benefit', string="Grant Benefit", ondelete="cascade")
    member_id = fields.Many2one('family.member', string="Member")
    # relationship = fields.Many2one(related='member_id.relation_id', string="Relationship", readonly=True)
    is_breadwinner = fields.Boolean(string=" Is Breadwinner?")
    relation_id = fields.Many2one('family.member.relation', string='Relation with res')
    rel_with_resd = fields.Char(string='Relation', default=lambda self: _('Follower'))

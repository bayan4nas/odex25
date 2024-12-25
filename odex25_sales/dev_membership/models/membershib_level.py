from odoo import models,api, fields,_

class MembershipLevel(models.Model):
    _name = 'membership.level'
    _description = 'Membership Level'
    _order='sequence'

    name = fields.Char(string='Name', required=True)
    years = fields.Integer(string='NO Of Years Subscription.', required=True)
    min = fields.Integer(string='Minimum', required=True)
    max = fields.Integer(string='Maximum', required=True)
    color = fields.Char(string='Membership Card Color')
    level_no = fields.Char("Number", tracking=True,copy=False)
    sequence = fields.Integer(string="Sequence", help="Define the display order")
    company_id = fields.Many2one('res.company', string='Company', readonly=True,
        default=lambda self: self.env.company)
    active = fields.Boolean(default=True)

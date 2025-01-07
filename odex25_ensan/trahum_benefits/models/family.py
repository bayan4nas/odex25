# -*- coding: utf-8 -*-
from odoo import models, fields

class GrantBenefit(models.Model):
    _inherit = 'grant.benefit'

    inmate_member_id = fields.Many2one('family.member', string='Inmate', domain="[('benefit_type', '=', 'inmate')]")
    breadwinner_member_id = fields.Many2one('family.member', string='Breadwinner', domain="[('benefit_type', '=', 'breadwinner')]")
    
    

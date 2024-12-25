# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class BranchInherit(models.Model):
    _inherit = 'res.branch'

    district_id = fields.Many2one('res.districts', string="District")

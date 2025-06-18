# -*- coding: utf-8 -*-

from odoo import models, fields, api

class Users(models.Model):
    _inherit = 'res.users'

    sign_signature = fields.Binary(string="Digital Signature")

# class ResCompanyExt(models.Model):
#     _inherit = 'res.company'
#
#     salary_def_id = fields.Many2one('hr.employee', string='Salary Definition Signature')

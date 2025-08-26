# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    idle_time = fields.Integer(string="Inactive Session Time Out Delay")


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    idle_time = fields.Integer(related='company_id.idle_time', readonly=False)






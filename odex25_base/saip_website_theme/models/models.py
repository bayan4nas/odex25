# -*- coding: utf-8 -*-
from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    jobs_per_page = fields.Integer(
        string="Jobs Per Page",
        default=5,
        config_parameter='saip_website_theme.jobs_per_page'
    )
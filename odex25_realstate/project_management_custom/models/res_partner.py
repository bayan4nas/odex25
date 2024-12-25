# -*- coding: utf-8 -*-
##############################################################################
#
#   Expert (LCT, Life Connection Technology)
#    Copyright (C) 2021-2022 LCT
#
##############################################################################

from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_engineering_office = fields.Boolean(string='Engineering Office')
    is_subcontractor = fields.Boolean(string='Subcontractor')
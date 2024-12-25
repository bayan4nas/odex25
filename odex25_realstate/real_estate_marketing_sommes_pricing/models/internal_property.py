# -*- coding: utf-8 -*-
##############################################################################
#
#   Expert (LCT, Life Connection Technology)
#    Copyright (C) 2021-2022 LCT
#
##############################################################################

from odoo import models, fields, api, _

class InternalProperty(models.Model):
    _inherit = 'internal.property'

    somme_ids = fields.One2many('re.sommes', 'property_id', string="Somme")
    pricing_ids = fields.One2many('re.pricing', 'property_id', 'Pricing')

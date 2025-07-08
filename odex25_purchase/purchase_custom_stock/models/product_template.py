#-*- coding: utf-8 -*-
from odoo import models, fields , api, _
from datetime import datetime
from datetime import timedelta

class ProductTempInherit(models.Model):
    _inherit = 'product.template'

    asset_ok = fields.Boolean(string="Asset Expensed")
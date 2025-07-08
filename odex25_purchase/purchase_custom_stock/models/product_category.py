#-*- coding: utf-8 -*-
from odoo import models, fields , api, _
from datetime import datetime
from datetime import timedelta

class Category(models.Model):
    _inherit = 'product.category'

    active = fields.Boolean("Active",default=True)
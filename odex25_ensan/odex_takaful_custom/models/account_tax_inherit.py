# -*- coding: utf-8 -*-
from odoo import models, fields, api, _



class AccountTaxInherit(models.Model):
    _inherit = "account.tax"

    projects_percentage = fields.Boolean(string='Projects Percentage')






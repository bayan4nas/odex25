from odoo import models, fields, api
from datetime import timedelta

class BenefitsService(models.Model):
    _inherit = 'benefits.service'

    sla_duration = fields.Integer("SLA Duration")
    sla_unit = fields.Selection([('hours', 'Hours'), ('days', 'Days')], default='days')
    auto_cancelled = fields.Boolean("Auto Cancel on SLA Expiry")

# -*- coding: utf-8 -*-

from odoo import fields, models


class ResourceCalendar(models.Model):
    _inherit = 'resource.calendar'

    grace_hour_before_work = fields.Float(string="Grace Hours Before Work")
    grace_hour_after_work = fields.Float(string="Grace Hours After Work")

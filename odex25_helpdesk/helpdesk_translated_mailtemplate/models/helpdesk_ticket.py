# -*- coding: utf-8 -*-
from odoo import api, fields, models, tools, _


class HelpdeskTicket(models.Model):
    _inherit = 'odex25_helpdesk.ticket'

    rated = fields.Boolean(default=False)
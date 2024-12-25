# -*- coding: utf-8 -*-

from odoo import models, api, fields, tools



class File(models.Model):
    _inherit = 'dms.file'

    event_id = fields.Many2one('event.event', 'Event')
# -*- coding: utf-8 -*-
from odoo import models, fields, api,_

class Fleet(models.Model):
    _inherit = 'fleet.vehicle'
    employee_maintenance_id = fields.Many2one(comodel_name='hr.employee',string=_('Employee'))

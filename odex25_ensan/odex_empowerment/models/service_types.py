# -*- coding: utf-8 -*-

from odoo import models, fields

class EmpServices(models.Model):
    _name = 'emp.service.types'

    name = fields.Char(string='Service Name')
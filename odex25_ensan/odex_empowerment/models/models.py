# -*- coding: utf-8 -*-

from odoo import models, fields

class empowerment(models.Model):
    _name = 'empowerment.requests'

    name = fields.Char(string='Request Number')
    branch_custom_id = fields.Many2one('hr.department', string='Branch')
    employee_id = fields.Many2one('hr.employee', string='Employee Name')
    benefit_id = fields.Many2one('grant.benefit', string='Benefit Name')
    request_date = fields.Datetime('Request Date')
    service_type = fields.Many2one('emp.service.types', string='Service Types')
from odoo import models, fields, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    plan_by = fields.Selection([('man_hours', 'Man hours'), ('man_days', 'Man Days'), ], string='Plan By')
    detailed_plan_unit = fields.Selection([('week', 'Weeks'), ('month', 'Months'), ], default='week',
                                          string='Detailed Plan Unit')
    plan_by_departments = fields.Boolean(string="Plan By Departments")


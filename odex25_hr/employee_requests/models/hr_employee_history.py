from odoo import models, fields


class EmployeeHistory(models.Model):
    _inherit = 'hr.employee.history'

    job_domain_id = fields.Many2one('employee.job.domain', string="Job Domain")
    salary = fields.Float(string="Salary", required=False)
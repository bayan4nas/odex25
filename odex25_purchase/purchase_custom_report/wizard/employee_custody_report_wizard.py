from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from collections import defaultdict


class EmployeeCustodyReport(models.TransientModel):
    _name = 'employee.custody.report'
    _description = 'Employee Custody Report'

    date_from = fields.Date(string='Start Date', required=True)
    date_to = fields.Date(string='End Date', required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee')
    department_id = fields.Many2one('hr.department', string='Department')

    def action_print(self):
        data = {
            'date_from': self.date_from,
            'date_to': self.date_to,
            'employee_id': self.employee_id.id if self.employee_id else False,
            'department_id': self.department_id.id if self.department_id else False,
        }
        return self.env.ref('purchase_custom_report.action_report_employee_custody').report_action(
            [],
            data=data,
        )


class ReportEmployeeCustody(models.AbstractModel):
    _name = 'report.purchase_custom_report.employee_custody_report_details'

    @api.model
    def _get_report_values(self, docids, data=None):
        domain = [('date', '>=', data['date_from']), ('date', '<=', data['date_to']),
                  ('state', 'not in', ['cancel', 'refuse'])]

        employee_obj = self.env['hr.employee']
        department_obj = self.env['hr.department']

        if data.get('employee_id'):
            domain.append(('employee_id', '=', data['employee_id']))
        if data.get('department_id'):
            domain.append(('department_id', '=', data['department_id']))

        requests = self.env['purchase.request'].search(domain)

        grouped_data = defaultdict(lambda: {'requests': [], 'operations': []})

        for request in requests:
            operations = self.env['account.asset.operation'].search([
                ('purchase_request_id', '=', request.id),
                ('type', '=', 'assignment'), ('state', '!=', 'cancel')
            ])

            if operations:
                key = (request.employee_id.id, request.department_id.id)
                grouped_data[key]['requests'].append(request)
                grouped_data[key]['operations'].extend(operations)
        result_data = []
        for (employee_id, department_id), records in grouped_data.items():
            result_data.append({
                'employee': employee_obj.browse(employee_id),
                'department': department_obj.browse(department_id),
                'requests': records['requests'],
                'operations': records['operations'],
            })

        return {
            'result_data': result_data,
            'date_from': data['date_from'],
            'date_to': data['date_to'],
            'employee': employee_obj.browse(data['employee_id']) if data.get('employee_id') else None,
            'department': department_obj.browse(data['department_id']) if data.get('department_id') else None,
            'show_department_column': not data.get('department_id'),
            'show_employee_column': not data.get('employee_id'),
        }

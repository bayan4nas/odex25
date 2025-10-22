from odoo import api, fields, models



class EmployeeOtherRequestExt(models.Model):
    _inherit = 'employee.other.request'

    def submit(self):
        super(EmployeeOtherRequestExt, self).submit()
        for i in self:
            if i.request_type == 'salary_define':
                i.write({'state': 'approved'})

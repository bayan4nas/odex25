from odoo import models, fields

class HrDepartment(models.Model):
    _inherit = 'hr.department'

    operation_manager_id = fields.Many2one('hr.employee', string='Operation Manager')
    # def name_get(self):
    #     result = []
    #     for department in self:
    #         name = department.name
    #         result.append((department.id, name))
    #     return result

    # def name_get(self):
    #     result = []
    #     print(self.env.context)  # Log the context for debugging
    #     if self.env.context.get('special_display_name', True):
    #         for department in self:
    #             name = department.name
    #             result.append((department.id, name))
    #             return result
    #     return super(HrDepartment, self).name_get()
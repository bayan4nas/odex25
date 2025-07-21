from odoo import models, fields, api
from odoo.tools.misc import clean_context


class ResUsers(models.Model):
    _inherit = 'res.users'

    create_employee = fields.Boolean(store=False, default=True, copy=False, string="Technical field, whether to create an employee")
    create_employee_id = fields.Many2one('hr.employee', store=False, copy=False, string="Technical field, bind user to this employee on create")


    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        employee_create_vals = []
        for user, vals in zip(res, vals_list):
            if not vals.get('create_employee') and not vals.get('create_employee_id'):
                continue
            if vals.get('create_employee_id'):
                self.env['hr.employee'].browse(vals.get('create_employee_id')).user_id = user
            else:
                employee_create_vals.append(dict(
                    name=user.name,
                    company_id=user.env.company.id,
                    **self.env['hr.employee']._sync_user(user)
                ))
        if employee_create_vals:
            self.env['hr.employee'].with_context(clean_context(self.env.context)).create(employee_create_vals)
        return res
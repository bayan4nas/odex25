from odoo import models, fields, api, _, exceptions
from odoo import SUPERUSER_ID
from odoo.exceptions import ValidationError
# from datetime import datetime , date


class EmployeeCustody(models.Model):
    _name = 'custom.employee.custody'
    _rec_name = 'employee_id'
    _description = 'Employee custody'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    current_date = fields.Date(default=lambda self: fields.Date.today())
    from_hr_department = fields.Boolean()
    employee_no = fields.Char(related="employee_id.emp_no", readonly=True)
    note = fields.Text()
    state = fields.Selection(selection=[
        ("draft", _("Send")),
        ("submit", _("send")),
        ("direct", _("Direct Manager")),
        ("admin", _("Human Resources Manager")),
        ("approve", _("Warehouse Keeper")),
        ("wait_release", _("Wait Release")),
        ("assign", _("Assignment")),
        ("wait", _("Wait Assignment")),
        ("done", _("Return Done")),
        ("refuse", _("Refuse"))
    ], default='draft',tracking=True)

    # Relational fields
    receiving_custody = fields.Many2one('hr.custody.receiving')
    custody_line_ids = fields.One2many('employee.custody.line', 'employee_custody_line')
    employee_id = fields.Many2one('hr.employee', 'Employee', default=lambda item: item.get_user_id(),
                                  domain=[('state', '=', 'open')])
    department_id = fields.Many2one(related="employee_id.department_id", readonly=True)
    job_id = fields.Many2one(related="employee_id.job_id", readonly=True)
    country_id = fields.Many2one(related="employee_id.country_id", readonly=True)

    def draft(self):
        self.state = "draft"

    def submit(self):
        self.state = "submit"

    def direct(self):
        self.state = "direct"

    def admin(self):
        if self.employee_id.parent_id.user_id.id != self.env.user.id:
            raise ValidationError(_("Only the employee's direct manager can approve at this stage."))
        self.state = "admin"

    def approve(self):
        self.state = "approve"

    def finish(self):
        self.asset_custody_release()
        self.state = "wait"
    def done(self):
        if not self.asset_line_ids:
            raise exceptions.Warning(_('Please Select an asset'))
        self.create_asset_custody()
        self.write({'state': "wait_release"})





    def refuse(self):
        self.state = "refuse"

    def get_user_id(self):
        employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        if employee_id:
            return employee_id.id
        else:
            return False

    def unlink(self):
        for i in self:
            if i.state != 'draft':
                raise exceptions.Warning(_('You can not delete record in state not in draft'))
        return super(EmployeeCustody, self).unlink()




class EmployeeCustodyLine(models.Model):
    _name = 'employee.custody.line'

    name = fields.Char()
    serial = fields.Char()
    quantity = fields.Float()
    receiving_quantity = fields.Float()
    note = fields.Char()
    receiving_date = fields.Date()
    amount = fields.Float()

    # Relational fields
    employee_custody_line = fields.Many2one(comodel_name='custom.employee.custody')  # Inverse field



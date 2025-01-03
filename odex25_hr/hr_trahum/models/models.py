# -*- coding: utf-8 -*-


from odoo import models, fields, api, _, exceptions
import logging
from odoo.exceptions import ValidationError
_logger = logging.getLogger(__name__)



class HrContractTrahum(models.Model):
    _inherit = 'hr.contract'

    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('employeed_aproval', 'Employeed Approval'),
        ('hr_head_approval', 'HR Head Approval'),
        ('sector_head_approval', 'Sector Head Approval'),
        ('program_directory', 'Executive Approval'),
        ('end_contract', 'End Contract')
    ], default='draft', tracking=True)

    # def action_sector_head_approval(self):
    #     """Approve contract by Sector Head"""
    #     if self.state != 'hr_head_approval':
    #         raise exceptions.UserError("Only HR Head approved contracts can proceed to Sector Head Approval.")
    #     self.state = 'sector_head_approval'

    def action_sector_head_approval(self):
        self.state = "sector_head_approval"



class HrOfficialMissionTrahum(models.Model):
    _inherit = 'hr.official.mission'
#

    state = fields.Selection([('draft', _('Draft')),
                              ('send', _('Waiting Direct Manager')),
                              ('direct_manager', _('Waiting Department Manager')),
                              ('depart_manager', _('Wait HR Department')),
                              ('sector_head_approval', _('Sector Head Approval')),
                              ('hr_aaproval', _('Wait Approval')),
                              ('approve', _('Approved')),
                              ('refused', _('Refused'))], default="draft", tracking=True)

    def action_sector_head_approval(self):
        self.state = "sector_head_approval"

    # def action_secretary_general(self):
    #     self.state = "secretary_general"


# class EmployeeOvertimeRequestTrahum(models.Model):
#     _inherit = 'employee.overtime.request'
#
#
#     state = fields.Selection(
#         [('draft', _('Draft')),
#          ('submit', _('Waiting Direct Manager')),
#          ('direct_manager', _('Waiting Department Manager')),
#          ('financial_manager', _('Wait HR Department')),
#          ('sector_head_approval', _('Sector Head Approval')),
#          ('hr_aaproval', _('Wait Approval')),
#          ('executive_office', _('Wait Transfer')),
#          ('validated', _('Transferred')),
#          ('refused', _('Refused'))], default="draft", tracking=True)

    # def action_sector_head_approval(self):
    #     self.state = "sector_head_approval"


    def action_secretary_general(self):
        self.state = "secretary_general"



class HrLoanSalaryAdvanceInherit(models.Model):
    _inherit = 'hr.loan.salary.advance'

    state = fields.Selection(
                [('draft', _('Draft')),
                 ('submit', _('Waiting Payroll Officer')),
                 ('direct_manager', _('Wait HR Department')),
                 ('sector_head_approval', _('Sector Head Approval')),
                 ('hr_manager', _('Wait GM Approval')),
                 ('executive_manager', _('Wait Transfer')),
                 ('pay', _('Transferred')), ('refused', _('Refused')),
                 ('closed', _('Loan Suspended'))],
            default="draft", tracking=True)

    def action_sector_head_approval(self):
        self.state = "sector_head_approval"



class HrSalaryAdvanceInherit(models.Model):
    _inherit = 'hr.payroll.raise'

    state = fields.Selection([('draft', 'Draft'),
                              ('hr_officer', 'HR Officer'),
                              ('confirm', 'HR Manager'),
                              ('sector_head_approval', _('Sector Head Approval')),
                              ('secretary_general', _('Secretary General')),
                              ('approve', 'Approved'),
                              ('refuse', 'Refused')], 'State', default='draft')
    def action_sector_head_approval(self):
        self.state = "sector_head_approval"


    def action_secretary_general(self):
        self.state = "secretary_general"


class TerminationpPatchinherit(models.Model):
    _inherit = "hr.termination"

    state = fields.Selection(selection=[
        ("draft", "Draft"),
        ("submit", "Waiting Direct Manager"),
        ("direct_manager", "Waiting Department Manager"),
        ("hr_manager", "Wait HR Officer"),
        ("finance_manager", "Wait HR Manager"),
        ('sector_head_approval', _('Sector Head Approval')),
        ('secretary_general', _('Secretary General')),
        ("gm_manager", "Wait CEO Manager"),
        ("done", "Wait Transfer"),
        ("pay", "Transferred"),
        ("refused", "Refused")], default='draft', tracking=True)

    def action_sector_head_approval(self):
        self.state = "sector_head_approval"


    def action_secretary_general(self):
        self.state = "secretary_general"


class EmployeeHrhierarchy(models.Model):
    _inherit = "hr.employee"

    # @api.model
    # def create(self, vals):
    #     employee = super(EmployeeHrhierarchy, self).create(vals)
    #     employee.update_all_managers()
    #     return employee
    #
    # def write(self, vals):
    #     result = super(EmployeeHrhierarchy, self).write(vals)
    #     for employee in self:
    #         employee.update_all_managers()
    #     return result
    def action_update_hierarchy(self):
        """
        زر لتحديث الحقول parent_id و coach_id.
        """
        self.update_hierarchy()

    def update_hierarchy(self):
        for employee in self:
            # Step 1: تحديد `parent_id`
            if employee.department_id and employee.department_id.manager_id:
                # إذا كان الموظف هو مدير القسم، نبحث عن المدير الأعلى
                if employee == employee.department_id.manager_id:
                    higher_manager = employee.department_id.parent_id.manager_id
                    if higher_manager:
                        employee.parent_id = higher_manager
                        print(f"Updated parent_id for {employee.name}: {higher_manager.name}")
                    else:
                        employee.parent_id = False
                        print(f"No higher manager found for {employee.name}. parent_id set to False.")
                else:
                    # الموظف ليس مدير القسم
                    employee.parent_id = employee.department_id.manager_id
                    print(f"Updated parent_id for {employee.name}: {employee.parent_id.name}")
            else:
                employee.parent_id = False
                print(f"No manager found for {employee.name}. parent_id set to False.")

            # Step 2: تحديد `coach_id`
            current_manager = employee.parent_id
            while current_manager and current_manager.parent_id:
                current_manager = current_manager.parent_id

            if current_manager:
                employee.coach_id = current_manager
                print(f"Updated coach_id for {employee.name}: {current_manager.name}")
            else:
                # إذا لم يتم العثور على مدير أعلى في التسلسل الإداري
                employee.coach_id = employee.parent_id
                print(f"No higher coach found for {employee.name}. coach_id set to {employee.parent_id.name if employee.parent_id else 'False'}.")

            # Step 3: التأكد من أن `coach_id` و `parent_id` متطابقان إذا كانا في نهاية التسلسل الإداري
            if employee.coach_id == employee.parent_id:
                print(f"coach_id and parent_id are the same for {employee.name}: {employee.coach_id.name}")
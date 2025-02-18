# -*- coding: utf-8 -*-


from odoo import models, fields, api, _, exceptions
import logging
from odoo.exceptions import ValidationError
from datetime import date
_logger = logging.getLogger(__name__)



class HrContractTrahum(models.Model):
    _inherit = 'hr.contract'

    state = fields.Selection(selection=[
        ('draft', _('Draft')),
        ('employeed_aproval', _('Employeed Approval')),
        ('hr_head_approval', _('HR Head Approval')),
        ('sector_head_approval', _('Sector Head Approval')),
        ('program_directory', _('Executive Approval')),
        ('end_contract', _('End Contract'))
    ], default='draft', tracking=True)

    delgiation_status_type = fields.Selection(selection=[
        ('employee','Employee'),
        ('manager', 'Manager'),
        ('gm', 'General Manager'),])

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

#     def action_sector_head_approval(self):
#         self.state = "sector_head_approval"


    # def action_secretary_general(self):
    #     self.state = "secretary_general"



class HrLoanSalaryAdvanceInherit(models.Model):
    _inherit = 'hr.loan.salary.advance'

    state = fields.Selection(
                [('draft', _('Draft')),
                 ('submit', _('Waiting Payroll Officer')),
                 ('direct_manager', _('Wait HR Department')),
                 ('director_financial_management', _('Director Financial Management')),
                 ('sector_head_approval', _('Wait Sector Head Approval')),
                 ('hr_manager', _('Wait HR')),
                 ('executive_manager', _('Wait GM Approval')),
                 ('pay', _('Transferred')), ('refused', _('Refused')),
                 ('closed', _('Loan Suspended'))],
            default="draft", tracking=True)

    # def action_director_financial_management(self):
    #     self.state = "director_financial_management"

    def action_sector_head_approval(self):
        self.state = "executive_office" 

    def hr_aaproval(self):
        self.state = "sector_head_approval"


class HrSalaryAdvanceInherit(models.Model):
    _inherit = 'hr.payroll.raise'

    state = fields.Selection([('draft', 'Draft'),
                              ('hr_officer', 'HR Officer'),
                              ('confirm', 'HR Manager'),
                              ('sector_head_approval', 'Sector Head Approval'),
                              ('secretary_general', 'Secretary General'),
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
        ('sector_head_approval',"Sector Head Approval"),
        ("gm_manager", "Wait CEO Manager"),
        ("done", "Wait Transfer"),
        ("pay", "Transferred"),
        ("refused", "Refused")], default='draft', tracking=True)

    def action_sector_head_approval(self):
        self.state = "sector_head_approval"




class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    state = fields.Selection(selection_add=[('accounting_head_approval', _('Accounting Head Approval')),
                                            ('sector_head_approval', _('Sector Head Approval')),
                                            ('secretary_general', _('Secretary General')),
                                            ('transfered', 'Transfer')
                                            ], tracking=True)


    def action_accounting_head_approval(self):
        self.state = "accounting_head_approval"

    def action_sector_head_approval(self):
        self.state = "sector_head_approval"

    def action_secretary_general(self):
        self.state = "secretary_general"

class HrPayslipRuninhirt(models.Model):
    _inherit = 'hr.payslip.run'

    state = fields.Selection(selection_add=[('computed', 'Computed'),
                                            ('confirmed', 'Confirmed'),
                                            ('accounting_head_approval', _('Accounting Head Approval')),
                                            ('sector_head_approval', _('Sector Head Approval')),
                                            ('secretary_general', _('Secretary General')),
                                            ('transfered', 'Transfer'), ('close', 'Close')], tracking=True)


    def action_accounting_head_approval(self):
        self.state = "accounting_head_approval"

    def action_sector_head_approval(self):
        self.state = "sector_head_approval"

    def action_secretary_general(self):
        self.state = "secretary_general"

class HrEmployeePromotions(models.Model):
    _inherit = 'employee.promotions'


    state = fields.Selection(selection=[('draft', _('Draft')),
                                        ('confirm', _('HR Officer')),
                                        ('hr_manager', _('HR Manager')),
                                        ('sector_head_approval', _('Sector Head Approval')),
                                        ('secretary_general', _('Secretary General')),
                                        ('approved', _('Approved')), ('refuse', 'Refused')],
                             default='draft', tracking=True)

    def action_sector_head_approval(self):
        self.state = "sector_head_approval"

    def action_secretary_general(self):
        self.state = "secretary_general"


class DepartmentHrhierarchy(models.Model):
    _inherit = "hr.department"

    employee_type_id = fields.Many2one('hr.contract.type', string="Employee Type")

class Employee(models.Model):
    _inherit = "hr.employee"



    parent_id = fields.Many2one('hr.employee', string="Manager")
    coach_id = fields.Many2one('hr.employee', string="Coach")
    emp_no = fields.Char(string="Employee Number", default="new", tracking=True)

    def get_emp_type_id(self):
        return self.department_id.employee_type_id
    
    @api.model
    def _generate_emp_no(self):
        seq = self.env['ir.sequence'].next_by_code('hr.employee.emp_no.sequence')
        return seq

    def complete_state(self):
        for employee in self:
            if employee.emp_no == "new":
                employee.emp_no = self._generate_emp_no()
            employee.state = "complete"

    @api.constrains("emp_no", "birthday", 'attachment_ids')
    def e_unique_field_name_constrains(self):
        for item in self:
            if item.emp_no != 'new':
                items = self.search([("emp_no", "=", item.emp_no)])
                if len(items) > 1:
                    raise ValidationError(
                        _("You cannot create Employee with the same employee number")
                    )

            if item.birthday >= date.today():
                raise Warning(_("Sorry, The Birthday Must Be Less than Date Today"))

            if item.attachment_ids:
                for rec in item.attachment_ids:
                    if not rec.doc_name:
                        raise exceptions.Warning(_('Attach the attachment to the Document %s') % (rec.name))



    # def _assign_manager_and_coach(self, department):
    #     """
    #     Helper function to traverse department hierarchy and assign manager and coach.
    #     """
    #     assigned_manager = None
    #     assigned_coach = None
    
    #     visited_departments = set()
    #     while department:
    #         if department.id in visited_departments:
    #             raise exceptions.ValidationError("Cyclic department hierarchy detected.")
    #         visited_departments.add(department.id)
    
    #         manager = department.manager_id
    #         if manager:
    #             if not assigned_manager and manager.id != self.id:
    #                 assigned_manager = manager
    #             elif not assigned_coach and manager.id != self.id and manager.id != (
    #             assigned_manager.id if assigned_manager else None):
    #                 assigned_coach = manager
    
    #         if assigned_manager and assigned_coach:
    #             break
    
    #         department = department.parent_id
    
    #     # If no separate coach is found, assign coach as the manager
    #     if not assigned_coach:
    #         assigned_coach = assigned_manager
    
    #     return assigned_manager, assigned_coach

    def _assign_manager(self, department):
        manager_id = False
        current_department = department
        while current_department.parent_id :
            if current_department.manager_id.id != self.id : break
            current_department = current_department.parent_id
        manager_id = current_department.manager_id
        return manager_id 

    
    def _assign_top_manager(self, department, direct_manager):
        manager_id = False
        current_department = department.parent_id and department.parent_id or department
        while current_department.parent_id :
            if current_department.manager_id.id != self.id and direct_manager.id != current_department.manager_id.id: break
            current_department = current_department.parent_id
        manager_id = current_department.manager_id
        return manager_id

    
    @api.model
    def create(self, vals):
        if 'department_id' in vals:
            department = self.env['hr.department'].browse(vals['department_id'])
            manager = self._assign_manager(department)
            coach = self._assign_top_manager(department, manager)
            if manager:
                vals['parent_id'] = manager.id
            if coach:
                vals['coach_id'] = coach.id
        return super(Employee, self).create(vals)
    
    def write(self, vals):
        if 'department_id' in vals:
            department = self.env['hr.department'].browse(vals['department_id'])
            manager = self._assign_manager(department)
            coach = self._assign_top_manager(department, manager)
            if manager:
                vals['parent_id'] = manager.id
            if coach:
                vals['coach_id'] = coach.id
        return super(Employee, self).write(vals)




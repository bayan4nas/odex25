# -*- coding: utf-8 -*-


from odoo import models, fields, api, _, exceptions
import logging
from odoo.exceptions import ValidationError
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


class EmployeeOvertimeRequestTrahum(models.Model):
    _inherit = 'employee.overtime.request'


    state = fields.Selection(
        [('draft', _('Draft')),
         ('submit', _('Waiting Direct Manager')),
         ('direct_manager', _('Waiting Department Manager')),
         ('financial_manager', _('Wait HR Department')),
         ('sector_head_approval', _('Sector Head Approval')),
         ('hr_aaproval', _('Wait Approval')),
         ('executive_office', _('Wait Transfer')),
         ('validated', _('Transferred')),
         ('refused', _('Refused'))], default="draft", tracking=True)

    def action_sector_head_approval(self):
        self.state = "sector_head_approval"


    # def action_secretary_general(self):
    #     self.state = "secretary_general"



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
        ("gm_manager", "Wait CEO Manager"),
        ("done", "Wait Transfer"),
        ("pay", "Transferred"),
        ("refused", "Refused")], default='draft', tracking=True)

    def action_sector_head_approval(self):
        self.state = "sector_head_approval"




class HrPayslipRuninhirt(models.Model):
    _inherit = 'hr.payslip.run'

    state = fields.Selection(selection_add=[('computed', 'Computed'),
                                            ('confirmed', 'Confirmed'),
                                            ('sector_head_approval', _('Sector Head Approval')),
                                            ('secretary_general', _('Secretary General')),
                                            ('transfered', 'Transfer'), ('close', 'Close')], tracking=True)
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


class EmployeeHrhierarchy(models.Model):
    _inherit = "hr.employee"



    parent_id = fields.Many2one('hr.employee', string="Manager")
    coach_id = fields.Many2one('hr.employee', string="Coach")

    def _assign_manager_and_coach(self, department):
        """
        Helper function to traverse department hierarchy and assign manager and coach.
        """
        assigned_manager = None
        assigned_coach = None

        visited_departments = set()
        while department:
            if department.id in visited_departments:
                raise exceptions.ValidationError("Cyclic department hierarchy detected.")
            visited_departments.add(department.id)

            manager = department.manager_id
            if manager:
                if not assigned_manager and manager.id != self.id:
                    assigned_manager = manager
                elif not assigned_coach and manager.id != self.id and manager.id != (
                assigned_manager.id if assigned_manager else None):
                    assigned_coach = manager

            if assigned_manager and assigned_coach:
                break

            department = department.parent_id

        # If no separate coach is found, assign coach as the manager
        if not assigned_coach:
            assigned_coach = assigned_manager

        return assigned_manager, assigned_coach

    @api.model
    def create(self, vals):
        if 'department_id' in vals:
            department = self.env['hr.department'].browse(vals['department_id'])
            manager, coach = self._assign_manager_and_coach(department)
            if manager:
                vals['parent_id'] = manager.id
            if coach:
                vals['coach_id'] = coach.id
        return super(EmployeeHrhierarchy, self).create(vals)

    def write(self, vals):
        if 'department_id' in vals:
            department = self.env['hr.department'].browse(vals['department_id'])
            manager, coach = self._assign_manager_and_coach(department)
            print(department,"department",coach,manager)
            # print(department,"department")
            if manager:
                vals['parent_id'] = manager.id
            if coach:
                vals['coach_id'] = coach.id
        return super(EmployeeHrhierarchy, self).write(vals)




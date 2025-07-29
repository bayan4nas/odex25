# -*- coding: utf-8 -*-


from odoo import models, fields, api, _, exceptions
import logging
from odoo.exceptions import ValidationError
from datetime import date
from datetime import datetime

_logger = logging.getLogger(__name__)


class HrPayrollStructureType(models.Model):
    _inherit = 'hr.payroll.structure.type'

class EmployeeOvertimeRequestTrahum(models.Model):
    _inherit = 'employee.overtime.request'

    state = fields.Selection(
        [('draft', _('Draft')),
         ('submit', _('Waiting Direct Manager')),
         ('direct_manager', _('Waiting Department Manager')),
         ('financial_manager', _('Wait HR Department')),
         ('hr_aaproval', _('Wait Approval')),
         ('hr_aaproval2', _('Wait Shared Service')),
         ('executive_office', _('Wait Transfer')),
         ('executive_office2', _('Wait Executive Manager Approval')),
         ('secret_general', _('Secret General')),
         ('validated', _('Transferred')),
         ('refused', _('Refused'))], default="draft", tracking=True)

    def financial_manager(self):
        if not self.is_branch:
            self.state = "financial_manager"
        else:
            self.state='hr_aaproval'


    def hr_aaproval(self):
        super(EmployeeOvertimeRequestTrahum, self).hr_aaproval()
        if self.is_branch:
            self.state = "hr_aaproval2"
        else:
            self.state = "hr_aaproval"

    def executive_office2(self):
        self.chick_not_mission()
        self.state = "executive_office2"

    def secret_general_approval(self):
        self.state = "validated"

class HrReContract(models.Model):
    _inherit = 'hr.re.contract'

    state = fields.Selection(string='State', selection=[
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('direct_manager', 'Direct Manager'),
        ('hr_manager', 'HR Manager'),
        ('secretary_general', 'Secretary General'),
        ('shared_service_approval', 'Shared Service Approval'),
        ('executive_manager', 'Executive Manager'),
        ('done', 'Re-Contract'),
        ('refuse', 'Refuse'),
    ], default='submitted', tracking=True)

    is_branch = fields.Many2one(related='department_id.branch_name', store=True, readonly=True)

    def action_direct_manager(self):
        # if self.employee_id.parent_id and self._uid != self.employee_id.parent_id.user_id.id:
        #    raise exceptions.Warning(_('This is Not Your Role beacuse Your Direct Manager'))

        self._get_employee_data()
        self._check_contract()
        employee = self.sudo().employee_id
        parent = employee.parent_id
        hr_manager = self.sudo().employee_id.company_id.hr_manager_id

        if parent:
            user_id = self.env.uid
            if parent.user_id.id == user_id or hr_manager.user_id.id == user_id:
                self.state = "hr_manager" if not self.is_branch else "shared_service_approval"
            else:
                raise exceptions.Warning(_(
                    'Sorry, The Approval For The Direct Manager %s Only OR HR Manager!'
                ) % parent.name)
        else:
            self.state = "hr_manager" if not self.is_branch else "shared_service_approval"


    def action_hr_manager(self):
        self._get_employee_data()
        if self.is_branch:
            self.state='executive_manager'
        else:
            self.state = "secretary_general"

    def action_done(self):
        self._check_contract()
        today = datetime.now().date()
        str_today = today.strftime('%Y-%m-%d')
        # if str_today != self.effective_date:
        # raise exceptions.Warning(_('You can not re-contract employee because effective date is not today'))
        last_record = self.env['hr.re.contract'].search(
            [('id', '!=', self.id), ('employee_id', '=', self.employee_id.id),
             ('state', '=', 'done'), ('last_renewal', '=', True)], order='id desc', limit=1)
        default = {
            'job_id': self.job_id.id,
            'employee_id': self.employee_id.id,
            'department_id': self.department_id.id,
            # 'date_start': self.new_contract_start_date,
            'date_end': self.new_contract_end_date,
            'name': 'Re-Contract' + self.employee_id.name,
            'state': 'program_directory',
        }
        if self.increase_salary == 'yes':

            default.update({'wage': self.new_salary_degree.base_salary,
                            'salary_scale': self.new_salary_scale.id,
                            'salary_level': self.new_salary_level.id,
                            # 'experience_year': self.experience_year,
                            'salary_group': self.new_salary_group.id,
                            'salary_degree': self.new_salary_degree.id,
                            })

        else:
            default.update({'wage': self.contract_id.salary_degree.base_salary,
                            'salary_scale': self.contract_id.salary_scale.id,
                            'salary_level': self.contract_id.salary_level.id,
                            'experience_year': self.contract_id.experience_year,
                            'salary_group': self.contract_id.salary_group.id,
                            'salary_degree': self.contract_id.salary_degree.id,
                            })

        c_id = self.contract_id.copy(default=default)

        for line in self.contract_id.employee_dependant:
            line.contract_id = c_id.id

        for line in self.contract_id.advantages:
            line.contract_advantage_id = c_id.id

        self.contract_id.write({'active': False})
        if last_record:
            last_record.last_renewal = False
        if self.contract_type == 'permanent':
            c_id.contract_description = 'permanent'
        # Employee back to service
        self.employee_id.state = 'open'
        self.contract_id.state = 'program_directory'

        self.state = "done"


    def action_re_hr_manager(self):
        self.state='hr_manager'

class HrContractTrahum(models.Model):
    _inherit = 'hr.contract'

    state = fields.Selection(selection=[
        ('draft', _('Draft')),
        ('employeed_aproval', _('Employeed Approval')),
        ('hr_head_approval', _('HR Head Approval')),
        ('secret_general', _('Secret General')),
        ('secretary_general', _('Secretary General')),
        ('program_directory', _('Executive Approval')),

        ('end_contract', _('End Contract'))
    ], default='draft', tracking=True)

    is_branch = fields.Many2one(related='department_id.branch_name', store=True, readonly=True)

    delgiation_status_type = fields.Selection(selection=[
        ('employee', 'Employee'),
        ('manager', 'Manager'),
        ('gm', 'General Manager'), ])

    # def action_sector_head_approval(self):
    #     """Approve contract by Sector Head"""
    #     if self.state != 'hr_head_approval':
    #         raise exceptions.UserError("Only HR Head approved contracts can proceed to Sector Head Approval.")
    #     self.state = 'sector_head_approval'

    def employeed_aproval(self):
        # self.chick_saudi_percentage()
        self.state = "employeed_aproval"

    def hr_head_approval(self):
        # self.chick_saudi_percentage()
        self.state = "hr_head_approval"

    def action_sector_head_approval(self):
        if self.is_branch:
            self.state = "secret_general"
        else:
            self.program_directory()

    def action_secret_general(self):
        self.program_directory()


class HrOfficialMissionTrahum(models.Model):
    _inherit = 'hr.official.mission'
    #

    state = fields.Selection([('draft', _('Draft')),
                              ('send', _('Waiting Direct Manager')),
                              ('direct_manager', _('Waiting Department Manager')),
                              ('depart_manager', _('Wait HR Department')),
                              ('hr_aaproval', _('Wait HR Manager')),
                              ('hr_manager_approve', _('Sector Head Approval')),
                              ('hr_manager_approve2', _('Wait Shared Service')),
                              ('sector_head_approval', 'Wait General Manager Approval'),
                              ('shared_service_approval', 'Wait Executive Manager Approval'),
                              ('secret_general', 'Secret General'),
                              ('approve', _('Approved')),
                              ('refused', _('Refused'))], default="draft", tracking=True)

    def hr_manager_approve(self):
            self.state = "hr_manager_approve2"
        # else:
        #     self.state = "hr_manager_approve"

    def hr_aaproval(self):
        # self.chick_employee_ids()
        self.employee_ids.chick_not_overtime()
        self.employee_ids.compute_Training_cost_emp()
        if not self.is_branch:
            self.state = "hr_aaproval"
        else:
            self.state = 'hr_manager_approve'

    def direct_manager(self):
        self.employee_ids.chick_not_overtime()
        self.employee_ids.compute_Training_cost_emp()

        for rec in self:
            is_especial = rec.process_type == 'especially_hours'
            employee = rec.sudo().employee_id
            parent = employee.parent_id
            hr_manager = employee.user_id.company_id.hr_manager_id

            if parent:
                user_id = rec.env.uid
                if parent.user_id.id == user_id or hr_manager.user_id.id == user_id:
                    rec.state = "direct_hr" if is_especial else "direct_manager"
                else:
                    raise exceptions.Warning(_(
                        'Sorry, The Approval For The Direct Manager %s Only OR HR Manager!'
                    ) % parent.name)
            else:
                rec.state = "direct_hr" if is_especial else "direct_manager"

    def action_sector_head_approval(self):
        self.state = "sector_head_approval"

    def action_shared_service_approval(self):
        self.state = "shared_service_approval"

    def action_secret_general(self):
        self.state = "approve"

    def executive_office2(self):
        self.state = "executive_office2"


class HrLoanSalaryAdvanceInherit(models.Model):
    _inherit = 'hr.loan.salary.advance'

    state = fields.Selection(
        [('draft', _('Draft')),
         ('submit', _('Waiting Payroll Officer')),
         ('direct_manager', _('Wait HR Department')),
         ('director_financial_management', _('Director Financial Management')),
         ('sector_head_approval', _('Sector Head Approval')),
         ('sheared_service_approval', _('Shared Service Approval')),
         ('gm_approve', _('Wait Secretary-General Approval')),
         ('branch_gm_approve', _('Wait Excutive Manager Approval')),
         ('wait_transfer', _('Wait Transfer')),
         ('secret_general', _('Secret General')),
         ('pay', _('Transferred')), ('refused', _('Refused')),
         ('closed', _('Loan Suspended'))],
        default="draft", tracking=True)
    is_branch = fields.Many2one(related='department_id.branch_name', store=True, readonly=True)

    def action_director_financial_management(self):
        self.state = "director_financial_management"

    def action_sector_head_approval(self):
        if self.is_branch:
            self.state = "sheared_service_approval"
        else:
            self.state = "sector_head_approval"

    def gm_approve(self):
        self.state = "gm_approve"

    def branch_gm_approve(self):
        self.state = "branch_gm_approve"

    def secret_general_approval(self):
        self.state = "wait_transfer"

    def executive_manager(self):
        if self.is_branch:
            self.state = "secret_general"
        else:
            self.state = 'wait_transfer'

    def direct_manager(self):
        if not self.is_branch:
            self.state = "direct_manager"
        else:
            self.state = 'director_financial_management'




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
        ('sector_head_approval', "Sector Head Approval"),
        ("shared_service_approval", "Wait Shared Service"),
        ("gm_manager", "Wait General Manager"),
        ("branch_gm_manager", "Wait Excutive Manager"),
        ("secret_general", "Secret General"),
        ("done", "Wait Transfer"),
        ("pay", "Transferred"),
        ("refused", "Refused")], default='draft', tracking=True)
    is_branch = fields.Many2one(related='department_id.branch_name', store=True, readonly=True)

    def complete(self):
        if self.is_branch:
            self.state = 'secret_general'
        else:
            self.state = 'done'

    def action_sector_head_approval(self):
        self.state = "gm_manager"

    def action_shared_service_approval(self):
        self.state = "branch_gm_manager"

    def hr_manager_approve(self):
            self.state = "shared_service_approval"



    def action_secret_general(self):
        self.state = "done"

    def finance_manager(self):
        self.re_compute_salary_rules_and_loans()
        # check for clearance for employee
        employee_clearance = self.env['hr.clearance.form'].sudo().search([('employee_id', '=', self.employee_id.id),
                                                                   ('clearance_type', '!=', 'vacation'),
                                                                   ('state', 'in', ['done', 'wait'])])
        if len(employee_clearance) == 0 and self.cause_type.clearance:
            raise exceptions.Warning(
                _('You can not create termination when missing clearance for Employee %s') % self.employee_id.name)
        if self.employee_id:
            #             self.employee_id.state = 'under_out_of_service'
            self.employee_id.sudo().contract_id.state = 'end_contract'
        if not self.is_branch:
            self.state = 'finance_manager'
        else:
            self.state = "sector_head_approval"


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    state = fields.Selection(selection_add=[('hr_manager_approval', _('HR Manager Approval')),
                                            ('accounting_head_approval', _('Accounting Head Approval')),
                                            ('sector_head_approval', _('Sector Head Approval')),
                                            ('sheard_service_approval', _('Sheared Service Approval')),
                                            ('secretary_general', _('Secretary General')),
                                            ('branch_excutive_manager', _('Excutive Manager')),
                                            ('transfered', 'Transfer')
                                            ], tracking=True)
    is_branch = fields.Many2one("hr.department", domain=[('is_branch', '=', True)])

    def action_hr_manager_approval(self):
        self.state = "hr_manager_approval"

    def action_accounting_head_approval(self):
        self.state = "accounting_head_approval"

    def action_sector_head_approval(self):
        self.state = "sector_head_approval"

    def action_sheard_service_approval(self):
        self.state = "sheard_service_approval"

    def action_secretary_general(self):
        self.state = "secretary_general"

    def action_branch_excutive_manager(self):
        self.state = "branch_excutive_manager"


class HrPayslipRuninhirt(models.Model):
    _inherit = 'hr.payslip.run'

    state = fields.Selection(selection_add=[('computed', 'Computed'),
                                            ('confirmed', 'Confirmed'),
                                            ('hr_manager_approval', _('Wait Accounting Manager')),
                                            ('accounting_head_approval', _('Wait Shared Service')),
                                            ('sector_head_approval', _('Wait General Manager')),
                                            ('sheard_service_approval', _('Wait Excutive Manager')),
                                            ('secretary_general', _('Wait Finance Transfer')),
                                            ('branch_excutive_manager', _('Wait Finance Transfer')),
                                            ('transfered', 'Transfer')], tracking=True)

    is_branch = fields.Many2one("hr.department", string="Branch", domain=[('is_branch', '=', True)])

    def action_hr_manager_approval(self):
        self.state = "hr_manager_approval"

    def action_accounting_head_approval(self):
        self.state = "accounting_head_approval"

    def action_sector_head_approval(self):
        self.state = "sector_head_approval"

    def action_sheard_service_approval(self):
        self.state = "sheard_service_approval"

    def action_secretary_general(self):
        self.state = "secretary_general"

    def action_branch_excutive_manager(self):
        self.state = "branch_excutive_manager"


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
    def complete_data(self):
        for employee in self:
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
            if item.birthday:
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
        while current_department.parent_id:
            if current_department.manager_id.id != self.id: break
            current_department = current_department.parent_id
        manager_id = current_department.manager_id
        return manager_id

    def _assign_top_manager(self, department, direct_manager):
        manager_id = False
        current_department = department.parent_id and department.parent_id or department
        while current_department.parent_id:
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

    def _onchange_department(self):
        manager = self._assign_manager(self.department_id)
        coach = self._assign_top_manager(self.department_id, manager)
        self.parent_id = manager.id
        self.coach_id = coach.id

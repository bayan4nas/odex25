# -*- coding: utf-8 -*-


from odoo import models, fields, api, _, exceptions

import logging


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
                              ('secretary_general', _('Secretary General')),
                              ('hr_aaproval', _('Wait Approval')),
                              ('approve', _('Approved')),
                              ('refused', _('Refused'))], default="draft", tracking=True)

    def action_sector_head_approval(self):
        self.state = "sector_head_approval"

    def action_secretary_general(self):
        self.state = "secretary_general"


class EmployeeOvertimeRequestTrahum(models.Model):
    _inherit = 'employee.overtime.request'


    state = fields.Selection(
        [('draft', _('Draft')),
         ('submit', _('Waiting Direct Manager')),
         ('direct_manager', _('Waiting Department Manager')),
         ('financial_manager', _('Wait HR Department')),
         ('sector_head_approval', _('Sector Head Approval')),
         ('secretary_general', _('Secretary General')),
         ('hr_aaproval', _('Wait Approval')),
         ('executive_office', _('Wait Transfer')),
         ('validated', _('Transferred')),
         ('refused', _('Refused'))], default="draft", tracking=True)

    def action_sector_head_approval(self):
        self.state = "sector_head_approval"


    def action_secretary_general(self):
        self.state = "secretary_general"



class HrLoanSalaryAdvanceInherit(models.Model):
    _inherit = 'hr.loan.salary.advance'

    state = fields.Selection(
                [('draft', _('Draft')),
                 ('submit', _('Waiting Payroll Officer')),
                 ('direct_manager', _('Wait HR Department')),
                 ('sector_head_approval', _('Sector Head Approval')),
                 ('secretary_general', _('Secretary General')),
                 ('hr_manager', _('Wait GM Approval')),
                 ('executive_manager', _('Wait Transfer')),
                 ('pay', _('Transferred')), ('refused', _('Refused')),
                 ('closed', _('Loan Suspended'))],
            default="draft", tracking=True)

    def action_sector_head_approval(self):
        self.state = "sector_head_approval"


    def action_secretary_general(self):
        self.state = "secretary_general"

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
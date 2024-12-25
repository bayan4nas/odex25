# -*- coding: utf-8 -*-
##############################################################################
#
#   Expert (LCT, Life Connection Technology)
#    Copyright (C) 2021-2022 LCT
#
##############################################################################

from datetime import datetime, date
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProjectCustom(models.Model):
    _inherit = 'project.project'
    _description = "Real Estate Project"

    def _get_task_type(self):
        """
        :return:  project task type if it default
        """
        type_ids = self.env['project.task.type'].search([('case_default', '=', True)])
        return type_ids

    code = fields.Char(string="Code")
    project_type = fields.Selection([('with_bone', 'With Bone'),
                                     ('without_bone', 'Without Bone'),
                                     ('finishing', 'Finishing')], string="Project Type", default='with_bone')
    project_owner_type = fields.Selection([('company', 'Company'),
                                           ('investment', 'Investment')], string="Owner Type")
    branch_id = fields.Many2one('res.branches', string="Branch")
    member_ids = fields.Many2many('res.users', string="Project Member")
    date_start = fields.Date(string="Start Date")
    date_end = fields.Date(string="End Date")
    # attachment_ids = fields.One2many('ir.attachment', 'project_id', string="Attachment")
    type_ids = fields.Many2many('project.task.type', 'project_task_type_rel', 'project_id', 'type_id',
                                string='Tasks Stages', default=_get_task_type)
    engineering_office_id = fields.Many2one('res.partner', string="Engineering Office")
    engineering_contract_amount = fields.Float(string="Contract Value")
    engineering_contract_balance = fields.Float(string="Engineering Contract Balance", compute="get_contract_balance")
    engineering_office_line_ids = fields.One2many('engineering.office.line', 'project_id',
                                                  string="Engineering Office Payment", copy=True, auto_join=True)
    project_estimated_quantities_ids = fields.One2many('project.estimated.quantities', 'project_id',
                                                       string="Project Estimated Quantities")
    project_expenses_account_id = fields.Many2one('account.account', string='Project Expenses Account')
    project_investment_account_id = fields.Many2one('account.account', string='Project Investment Account')
    discount_account_id = fields.Many2one('account.account', string='Discount Account')
    subcontractor_work_ids = fields.One2many('subcontractor.work','project_id', string="Subcontractor")
    spayment_counts = fields.Integer(string='Subcontractor Payment', compute='count_payment_number')
    epayment_counts = fields.Integer(string='Engineering Payment', compute='count_payment_number')
    sinstallment_count = fields.Integer(string='Subcontractor Installment', compute='count_installment')
    state = fields.Selection([('draft', 'Draft'),
                                     ('in_progess', 'In Progress'),
                                     ('done', 'Done'),
                                     ('cancel', 'Cancelled'),], string="Status", default='draft')
    project_cost = fields.Float(string="Project Cost", compute="get_project_cost")
    estimated_cost = fields.Float(string="Estimated Cost", compute="get_project_cost")
    project_total_cost = fields.Float(string="Project Expected Cost")
    project_revenue = fields.Float(string="Project Revenue",compute="get_project_cost")
    street = fields.Char(string='Street', copy=False)
    city = fields.Many2one('re.city', string="City", copy=False)
    district = fields.Many2one('district',string="District", copy=False)

    @api.depends('project_total_cost','subcontractor_work_ids', 'subcontractor_work_ids.contract_amount', 'project_estimated_quantities_ids', 'project_estimated_quantities_ids.total_estimated_qty', 'engineering_contract_amount')
    def get_project_cost(self):
        estimated_cost = 0.0
        project_cost = 0.0
        for rec in self:
            for line in rec.project_estimated_quantities_ids:
                estimated_cost += line.total_estimated_qty
            for subcontractor in rec.subcontractor_work_ids:
                project_cost += subcontractor.contract_amount
            project_cost += rec.engineering_contract_amount
            rec.project_cost = project_cost
            rec.estimated_cost = estimated_cost
            rec.project_revenue = rec.project_total_cost - rec.project_cost


    def _check_validations(self):
        for record in self:
            if record.engineering_contract_amount == 0.0:
                raise ValidationError(_("To Proceed,Contract Value Cannot be zero"))
            if not record.engineering_office_line_ids:
                raise ValidationError(_("To Proceed,Please Insert Engineering Office Payment"))
            if record.engineering_office_line_ids:
                due_date = record.engineering_office_line_ids.mapped('due_date')
                if len (due_date) == 1 and not due_date[0]:
                    raise ValidationError(_("To Proceed,Please Insert Engineering Office Payment"))
            if not record.project_estimated_quantities_ids:
                raise ValidationError(_("To Proceed,Please Insert Project Estimated Quantities"))
            if not record.subcontractor_work_ids:
                raise ValidationError(_("To Proceed,Please Insert Subcontractor"))

    def action_submit(self):
        self._check_validations()
        self.state = 'in_progess'

    def action_done(self):
        paid = True
        contract_installment = self.env['subcontractor.installment'].search([('project_id', '=', self.id)])
        # Check Contractor Payment
        for payment in contract_installment.installment_line_ids:
            if not payment.paid:
                paid = False
        # Check Engineering Payment
        for engineering_payment in self.engineering_office_line_ids:
            if not engineering_payment.paid:
                paid = False
        if paid:
            self.state = 'done'

        elif not paid:
            raise ValidationError(_("Please Check Project Payment first To Mark This Project as Done"))

    def action_draft(self):
        self.state = 'draft'


    def action_cancel(self):
        self.state = 'cancel'

    def get_subcontractor_payment(self):
        subcontractor_payment_ids = self.env['project.payment.request'].search([('project_id', '=', self.id),
                                                                          ('type', '=', 'subcontractor')])
        form_id = self.env.ref('project_management_custom.project_payment_request_view_forms').id
        tree_id = self.env.ref('project_management_custom.project_payment_request_view_tree').id
        domain = [('id', 'in', subcontractor_payment_ids.ids)]
        return {
            'name': _('Subcontractor Payment'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'project.payment.request',
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': domain,
        }

    def get_engineering_payment(self):
        engineering_payment_ids = self.env['project.payment.request'].search([('project_id', '=', self.id),
                                                                                      ('type', '=', 'eng_office')])
        form_id = self.env.ref('project_management_custom.project_payment_request_view_forms').id
        domain = [('id', 'in', engineering_payment_ids.ids)]
        return {
            'name': _('Engineering Office Payment'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'project.payment.request',
            'views': [(False, 'tree'), (form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': domain,
        }

    def get_subcontractor_installment(self):
        subcontractor_installment_ids = self.env['subcontractor.installment'].search(
            [('project_id', '=', self.id)])
        form_id = self.env.ref('project_management_custom.subcontractor_installment_form').id
        domain = [('id', 'in', subcontractor_installment_ids.ids)]
        return {
            'name': _('Subcontractor Installment'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'subcontractor.installment',
            'views': [(False, 'tree'), (form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': domain,
        }

    def count_installment(self):
        sinstallment_count = self.env['subcontractor.installment'].search_count([('project_id', '=', self.id)])
        self.sinstallment_count = sinstallment_count

    def count_payment_number(self):
        spayment_count = self.env['project.payment.request'].search_count([('project_id', '=', self.id),
                                                                          ('type', '=', 'subcontractor')])
        epayment_count = self.env['project.payment.request'].search_count([('project_id', '=', self.id),
                                                                           ('type', '=', 'eng_office')])

        self.spayment_counts = spayment_count
        self.epayment_counts = epayment_count


    @api.depends('engineering_office_line_ids', 'engineering_office_line_ids.amount',
                 'engineering_office_line_ids.paid')
    def get_contract_balance(self):
        for rec in self:
            paid_amount = sum([line.amount if line.paid == True else 0.0 for line in rec.engineering_office_line_ids])
            rec.engineering_contract_balance = rec.engineering_contract_amount - paid_amount

    @api.constrains('engineering_contract_amount')
    def check_amount(self):
        for rec in self:
            if rec.engineering_contract_amount < 0.0:
                raise ValidationError(_("Contract Value Cannot be less than zero"))

    @api.constrains('engineering_office_line_ids', 'engineering_office_line_ids.amount')
    def check_total(self):
        for rec in self:
            line_amount = sum([line.amount for line in rec.engineering_office_line_ids])
            if rec.engineering_office_line_ids:
                for line in rec.engineering_office_line_ids:
                    if line_amount > rec.engineering_contract_amount or line_amount < rec.engineering_contract_amount and not line.display_type:
                        raise ValidationError(
                            _("Please Check Payment Line Must Be equal to %s") % rec.engineering_contract_amount)


# class IrAttachment(models.Model):
#     _inherit = "ir.attachment"
#     _description = "Project Attachment"

#     project_id = fields.Many2one('project.project', string="Project")

#-*- coding: utf-8 -*-

from odoo import models, fields, api, _, exceptions
from odoo.exceptions import UserError, ValidationError


class EmployeeOtherRequest(models.Model):
    _inherit = "employee.other.request"

    journal_id = fields.Many2one('account.journal', 'Salary Journal')
    move_id = fields.Many2one('account.move', string="Move Number")
    rule_id = fields.Many2one('hr.salary.rule', string="Allowance Name",
                              default=lambda self: self.env['hr.salary.rule'].search([('compensation_rule', '=', True)],
                                                                                     limit=1))
    item_budget_id = fields.Many2one(related='rule_id.item_budget_id')
    operation_type = fields.Selection(selection=[('operation_budget', 'Operation Budget'), ('other_budget', 'Other')],
                                      default='operation_budget', tracking=True)
    other = fields.Char('Oher')

    # @api.model
    # def get_email_to(self):
    #     user_group = self.env.ref("account_budget_custom.group_department_manager_budget")
    #     email_list = [usr.partner_id.email for usr in user_group.users if usr.partner_id.email]
    #     return ",".join(email_list)
    #
    # def schedule_activity_on_approval(self):
    #     budget_manager_group = self.env.ref("account_budget_custom.group_department_manager_budget")
    #     budget_managers = self.env['res.users'].search([('groups_id', 'in', budget_manager_group.id)])
    #
    #     note = _("Your approval is required for the compensation requset")
    #
    #     for manager in budget_managers:
    #         self.activity_schedule(
    #             'mail.mail_activity_data_todo',
    #             fields.Date.today(),
    #             note=note,
    #             user_id=manager.id or self.env.uid
    #         )
    def confirm(self):
        super(EmployeeOtherRequest, self).confirm()
        if self.request_type == 'compensation':
            domain = [('type', '=', 'purchase'), ('hr_journal', '=', True)]
            journal = self.env['account.journal'].search(domain, limit=1)
            self.journal_id = journal.id

    def approved(self):
        super(EmployeeOtherRequest, self).approved()
        if self.request_type == 'compensation':
            self.create_workers_compensation()

    def create_workers_compensation(self):
        domain = [('type', '=', 'purchase'), ('hr_journal', '=', True)]
        journal = self.env['account.journal'].search(domain, limit=1)
        for rec in self:
            invoice_line_ids = [(0, 0, {
                'name': rec.rule_id.name,
                'account_id': rec.rule_id.rule_debit_account_id.id,
                'analytic_account_id': rec.rule_id.analytic_account_id.id,
                'item_budget_id': rec.rule_id.item_budget_id.id,
                'quantity': 1.0,
                'price_unit': rec.amount,
            })]
            bill = self.env['account.move'].sudo().create({
                'partner_id': rec.company_id.partner_id.id,
                'journal_id': journal.id,
                'hr_operation': True,
                'invoice_line_ids': invoice_line_ids,
                'date': rec.date,
                'invoice_date': rec.date,
                'move_type': 'in_invoice',
                'ref': _("Compensation Requset For %s") % self.sudo().employee_id.name,
                'narration': "%s - %s" % (self.sudo().employee_id.name, rec.school),
            })
            rec.move_id = bill.id

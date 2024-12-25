# -*- coding: utf-8 -*-
##############################################################################
#
#   Expert (LCT, Life Connection Technology)
#    Copyright (C) 2021-2022 LCT
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ProjectExpense(models.Model):
    _name = 'project.expense'
    _description = "Project Expense"

    name = fields.Many2one('project.expense.conf',string="Description")
    partner_id = fields.Many2one('res.partner', string="Vendor")
    project_id = fields.Many2one('project.project', string="Project")
    date = fields.Date(string="Date", default=fields.Date.context_today)
    amount = fields.Float(string="Amount")
    paid = fields.Boolean(string="Paid")
    invoice_id = fields.Many2one('account.move', string="Invoice")

    def _prepare_invoice_values(self, expense, name_spec, account_id, amount):
        invoice_vals = {
            'ref': expense.name.name,
            'move_type': 'in_invoice',
            'invoice_origin': expense.name.name,
            'invoice_user_id': self.env.user.id,
            'invoice_date': expense.date,
            'project_expense_id': expense.id,
            'invoice_date_due': expense.date,
            'narration': expense.name.name,
            'partner_id': expense.partner_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': name_spec,
                'price_unit': amount,
                'quantity': 1.0,
                'account_id': account_id.id,
            })],
        }

        return invoice_vals

    def create_invoice(self):
        if not self.project_id.project_expenses_account_id or not self.project_id.project_investment_account_id:
            raise UserError(_('Please Contact Administrator to configure your project accounts.'))
        if self.project_id.project_owner_type == 'company':
            account_id = self.project_id.project_expenses_account_id
        else:
            account_id = self.project_id.project_investment_account_id
        name_spec = 'Expense Reference:' + str(self.name.name) + '-' + str(self.project_id.name)
        invoice = self._prepare_invoice_values(self, name_spec, account_id, self.amount)
        invoice_id = self.env['account.move'].sudo().create(invoice).with_user(self.env.uid)
        self.write({'invoice_id': invoice_id.id})


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    project_expense_id = fields.Many2one('project.expense', string='Project Expense')

    def action_post(self):
        res = super(AccountInvoice, self).action_post()
        if self.project_expense_id:
            self.project_expense_id.paid = True
        return res

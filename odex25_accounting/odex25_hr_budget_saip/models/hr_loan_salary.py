# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime, date, timedelta
from odoo.exceptions import UserError, ValidationError


class LoanRequestTypes(models.Model):
    _inherit = 'loan.request.type'

    item_budget_id = fields.Many2one('item.budget', 'Budget Item')


class HrSalaryAdvance(models.Model):
    _inherit = "hr.loan.salary.advance"

    def pay(self):

        AccountBudgetPost = self.env['account.budget.post']

        for item in self:
            if item.is_old:
                continue

            budget_lines = item.request_type.item_budget_id.crossovered_budget_line.filtered(
                lambda bl: bl.crossovered_budget_id.state == 'done'
                           and bl.date_from <= item.date <= bl.date_to)
            if not budget_lines:
                raise ValidationError(_('No budget for this service: {} - {}').format(item.request_type.name, item.request_type.item_budget_id.name))

            valid_posts = AccountBudgetPost.search([]).filtered(lambda post: item.request_type.account_id in post.account_ids)
            general_budget = item.request_type.item_budget_id.crossovered_budget_line.filtered(lambda bl: bl.general_budget_id in valid_posts)
            if not general_budget:
                raise ValidationError(_('No budget for this account: {}').format(item.request_type.account_id.name))

            if not item.gm_propos_amount or item.gm_propos_amount <= 0:
                raise ValidationError(_("Cannot create invoice without a valid amount."))

            if not item.request_type.account_id:
                raise ValidationError(_("No account defined for this request type."))

            invoice_vals = {
                'partner_id': item.employee_id.user_id.partner_id.id,
                'journal_id': item.request_type.journal_id.id,
                'hr_operation': True,
                'state': 'draft',
                'move_type': 'in_invoice',
                'date': item.date,
                'ref': 'Loan',
                'invoice_line_ids': [(0, 0, {
                    'name': item.request_type.name or 'Salary Advance',
                    'account_id': item.request_type.account_id.id,
                    'item_budget_id': item.request_type.item_budget_id.id or False,
                    'quantity': 1.0,
                    'price_unit': item.gm_propos_amount,
                })],
            }

            if not invoice_vals.get('invoice_line_ids'):
                raise ValidationError(_("Invoice must contain at least one line."))

            invoice = self.env['account.move'].create(invoice_vals)

            attachments = self.env['ir.attachment'].sudo().search([('res_model', '=', 'hr.loan.salary.advance'),('res_id', '=', item.id)])
            for attachment in attachments:
                attachment.sudo().copy({
                    'res_model': 'account.move',
                    'res_id': item.id,
                })


            if not item.moves_ids:
                self.env['hr.account.moves'].create({
                    'number': item.code,
                    'amount': item.gm_propos_amount,
                    'journal': item.request_type.journal_id.id,
                    'partner_id': item.employee_id.user_id.partner_id.id,
                    'date': item.date,
                    'journal_move_id': invoice.id,
                    'moves_id': item.id
                })

            item.state = "pay"
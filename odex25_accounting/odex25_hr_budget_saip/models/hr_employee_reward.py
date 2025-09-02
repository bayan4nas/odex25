# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class LoanRequestTypes(models.Model):
    _inherit = 'hr.employee.reward'

    item_budget_id = fields.Many2one('item.budget', 'Budget Item')
    move_id = fields.Many2one('account.move')

    def action_done(self):
        AccountBudgetPost = self.env['account.budget.post']
        if self.transfer_type == 'accounting':
            for item in self:
                # تحقق من الميزانية
                budget_lines = item.item_budget_id.crossovered_budget_line.filtered(
                    lambda bl: bl.crossovered_budget_id.state == 'done'
                               and bl.date_from <= item.date <= bl.date_to)
                if not budget_lines:
                    raise ValidationError(_('No budget for this service: {}').format(item.item_budget_id.name))

                valid_posts = AccountBudgetPost.search([]).filtered(
                    lambda post: item.account_id in post.account_ids)
                general_budget = item.item_budget_id.crossovered_budget_line.filtered(
                    lambda bl: bl.general_budget_id in valid_posts)
                if not general_budget:
                    raise ValidationError(_('No budget for this account: {}').format(item.account_id.name))

                if not item.account_id:
                    raise ValidationError(_("No account defined"))

                # -------- 👇 هنا نجمع الخطوط (بدل ما ننشئ فاتورة لكل واحد)
                invoice_lines = []
                for record in item.line_ids_reward:
                    if not record.amount or record.amount <= 0:
                        raise ValidationError(_("Cannot create invoice without a valid amount."))
                    if not record.account_id:
                        raise ValidationError(_("No expense account defined for employee: %s") % record.employee_id.name)
                    if not record.journal_id:
                        raise ValidationError(_("No journal defined for employee: %s") % record.employee_id.name)
                    if record.account_id.user_type_id.type not in ['expense', 'other']:
                        raise ValidationError(
                            _("The account %s is not valid for invoice lines. It must be an Expense account.") % record.account_id.display_name)

                    line_vals = (0, 0, {
                        'name': record.employee_id.name,
                        'account_id': record.account_id.id,
                        'quantity': 1.0,
                        'price_unit': record.amount,
                        'item_budget_id': item.item_budget_id.id if item.item_budget_id else False,
                    })
                    invoice_lines.append(line_vals)

                # -------- 👇 ننشئ فاتورة واحدة فيها كل الخطوط
                invoice_vals = {
                    'partner_id': item.company_id.partner_id.id,  # الشركة كطرف مقابل
                    'journal_id': item.journal_id.id,  # ناخذ أول journal (ممكن تخليها ثابتة)
                    'move_type': 'in_invoice',
                    'hr_operation': True,
                    'date': item.date,
                    'ref': _("Rewards Batch - %s") % item.allowance_reason,
                    'invoice_line_ids': invoice_lines,
                }

                invoice = self.env['account.move'].create(invoice_vals)
                item.move_id = invoice.id

            self.state = "done"
#
# -*- coding: utf-8 -*-
# from odoo import models, fields, api, _
# from odoo.exceptions import UserError, ValidationError
#
#
#
# class LoanRequestTypes(models.Model):
#     _inherit = 'hr.employee.reward'
#
#     item_budget_id = fields.Many2one('item.budget', 'Budget Item')
#     move_id = fields.Many2one('account.move')
#
#     def action_done(self):
#         AccountBudgetPost = self.env['account.budget.post']
#         if self.transfer_type == 'accounting':
#             for item in self:
#                 budget_lines = item.item_budget_id.crossovered_budget_line.filtered(
#                     lambda bl: bl.crossovered_budget_id.state == 'done'
#                                and bl.date_from <= item.date <= bl.date_to)
#                 if not budget_lines:
#                     raise ValidationError(_('No budget for this service: {}').format(item.item_budget_id.name))
#
#                 valid_posts = AccountBudgetPost.search([]).filtered(
#                     lambda post: item.account_id in post.account_ids)
#                 general_budget = item.item_budget_id.crossovered_budget_line.filtered(
#                     lambda bl: bl.general_budget_id in valid_posts)
#                 if not general_budget:
#                     raise ValidationError(_('No budget for this account: {}').format(item.account_id.name))
#
#                 if not item.account_id:
#                     raise ValidationError(_("No account defined"))
#                 for record in item.line_ids_reward:
#                     if not record.amount or record.amount <= 0:
#                         raise ValidationError(_("Cannot create invoice without a valid amount."))
#                     if not record.account_id:
#                         raise ValidationError(_("No expense account defined for employee: %s") % record.employee_id.name)
#                     if not record.journal_id:
#                         raise ValidationError(_("No journal defined for employee: %s") % record.employee_id.name)
#                     if record.account_id.user_type_id.type not in ['expense', 'other']:
#                         raise ValidationError(
#                             _("The account %s is not valid for invoice lines. It must be an Expense account.") % record.account_id.display_name)
#
#                     invoice_vals = {
#                         'partner_id': record.company_id.partner_id.id,
#                         'journal_id': record.journal_id.id,
#                         'move_type': 'in_invoice',
#                         'hr_operation': True,
#                         'date': item.date,
#                         'ref': record.employee_id.name,
#                         'invoice_line_ids': [(0, 0, {
#                             'name': record.employee_id.name,
#                             'account_id': record.account_id.id,
#                             'quantity': 1.0,
#                             'price_unit': record.amount,
#                             'item_budget_id': item.item_budget_id.id if item.item_budget_id else False,
#                         })],
#                     }
#
#                     invoice = self.env['account.move'].create(invoice_vals)
#
#                     record.move_id = invoice.id
#
#             self.state = "done"

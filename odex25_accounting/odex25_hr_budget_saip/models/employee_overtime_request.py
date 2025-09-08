# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, exceptions
from odoo.exceptions import UserError, ValidationError


class HREmployeeOvertimeRequest(models.Model):
    _inherit = 'employee.overtime.request'

    def action_overtime_return(self):
        return {
            'name': _('Return Overtime request'),
            'type': 'ir.actions.act_window',
            'res_model': 'overtime.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
             'context': {'default_reason': '', 'default_type':'overtime'}
        }

    # @api.onchange('transfer_type', 'benefits_discounts', 'journal_id', 'line_ids_over_time')
    # def onchange_transfer_type(self):
    #     if self.transfer_type == 'accounting':
    #         for line in self.line_ids_over_time:
    #             if self.state == 'account_manager':
    #
    #                 if not line.account_id:
    #                     line.account_id = self.benefits_discounts.rule_debit_account_id
    #                 if not line.journal_id:
    #                     line.journal_id = self.journal_id
    #             else:
    #                 line.account_id = False
    #                 line.journal_id = False

    # def hr_aaproval(self):
    #     self.chick_not_mission()
    #     self.state = "account_manager"

    def hr_aaproval(self):
        if self.transfer_type == "accounting":
            for item in self:
                for record in item.line_ids_over_time:
                    journal_id = record.employee_id.contract_id.working_hours.journal_overtime_id
                    emp_type = record.employee_id.get_emp_type_id()
                    item_budget_id = self.benefits_discounts.get_item_budget_id(emp_type)
                    budget_lines =  item_budget_id.crossovered_budget_line.filtered(
                        lambda bl: bl.crossovered_budget_id.state == 'done' and fields.Date.from_string(
                            bl.date_from) <= fields.Date.from_string(self.request_date) <= fields.Date.from_string(bl.date_to))
                    if not budget_lines:
                        raise ValidationError(_('No budget for this service: {} - {}').format(
                            self.benefits_discounts.name, self.item_budget_id.name))

                    general_budget = item.benefits_discounts.item_budget_id.crossovered_budget_line.filtered(
                        lambda bl: bl.general_budget_id in self.env['account.budget.post'].search([]).filtered(
                            lambda post: item.benefits_discounts.rule_debit_account_id in post.account_ids))
                    if not general_budget:
                        raise ValidationError(
                            _('No budget for this account: {}').format(item.benefits_discounts.rule_debit_account_id.name))
                    if record.price_hour > 0.0:
                        invoice_line_ids = [(0, 0, {
                            'name': self.benefits_discounts.name,
                            'account_id': self.benefits_discounts.rule_debit_account_id.id,
                            'analytic_account_id': self.benefits_discounts.analytic_account_id.id,
                            'item_budget_id': self.benefits_discounts.item_budget_id.id,
                            'quantity': 1.0,
                            'price_unit': record.price_hour,
                        })]
                        bill = self.env['account.move'].create({
                            'partner_id': record.employee_id.user_id.partner_id.id,
                            'journal_id': journal_id.id,
                            'hr_operation': True,
                            'invoice_line_ids': invoice_line_ids,
                            'date': self.request_date,
                            'invoice_date':  self.request_date,
                            'state': 'draft',
                            'move_type': 'in_invoice',
                            'ref': _("Overtime for %s") % item.employee_id.name,
                            # 'narration': "%s - %s" % (self.sudo().employee_id.name, rec.school),
                        })
                        record.move_id = bill.id
            self.state = "hr_aaproval"



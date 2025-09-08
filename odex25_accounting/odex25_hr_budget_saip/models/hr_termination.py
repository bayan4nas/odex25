from odoo import models, fields, api, _, exceptions
from datetime import date


class HrTermination(models.Model):
    _inherit = 'hr.termination'

    def action_termination_return(self):
        return {
            'name': _('Return Termination request'),
            'type': 'ir.actions.act_window',
            'res_model': 'overtime.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_reason': '', 'default_type':'termination'}
        }

    def pay(self):
        invoice_line_ids = []

        for item in self:
            if item.net > 0.0:
                allowance = item.cause_type.allowance_id
                emp_type = item.employee_id.get_emp_type_id()
                item_budget_id = allowance.get_item_budget_id(emp_type)
                if not allowance:
                    raise exceptions.Warning(_('Undefined end of service rule for %s.') % item.cause_type.name)
                if not allowance.rule_debit_account_id:
                    raise exceptions.Warning(_('Undefined debit account for salary rule %s.') % allowance.name)
                if not item_budget_id:
                    raise exceptions.Warning(_('Undefined item budget for salary rule %s.') % allowance.name)

                # Add the allowance or deduction to the invoice line items
                invoice_line_ids.append((0, 0, {
                    'name': allowance.name,
                    'account_id': allowance.rule_debit_account_id.id,
                    'analytic_account_id': allowance.analytic_account_id.id,
                    'item_budget_id': item_budget_id.id,
                    'quantity': 1.0,
                    'price_unit': item.net,
                }))

        if invoice_line_ids:
            move = self.env['account.move'].create({
                'state': 'draft',
                'partner_id': self.employee_id.user_id.partner_id.id,
                'move_type': 'in_invoice',
                'journal_id': self.journal.id,
                'date': date.today(),
                'invoice_date': date.today(),
                'ref': _('Termination of %s') % self.sudo().employee_id.name,
                'invoice_line_ids': invoice_line_ids,
            })

            self.write({'account_move_id': move.id})

        # Update employee's last work date and status
        if self.last_work_date:
            self.employee_id.sudo().write({'leaving_date': self.last_work_date})
            self.employee_id.contract_id.sudo().write({'date_end': self.last_work_date})

        self.sudo().employee_id.contract_id.state = 'end_contract'
        self.sudo().employee_id.state = 'out_of_service'

        # Set holiday balance to 0
        holiday_balance = self.env['hr.holidays'].sudo().search([
            ('type', '=', 'add'),
            ('check_allocation_view', '=', 'balance'),
            ('holiday_status_id.leave_type', '=', 'annual'),
            ('employee_id', '=', self.sudo().employee_id.id)
        ], limit=1)

        if holiday_balance:
            holiday_balance.remaining_leaves = 0
        self.state = 'pay'

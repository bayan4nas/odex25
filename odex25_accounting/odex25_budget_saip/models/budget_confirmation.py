# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import Warning, ValidationError


class BudgetConfirmationCustom(models.Model):
    _inherit = 'budget.confirmation'

    type = fields.Selection(selection_add=[('contract.contract', 'Contract')])
    contract_id = fields.Many2one('contract.contract')
    reminder = fields.Char('Reminder', default=lambda self: self._get_default_reminder())

    @api.model
    def _get_default_reminder(self):
        if self.env.user.lang == 'ar_001':
            return "تم تجاوز الميزانية"
        else:
            return "Budget exceeded"
    # todo start


    # todo end

    def action_reject(self):
        return {
            'name': _('Reject Budget Confirmation'),
            'type': 'ir.actions.act_window',
            'res_model': 'operation.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
             'context': {'default_confirmation': True}
        }

    def cancel(self):
        super(BudgetConfirmationCustom, self).cancel()
        # fix issue singltone error by add loop
        for record in self:
            if record.po_id and record.type == 'purchase.order':
                record.po_id.write({'state': 'budget_rejected'})
            if record.request_id and record.type == 'purchase.request':
                for line in record.lines_ids:
                    budget_lines = record.update_budget_lines(line)
                    amount = budget_lines.initial_reserve - line.amount
                    budget_lines.update({'initial_reserve': amount})
                record.request_id.write({'state': 'refuse'})
            if record.contract_id and record.type == 'contract.contract':
                record.contract_id.write({'state': 'cancel'})

    def update_budget_lines(self, line):
        budget_posts = self.env['account.budget.post'].search([]).filtered(
            lambda post: line.account_id in post.account_ids)
        budget_lines = line.item_budget_id.crossovered_budget_line.filtered(lambda budget_line: (
                budget_line.general_budget_id in budget_posts and budget_line.crossovered_budget_id.state == 'done' and budget_line.date_from <= self.date <= budget_line.date_to))
        return budget_lines

    def done(self):
        super(BudgetConfirmationCustom, self).done()
        for line in self.lines_ids:
            budget_lines = self.update_budget_lines(line)
            if not budget_lines:
                continue
            if self.po_id and self.type == 'purchase.order':
                amount = budget_lines.reserve + line.amount
                budget_lines.write({'reserve': amount})

                if self.po_id.requisition_id:
                    self.po_id.write({'state': 'to approve'})
                    self.po_id.requisition_id.write({'state': 'checked'})
                else:
                    if self.po_id.email_to_vendor:
                        self.po_id.write({'state': 'sent'})
                    else:
                        self.po_id.write({'state': 'draft'})

            if self.request_id and self.type == 'purchase.request':
                amount = budget_lines.initial_reserve + line.amount
                self.request_id.write({"state": "waiting"})
                budget_lines.update({'initial_reserve': amount})
            if self.contract_id and self.type == 'contract.contract':
                self.contract_id.write({'state': 'EDPC'})

    def confirm(self):
        super(BudgetConfirmationCustom, self).confirm()
        if self.contract_id and self.type == 'contract.contract':
            self.done()
        else:
            self.write({'state': 'confirmed'})



class BudgetConfirmationLine(models.Model):
    _inherit = 'budget.confirmation.line'

    item_budget_id = fields.Many2one('item.budget', 'Budget Item')

    def check_budget(self):
        self.ensure_one()
        if not self.account_id:
            raise ValidationError(_('All lines should have accounts'))

        date = self.date
        budget_post = self.env['account.budget.post'].search([]).filtered(
            lambda post: self.account_id in post.account_ids)
        budget_lines = self.item_budget_id.crossovered_budget_line.filtered(
            lambda line: (
                    line.general_budget_id in budget_post and
                    line.crossovered_budget_id.state == 'done' and
                    fields.Date.from_string(line.date_from) <= date <= fields.Date.from_string(line.date_to)))

        if budget_lines:
            remain = abs(budget_lines[0].remain)
            if remain >= self.confirmation_id.total_amount:
                return True
            if self.confirmation_id.exceed_budget:
                return True
        else:
            if not budget_post:

                raise ValidationError(
                    _('No general budget is linked to the account: %s in the budget post.') % self.account_id.name)

            # If budget exists but is not enough
        raise ValidationError(_('The exist budget is not enough for :') + self.item_budget_id.name)



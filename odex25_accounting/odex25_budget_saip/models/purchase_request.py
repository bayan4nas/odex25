# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from typing import Optional


class PurchaseRequest(models.Model):
    _inherit = 'purchase.request'

    item_budget_id = fields.Many2one('item.budget', 'Budget Item')

    def action_skip_budget(self):
        self.state = 'waiting'


    def action_confirm(self) -> Optional[bool]:
        for rec in self:
            rec.state = 'wait_for_send'
        return super(PurchaseRequest, self).action_confirm()

    def initial_engagement(self) -> None:
        for rec in self:
            rec.action_budget()
            rec.state = 'initial'

    def action_refuse(self):
        res = super(PurchaseRequest, self).action_refuse()
        for rec in self:
            budget_confs = self.env['budget.confirmation'].sudo().search([('request_id', '=', rec.id)])
            budget_confs.write({'state': 'cancel'})
        return res

    def action_cancel(self):
        budget_confirmation = self.env['budget.confirmation'].search([('request_id', '=', self.id)])
        if budget_confirmation:
            budget_confirmation.cancel()
        self.write({'state': 'cancel'})

    def action_budget(self):
        print("old one @@@@@@@@@@@@@@@@@")
        self.ensure_one()
        confirmation_lines = []
        total_amount = sum(line.line_total for line in self.line_ids)
        balance = 0.0

        if not self.item_budget_id:
            raise ValidationError(_("No budget item selected"))

        for line in self.line_ids:
            if not line.product_id:
                raise ValidationError(_("There is no product"))

            expense_account = line.product_id.property_account_expense_id or line.product_id.categ_id.property_account_expense_categ_id
            if not expense_account:
                raise ValidationError(_("This product has no expense account: {}").format(line.product_id.name))

            general_budget = self.item_budget_id.crossovered_budget_line.filtered(
                lambda bl: bl.general_budget_id in self.env['account.budget.post'].search([]).filtered(
                    lambda post: expense_account in post.account_ids))
            if not general_budget:
                raise ValidationError(_('No budget for this account: {}').format(expense_account.name))

            budget_lines = self.item_budget_id.crossovered_budget_line.filtered(
                lambda bl: bl.crossovered_budget_id.state == 'done' and fields.Date.from_string(
                    bl.date_from) <= fields.Date.from_string(self.date) <= fields.Date.from_string(bl.date_to))
            if not budget_lines:
                raise ValidationError(_('No budget for this service: {} - {}').format(
                    line.product_id.name, self.item_budget_id.name))

            budget_line = budget_lines[0]
            remain = abs(budget_line.available_liquidity)
            balance += line.line_total
            new_remain = remain - balance

            confirmation_lines.append((0, 0, {
                'amount': line.line_total,
                'item_budget_id': self.item_budget_id.id,
                'description': line.product_id.name,
                'budget_line_id': budget_line.id,
                # 'analytic_account_id': line.account_id.id,
                'remain': new_remain + line.line_total,
                'new_balance': new_remain,
                'account_id': expense_account.id,
            }))

        rec = self.env['budget.confirmation'].sudo().create({
            'name': self.name,
            'date': self.date,
            'state': 'bdgt_dep_mngr',
            'beneficiary_id': self.partner_id.id,
            'department_id': self.department_id.id,
            'type': 'purchase.request',
            'ref': self.name,
            'description': self.purchase_purpose,
            'total_amount': total_amount,
            'lines_ids': confirmation_lines,
            'request_id': self.id,
        })
        # self.write({'state': 'wait_budget'})




class PurchaseRequestLine(models.Model):
    _inherit = 'purchase.request.line'

    item_budget_id = fields.Many2one(related='request_id.item_budget_id')

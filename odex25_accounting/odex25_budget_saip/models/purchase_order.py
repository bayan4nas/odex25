from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    item_budget_id = fields.Many2one(related='request_id.item_budget_id')

    def action_budget(self):
        self.ensure_one()
        confirmation_lines = []
        total_amount = sum(line.price_subtotal for line in self.order_line)
        initial_reserve_deduction = sum(rec.line_total for rec in self.request_id.line_ids)
        balance = 0.0

        if not self.item_budget_id:
            raise ValidationError(_("No budget item selected"))

        for line in self.order_line:
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
                    bl.date_from) <= fields.Date.from_string(self.date_order) <= fields.Date.from_string(bl.date_to))
            if not budget_lines:
                raise ValidationError(_('No budget for this service: {} - {}').format(
                    line.product_id.name, self.item_budget_id.name))

            budget_line = budget_lines[0]
            initial_reserve = budget_lines[0].initial_reserve - initial_reserve_deduction
            budget_lines.write({'initial_reserve': abs(initial_reserve)})
            remain = abs(budget_line.available_liquidity)
            balance += line.price_subtotal
            new_remain = remain - balance

            confirmation_lines.append((0, 0, {
                'amount': line.price_subtotal,
                'item_budget_id': self.item_budget_id.id,
                'description': line.product_id.name,
                'budget_line_id': budget_line.id,
                # 'analytic_account_id': line.account_id.id,
                'remain': new_remain + line.price_subtotal,
                'new_balance': new_remain,
                'account_id': expense_account.id,
            }))

        rec = self.env['budget.confirmation'].sudo().create({
            'name': self.name,
            'date': self.date_order,
            'state': 'bdgt_dep_mngr',
            'beneficiary_id': self.partner_id.id,
            'department_id': self.department_id.id,
            'type': 'purchase.order',
            'ref': self.name,
            'description': self.purpose,
            'total_amount': total_amount,
            'lines_ids': confirmation_lines,
            'po_id': self.id,
        })
        self.write({'state': 'waiting'})

    def action_view_contract(self):
        formview_ref = self.env.ref('odex25_contract_saip.inherit_contract_contract_supplier_form_view', False)
        treeview_ref = self.env.ref('contract.contract_contract_tree_view', False)
        return {
            'name': _('Contract'),
            'domain': [('purchase_id', '=', self.id),('contract_type', '=', 'purchase')],
            'view_mode': 'tree,form',
            'res_model': 'contract.contract',
            'view_id': False,
            'views': [(treeview_ref and treeview_ref.id or False, 'tree'),
                      (formview_ref and formview_ref.id or False, 'form')],
            'type': 'ir.actions.act_window',
        }




class PurchaseRequest(models.Model):
    _inherit = 'purchase.order.line'

    item_budget_id = fields.Many2one(related='order_id.item_budget_id')

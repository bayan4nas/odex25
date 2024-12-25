from odoo import models,fields,api


class CrossoveredBudgetLines(models.Model):
    _inherit = "crossovered.budget.lines"

    purchase_remain = fields.Float(compute='_compute_operations_amount_new')

    @api.depends('from_operation_ids', 'to_operation_ids','general_budget_id')
    def _compute_operations_amount_new(self):
        for item in self:
            purchase_order_lines = item.env['purchase.order.line'].search([('order_id.state', '=', 'purchase'), ('order_id.budget_id', '=', item.crossovered_budget_id.id),
                                                                 ('account_analytic_id','=',item.analytic_account_id.id)])
            not_invoiced_lines = purchase_order_lines.filtered(lambda x: x.order_id.invoice_status != 'invoiced')
            not_invoiced_amount = sum(not_invoiced_lines.mapped('price_total'))
            item.reserve = not_invoiced_amount

            vendor_invoices = item.env['account.move.line'].search([('move_id.state', '=', 'posted'), ('move_id.move_type', '=', 'in_invoice'),
                                                               ('move_id.invoice_date_due', '>=', fields.Date.today()),

                                                               ('analytic_account_id', '=', item.analytic_account_id.id),
                                                                    '|', ('purchase_order_id.budget_id', '=', item.crossovered_budget_id.id),('move_id.purchase_id.budget_id', '=', item.crossovered_budget_id.id)])

            due_amount = sum(vendor_invoices.mapped('move_id').mapped('amount_residual'))
            item.purchase_remain = due_amount

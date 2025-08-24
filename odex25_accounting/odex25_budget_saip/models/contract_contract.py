# from pygments.lexer import default

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class CnotractContract(models.Model):
    _inherit = 'contract.contract'
    confirmation_ids = fields.One2many('budget.confirmation', 'contract_id')
    item_budget_id = fields.Many2one(related='request_id.item_budget_id')
    budget_checked = fields.Boolean(default=False)

    def cancel_state(self):
        super(CnotractContract, self).cancel_state()
        confirmation = self.env['budget.confirmation'].search([('contract_id', '=', self.id)])
        if confirmation:
            for rec in confirmation:
                rec.cancel()
                rec.sudo().unlink()
        self.write({"state": "cancel"})

    def open_confirmation(self):
        formview_ref = self.env.ref('account_budget_custom.view_budget_confirmation_form', False)
        treeview_ref = self.env.ref('account_budget_custom.view_budget_confirmation_tree', False)
        return {
            'name': _("Budget Confirmation"),
            'view_mode': 'tree, form',
            'view_id': False,
            'res_model': 'budget.confirmation',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': "[('id', 'in', %s)]" % self.confirmation_ids.ids,
            'views': [(treeview_ref and treeview_ref.id or False, 'tree'),
                      (formview_ref and formview_ref.id or False, 'form')],
            'context': {'create': False}
        }

    def action_show_invoices(self):
        super(CnotractContract, self).action_show_invoices()
        self.ensure_one()
        tree_view_ref = (
            "account.move_supplier_tree" if self.contract_type == "purchase" else "account.move_tree_with_onboarding")
        form_view_ref = (
            "odex25_account_saip.account_move_form_inherit" if self.contract_type == "purchase" else "account.move_form")
        tree_view = self.env.ref(tree_view_ref, raise_if_not_found=False)
        form_view = self.env.ref(form_view_ref, raise_if_not_found=False)
        action = {
            'name': _("Bill Invoices"),
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "view_mode": "tree,form",
            "domain": [("contract_id", "=", self.id), ('move_type', '=', 'in_invoice')],
            "context": {"default_contract_id": self.id, "create": False},
        }
        if tree_view and form_view:
            action["views"] = [(tree_view.id, "tree"), (form_view.id, "form")]
        return action

    def action_show_payment(self):
        super(CnotractContract, self).action_show_payment()
        self.ensure_one()
        payments = self._get_related_payment()
        formview_ref = self.env.ref('odex25_account_saip.view_account_payment_new_approve_form', False)
        treeview_ref = self.env.ref('account.view_account_payment_tree', False)

        # Return action for payments in tree view
        return {
            "name": "Payments",
            "type": "ir.actions.act_window",
            "res_model": "account.payment",
            'view_id': False,
            "view_mode": "tree,form",
            'views': [(treeview_ref and treeview_ref.id or False, 'tree'),
                      (formview_ref and formview_ref.id or False, 'form')],
            "domain": [("id", "in", payments.ids),('payment_type','=', 'outbound')],
            "context": {"default_contract_id": self.id, "create": False},
        }

    def get_budget_lines(self, line):
        budget_posts = self.env['account.budget.post'].search([]).filtered(
            lambda post: line.account_id in post.account_ids)
        budget_lines = line.item_budget_id.crossovered_budget_line.filtered(lambda budget_line: (
                budget_line.general_budget_id in budget_posts and budget_line.crossovered_budget_id.state == 'done' and budget_line.date_from <= self.date <= budget_line.date_to))
        return budget_lines

    def button_confirm(self):
        for line in self.order_line:
            budget_lines = self.get_budget_lines(line)
            budget_lines.write({'initial_reserve': abs(line.price_subtotal - budget_lines.initial_reserve)})

        return res

    def sent_to_budget_management(self):
        confirmation_lines = []
        balance = 0.0
        amount = sum(rec.price_subtotal for rec in self.contract_line_ids)
        initial_reserve_deduction = sum(rec.sum_total for rec in self.request_id.line_ids)
        initial_reserve_updated = False  # Flag to ensure initial reserve deduction is applied only once

        for rec in self.contract_line_ids:
            if not rec.item_budget_id:
                raise ValidationError(_("No budget item selected"))

            if not rec.product_id:
                raise ValidationError(_("There is no product"))

            expense_account = rec.product_id.property_account_expense_id or rec.product_id.categ_id.property_account_expense_categ_id
            if not expense_account:
                raise ValidationError(_("This product has no expense account") + ': {}'.format(rec.product_id.name))

            budget_lines = rec.item_budget_id.crossovered_budget_line.filtered(
                lambda x: x.general_budget_id in self.env['account.budget.post'].search([]).filtered(lambda
                                                                                                         x: expense_account in x.account_ids) and x.crossovered_budget_id.state == 'done' and fields.Date.from_string(
                    x.date_from) <= self.date <= fields.Date.from_string(x.date_to))

            if not budget_lines:
                raise ValidationError(
                    _('No budget for this service') + ': {} - {}'.format(rec.product_id.name, rec.item_budget_id.name))
            remain = abs(budget_lines[0].available_liquidity)
            balance += rec.price_subtotal

            # Apply initial reserve deduction only once
            if self.request_id.is_competition_divisible == 'no':
                if initial_reserve_deduction > 0 and not initial_reserve_updated:
                    initial_reserve = budget_lines[0].initial_reserve - initial_reserve_deduction
                    budget_lines.write({'initial_reserve': abs(initial_reserve)})
                    initial_reserve_updated = True
            else:
                if initial_reserve_deduction > 0 and not initial_reserve_updated:
                    contracts = self.env['contract.contract'].search_count([('request_id', '=', self.request_id.id),('budget_checked','=',False)])
                    if contracts == 1:
                        initial_reserve = budget_lines[0].initial_reserve - initial_reserve_deduction
                        budget_lines.write({'initial_reserve': abs(initial_reserve)})
                        initial_reserve_updated = True
            new_remain = remain - balance
            confirmation_lines.append((0, 0, {
                'amount': rec.price_subtotal,
                'item_budget_id': rec.item_budget_id.id,
                'analytic_account_id': rec.analytic_account_id.id,
                'description': rec.product_id.name,
                'budget_line_id': budget_lines[0].id,
                'remain': new_remain + rec.price_subtotal,
                'new_balance': new_remain,
                'account_id': expense_account.id,
            }))

        self.env['budget.confirmation'].sudo().create({
            'name': self.name_seq,
            'date': self.date,
            'state': 'bdgt_dep_mngr',
            'beneficiary_id': self.partner_id.id,
            'department_id': self.request_id.department_id.id,
            'type': 'contract.contract',
            'ref': self.name_seq,
            'description': self.name,
            'total_amount': amount,
            'lines_ids': confirmation_lines,
            'contract_id': self.id
        })

        self.write({'state': 'wait_budget','budget_checked':True})


class ContractLine(models.Model):
    _inherit = 'contract.line'

    item_budget_id = fields.Many2one(related='contract_id.item_budget_id')


class ContractInstallmentLine(models.Model):
    _inherit = 'line.contract.installment'

    item_budget_id = fields.Many2one(related='contract_id.item_budget_id')
    account_id = fields.Many2one(comodel_name='account.account', string='Account', default=lambda s: s._default_account())
    is_related_to_cotract = fields.Boolean(compute='_compute_is_related_to_cotract')

    @api.depends('contract_id')
    def _compute_is_related_to_cotract(self):
        for rec in self:
            if rec.contract_id and rec.item_budget_id:
                rec.is_related_to_cotract = True
            else:
                rec.is_related_to_cotract = False

    @api.model
    def _default_account(self):
        contract_id = self._context.get('default_contract_id')
        if contract_id:
            domain = [('contract_id', '=', contract_id)]
            contract_line = self.env['contract.line'].search(domain, limit=1)
            if contract_line:
                return contract_line.product_id.property_account_expense_id.id
        return False

    def change_state_to_invoiced(self):
        customer_invoice_lines = []
        fiscal_position = self.contract_id.fiscal_position_id
        analytic_account = self.analytic_account_id
        item_budget_id = self.item_budget_id
        tax = self.tax_id

        if self and self.coc_ids.filtered(
                lambda coc: coc.coc_stage == 'before_bill' and coc.state != 'approve' and coc.need_coc == 'yes'):
            raise ValidationError(_("Sorry You cannot Create Bill untill CoC Created and Approved."))

        if self.amount <= 0:
            raise ValidationError(_('You Cant Create Invoice With Amout Zero Or Less'))
        if not self.contract_id:
            raise ValidationError(_('you cant create invoice without contract'))

        # if conditions to create invoice lines base taxed_invoice field
        if self.taxed_invoice == 'with_invoice' or self.taxed_invoice == 'taxed_invoice':
            customer_invoice_lines = [(0, 0, {
                'name': self.name,
                'account_id': self.account_id.id,
                'analytic_account_id': analytic_account.id,
                'item_budget_id': item_budget_id.id,
                'quantity': 1.0,
                'price_unit': self.amount,
                'tax_ids': [(6, 0, tax.ids)],

            })]

        if self.taxed_invoice == 'final_invoice':
            # beging with add this inovice lines to create the invoice
            customer_invoice_lines.append(
                (0, 0, {
                    'name': self.name,
                    'account_id': self.account_id.id,
                    'analytic_account_id': analytic_account.id,
                    'item_budget_id': item_budget_id.id,
                    'quantity': 1.0,
                    'price_unit': self.amount,
                    'tax_ids': [(6, 0, tax.ids)],
                }))
            # then search for the related invoices to this contract,
            # combine the above invoice line with the below lines to create one invoce.
            contract_invoices = self.env['account.move'].search(
                [('contract_id', '=', self.contract_id.id)])
            # ('taxed_invoice', '=', 'without_invoice')
            for contract in contract_invoices:
                for inv in contract.invoice_line_ids:
                    customer_invoice_lines.append((0, 0, {
                        'name': inv.name,
                        'account_id': inv.account_id.id,
                        'quantity': -1,
                        'price_unit': inv.price_unit,
                        'discount': inv.discount,
                        'analytic_account_id': inv.analytic_account_id.id,
                        'item_budget_id': inv.item_budget_id.id,
                        'tax_ids': [(6, 0, inv.tax_ids.ids)] if inv.tax_ids else False,

                    }))

        # create payment if tax invoice = without an invoice, no invoice will be created
        if self.taxed_invoice == 'without_invoice':
            # prepare payment vals in case of tax_invoice ==without_invoice
            payment_vals = {
                'reconciled_invoice_ids': [],
                # for related invoice, to do :fix this to add inovice related to this payment
                'reconciled_bill_ids': [],
                'amount': self.total_amount,
                'is_related_to_cotract': self.is_related_to_cotract,
                'payment_method_id': self.env.ref('account.account_payment_method_manual_in').id,
                'partner_id': self.contract_id.partner_id.id,
                'payment_date': fields.Date.today(),
                'partner_type': 'customer',
                'payment_type': 'inbound',
                'currency_id': self.currency_id.id,
                'journal_id': self.journal_id.id,
                'contract_id': self.contract_id.id,

            }
            payment = self.env['account.payment'].create(payment_vals)
            move = self.env['account.move'].create({
                'name': '/',
                'journal_id': 3,
                'contract_id': self.contract_id.id,
                'installment_id': self.id,
                # 3 is the id of missilionous journal, to do:fix this if you want to make journal dynamic
                'date': payment.payment_date,
                'line_ids': [(0, 0, {
                    'payment_id': payment.id,
                    'partner_id': self.contract_id.partner_id.id,
                    'debit': self.total_amount,
                    'account_id': self.contract_id.partner_id.property_account_receivable_id.id,
                }), (0, 0, {
                    'payment_id': payment.id,
                    'partner_id': self.contract_id.partner_id.id,
                    'credit': self.total_amount,
                    'account_id': self.account_id.id,
                })]
            })
            move.post()
            self.write({'payment_id': payment.id if payment.id else payment.journal_id.id, 'state': 'paid'})

        # second, create the invoice wiht customer_invoice_lines list if the tax invoice != without an invoice
        else:
            # Staff for invoice
            invoice = self.env['account.move'].create({
                'partner_id': self.contract_id.partner_id.id,
                'journal_id': self.contract_id.journal_id.id,
                'payment_reference': self.contract_id.code or '',
                'fiscal_position_id': fiscal_position.id or False,
                'invoice_payment_term_id': self.contract_id.payment_term_id.id or False,
                'is_related_to_cotract': self.is_related_to_cotract,
                'invoice_line_ids': customer_invoice_lines,
                'date': self.due_date,
                'invoice_date': self.due_date,
                'move_type': 'out_invoice' if self.contract_type == 'sale' else 'in_invoice',
                'contract_id': self.contract_id.id,
                'installment_id': self.id,
                'narration': "%s - %s" % (self.contract_id.name, self.name),
            })
            self.write({'invoice_id': invoice.id, 'state': 'invoiced'})

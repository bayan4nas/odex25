from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountInvoiceLine(models.Model):
    _inherit = 'account.move.line'

    contract_id = fields.Many2one(related='move_id.contract_id')
    item_budget_id = fields.Many2one('item.budget', 'Budget Item')
    remaining_item_budget = fields.Float("Available Liquidity", compute="_compute_budget")
    remaining_available_liquidity = fields.Float("Remain Balance", compute="_compute_budget")

    # todo start
    @api.depends('price_subtotal','move_id.amount_total','remaining_item_budget')
    # todo end
    def _compute_budget(self):
        budget_tracking = {}  # Dictionary to track remaining available liquidity per item_budget_id

        for rec in self:
            x = rec.move_id.amount_total
            rec.remaining_item_budget = 0.00
            rec.remaining_available_liquidity = 0.00 

            if rec.item_budget_id:
                budget_id = rec.item_budget_id.id

                budget_lines = rec.item_budget_id.crossovered_budget_line.filtered(
                    lambda x: x.crossovered_budget_id.state == 'done'
                              and x.date_from and x.date_to
                              and fields.Date.from_string(x.date_from) <= rec.move_id.date <= fields.Date.from_string(
                        x.date_to)
                )
                if budget_lines:
                    # Set remaining_item_budget once based on the first budget line's available liquidity
                    rec.remaining_item_budget = abs(budget_lines[0].available_liquidity)

                    # Initialize tracking for the item_budget_id if not already tracked
                    if budget_id not in budget_tracking:
                        budget_tracking[
                            budget_id] = rec.remaining_item_budget  # Start with the full available liquidity

                    # Set the remaining available liquidity based on the cumulative tracked value minus the current amount
                    rec.remaining_available_liquidity = budget_tracking[budget_id] - rec.price_total

                    # Update the cumulative tracking budget after subtracting the current amount
                    budget_tracking[budget_id] -= rec.price_subtotal

    # todo start
    @api.onchange('price_unit')
    def _check_price_unit(self):
        for line in self:
            if line.price_unit<0:
                raise ValidationError("The price cannot be negative.")

    #
    # todo end


class AccountMove(models.Model):
    _inherit = 'account.move'
    is_related_to_cotract = fields.Boolean()
    hr_operation = fields.Boolean()

    def action_budget_management(self):
        if self.move_type == 'in_receipt':
            for line in self.invoice_line_ids:
                if not line.name or not line.account_id or line.quantity <= 0 or line.price_unit <= 0:
                    pass
                    # raise ValidationError(_("Empty or incomplete lines are not allowed. Please fill all required fields in the line items."))
            # todo start
            if len(self.invoice_line_ids)<1:
                raise ValidationError(_("Please Add Items in Invoice line Before send"))

            first_line = self.invoice_line_ids[0]
            if first_line.price_unit == 0.00:
                raise ValidationError(_("The first line in the invoice has a price of 0.00, please update it before sending to the budget"))

            if len(self.invoice_line_ids) > 1:
                all_zero = all(line.price_unit == 0.00 for line in self.invoice_line_ids)
                if all_zero:
                    raise ValidationError(_("All lines have a price of 0.00, please update them before sending to the budget"))
            # todo end
            self.state = 'budget_management'

    def action_post(self):
        super(AccountMove, self).action_post()
        for move in self:
            if move.move_type in ['in_invoice', 'in_receipt']:  # Vendor Bill
                if (move.invoice_date_due and move.invoice_date_due > fields.Date.today()) or \
                        (not move.invoice_date_due and move.invoice_date and move.invoice_date > fields.Date.today()):
                    raise ValidationError(_("The bill can be posted only on the due date or after it"))

                # Automatically create and post the payment
                payment_vals = {
                    'partner_id': move.partner_id.id,
                    'amount': move.amount_residual,
                    'payment_type': 'outbound',
                    'partner_type': 'supplier',
                    'payment_method_id': self.env.ref('account.account_payment_method_manual_out').id,
                    'journal_id': self.env['account.journal'].search([('type', '=', 'bank')], limit=1).id,
                    'date': fields.Date.today(),
                    'state': 'draft',
                    'ref': move.name,
                    "contract_id": move.contract_id.id,
                    'installment_id': move.installment_id.id,
                    'payment_reference': move.name,
                     'is_related_to_cotract': move.is_related_to_cotract if move.is_related_to_cotract else False,
                    'hr_operation': move.hr_operation,
                }

                # Add budget item details
                budget_item_vals = [(0, 0, {
                    'item_budget_id': item.item_budget_id.id,
                    'amount':  item.price_total,
                    'name': item.name,
                }) for item in move.invoice_line_ids]

                payment_vals['item_budget_ids'] = budget_item_vals
                payment = self.env['account.payment'].create(payment_vals)

    def action_register_payment(self):
        res = super(AccountMove, self).action_register_payment()
        res['context'].update({'default_hr_operation': self.hr_operation,'default_is_related_to_cotract': self.is_related_to_cotract})
        move_lines = self.line_ids.filtered(lambda line: line.item_budget_id)
        if move_lines:
            budget_items = []
            for line in move_lines:
                budget_items.append({'item_budget_id': line.item_budget_id.id, 'amount':line.price_total,
                                     'name': line.name})
            res['context'].update({'default_budget_item_ids': budget_items})
        return res


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    item_budget_ids = fields.One2many('account.payment.line', 'payment_id')
    is_related_to_cotract = fields.Boolean()
    hr_operation = fields.Boolean()

    @api.onchange('item_budget_ids')
    def _onchange_item_budget_ids(self):
        self.amount = sum(self.item_budget_ids.mapped('amount'))

    def action_senior_accountant(self):
        self.state = 'budget_management'

    @api.constrains('amount', 'item_budget_ids')
    def _check_amount_equals_lines(self):
        for rec in self:
            total_lines = sum(rec.item_budget_ids.mapped('amount'))
            if rec.amount != total_lines:
                raise ValidationError(_("The payment amount must be equal to the total of the payment lines."))


class AccountPayment(models.Model):
    _name = 'account.payment.line'

    payment_id = fields.Many2one('account.payment')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    amount = fields.Monetary(currency_field="currency_id")
    name = fields.Char()
    item_budget_id = fields.Many2one('item.budget', 'Budget Item')


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    item_budget_id = fields.Many2one('item.budget', 'Budget Item')
    budget_item_ids = fields.One2many('account.payment.budget.item', 'register_id', string='Budget Items')
    is_related_to_cotract = fields.Boolean()
    hr_operation = fields.Boolean()

    def _create_payment_vals_from_wizard(self):
        payment_vals = super(AccountPaymentRegister, self)._create_payment_vals_from_wizard()
        payment_vals['is_related_to_cotract'] = self.is_related_to_cotract
        payment_vals['hr_operation'] = self.hr_operation
        budget_item_vals = [(0, 0, {
            'item_budget_id': item.item_budget_id.id,
            'amount': item.amount,
            'name': item.name,
        }) for item in self.budget_item_ids]

        payment_vals['item_budget_ids'] = budget_item_vals
        return payment_vals


class AccountPaymentRegisterBudgetItem(models.TransientModel):
    _name = 'account.payment.budget.item'
    _description = 'Payment Register Budget Item'

    register_id = fields.Many2one('account.payment.register', string='Payment Register')
    item_budget_id = fields.Many2one('item.budget', string='Budget Item')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    amount = fields.Monetary(currency_field="currency_id")
    name = fields.Char()
    # currency_id = fields.Many2one('res.currency', related='register_id.currency_id', readonly=True)
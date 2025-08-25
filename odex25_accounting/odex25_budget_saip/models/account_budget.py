
from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError


class AccountBudgetPost(models.Model):
    _inherit = "account.budget.post"

    item_budget_ids = fields.Many2many('item.budget', 'account_budget_post_item_rel', 'item_id', 'post_id',
                                       string='Budget Items')

    @api.constrains('item_budget_ids')
    def _check_item_budget_ids(self):
        for rec in self:
            for item_budget in rec.item_budget_ids:
                overlapping_budget_posts = self.env['account.budget.post'].search(
                    [('id', '!=', rec.id), ('item_budget_ids', 'in', [item_budget.id])])
                if overlapping_budget_posts:
                    raise ValidationError(
                        _('The %s is included in the %s budget') % (item_budget.name, overlapping_budget_posts[0].name))


class CrossoveredBudget(models.Model):
    _inherit = "crossovered.budget"

    state = fields.Selection([
        ('draft', 'Prepare'),
        ('prepare', 'Review'),
        ('confirm', 'Authentication'),
        ('validate', 'Approve'),
        ('done', 'Approved'),
        ('cancel', 'Cancelled'),
    ], 'Status', default='draft', index=True, required=True, readonly=True, copy=False, tracking=True)

    def action_budget_prepare(self):
        self.write({'state': 'prepare'})

    @api.constrains('crossovered_budget_line', 'date_from', 'date_to')
    def _check_budget_line_period(self):
        for budget in self:
            if budget.state == 'done':
                continue
            for line in budget.crossovered_budget_line:
                overlapping_lines_count = self.env['crossovered.budget.lines'].search_count([
                    ('crossovered_budget_id.date_from', '<=', budget.date_to),
                    ('crossovered_budget_id.date_to', '>=', budget.date_from),
                    ('crossovered_budget_id.state', '=', 'done'),
                    ('id', '!=', line.id),
                    ('analytic_account_id', '=', line.item_budget_id.id),
                    ('general_budget_id', '=', line.general_budget_id.id),
                ])
                if overlapping_lines_count:
                    raise ValidationError(_('Budget lines cannot overlap with another.'))


class CrossoveredBudgetLines(models.Model):
    _inherit = "crossovered.budget.lines"
    _description = "Budget Line"

    item_budget_id = fields.Many2one('item.budget', 'Budget Item')
    operation_id = fields.Many2one('budget.operations', string='Operation', ondelete='cascade')
    item_type = fields.Selection(related='item_budget_id.item_type')
    period = fields.Selection(related='item_budget_id.period')
    opening_amount = fields.Monetary('Opening Amount', help="carried out from previous budget.")
    transferd_balance = fields.Monetary('Opening Amount', help="carried to new budgets.")
    additions = fields.Monetary('Additions')
    transfer_debit = fields.Monetary('Transfer Debit')
    transfer_credit = fields.Monetary('Transfer Credit')
    cost_amount = fields.Monetary('Cost Amount')
    added_amount = fields.Monetary('Added Amount')
    # cost_after_modification = fields.Monetary('Cost After Modification', compute='_compute_cost_after_modification')
    after_modification = fields.Monetary('After modification', compute='_compute_after_modification',
                                         help="Planned_amount+opening_amount+additions+transfer_debit-transfer_credit+cost amount")
    contract_count = fields.Integer('Contract Count', compute='_compute_contract_count',
                                    help="Total of related contrct")
    financial_reserve = fields.Monetary('Financial Reserves', compute='_compute_financial_reserve')
    available_liquidity = fields.Monetary('Available Liquidity', compute='_compute_available_liquidity')
    current_year_payment = fields.Monetary('Current year payments', compute='_compute_current_year_payment')
    previous_year_payment = fields.Float(string='Previous Year Payment', compute='_compute_previous_year_payment')
    current_year_payment_contract = fields.Monetary('Current year payments',
                                                    compute='_compute_current_year_payment_contract')
    currency_id = fields.Many2one('res.currency', string='Currency', required=True)
    contract_reserve = fields.Float(string='Contract Amount', compute='_compute_contract_reserve_amount')
    purchase_reserve = fields.Float(string='Purchase Reserve', compute='_compute_purchase_reserve_amount')
    is_transferd = fields.Boolean()

    def name_get(self):
        result = []
        for line in self:
            name = ''
            name += line.item_budget_id and line.item_budget_id.name or '' + ' '
            result.append((line.id, name))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        recs = self.search([('item_budget_id.name', operator, name)] + args, limit=limit)
        if not recs.ids:
            return super(CrossoveredBudgetLines, self).name_search(name=name, args=args, operator=operator, limit=limit)
        return recs.name_get()

    def _compute_percentage(self):
        for line in self:
            if line.after_modification != 0.00:
                line.percentage = (line.current_year_payment / line.after_modification) % 100
            else:
                line.percentage = 0.00

    @api.depends('item_budget_id')
    def _compute_contract_reserve_amount(self):
        for rec in self:
            contract_reserve_amount = self.env['budget.confirmation.line'].search([
                ('item_budget_id', '=', rec.item_budget_id.id),
                ('account_id', 'in', rec.general_budget_id.account_ids.ids),
                ('confirmation_id.date', '>=', rec.date_from),
                ('confirmation_id.date', '<=', rec.date_to),
                ('confirmation_id.type', '=', 'contract.contract'),
                ('confirmation_id.state', '=', 'done')
            ]).mapped('amount')
            rec.contract_reserve = sum(contract_reserve_amount) if contract_reserve_amount else 0.0

    @api.depends('item_budget_id')
    def _compute_purchase_reserve_amount(self):
        for rec in self:
            purchase_reserve_amount = self.env['budget.confirmation.line'].search([
                ('item_budget_id', '=', rec.item_budget_id.id),
                ('account_id', 'in', rec.general_budget_id.account_ids.ids),
                ('confirmation_id.date', '>=', rec.date_from),
                ('confirmation_id.date', '<=', rec.date_to),
                ('confirmation_id.type', '=', 'purchase.order'),
                ('confirmation_id.state', '=', 'done')
            ]).mapped('amount')
            rec.purchase_reserve = sum(purchase_reserve_amount) if purchase_reserve_amount else 0.0

    @api.depends('item_budget_id')
    def _compute_contract_count(self):
        for rec in self:
            rec.contract_count = 0.0
            contracts = self.env['budget.confirmation'].search(
                [('contract_id.item_budget_id', '=', rec.item_budget_id.id), ('state', '=', 'done'),
                 ('date', '>=', rec.date_from), ('date', '<=', rec.date_to)])
            rec.contract_count = len(contracts)

    @api.depends('item_budget_id')
    def _compute_financial_reserve(self):
        for rec in self:
            installment_amounts = self.env['line.contract.installment'].search([
                ('item_budget_id', '=', rec.item_budget_id.id), ('contract_id.state', '=', 'in_progress'),
                ('due_date', '>=', rec.date_from),
                ('due_date', '<=', rec.date_to)
            ]).mapped('amount')

            rec.financial_reserve = sum(
                installment_amounts) - rec.current_year_payment_contract if installment_amounts else 0.0

    @api.depends('planned_amount', 'opening_amount', 'additions', 'transfer_debit', 'transfer_credit')
    def _compute_after_modification(self):
        for line in self:
            line.after_modification = line.planned_amount + line.added_amount + line.opening_amount + line.additions + line.transfer_debit - abs(line.transfer_credit)

    # @api.depends('cost_amount', 'planned_amount')
    # def _compute_cost_after_modification(self):
    #     for line in self:
    #         if line.period == 'not_annually':
    #             line.cost_after_modification = line.cost_amount - line.planned_amount
    #         else:
    #             line.cost_after_modification = 0.00

    @api.depends('item_budget_id')
    def _compute_current_year_payment(self):
        for rec in self:
        #     payment_line_amount = self.env['account.payment.line'].search([
        #         ('item_budget_id', '=', rec.item_budget_id.id),
        #         ('payment_id.date', '>=', rec.date_from),
        #         ('payment_id.date', '<=', rec.date_to),
        #         ('payment_id.state', '=', 'posted')
        #     ]).mapped('amount')
        #     rec.current_year_payment = sum(payment_line_amount) if payment_line_amount else 0.0
            rec.current_year_payment = 0.0

    @api.depends('item_budget_id')
    def _compute_previous_year_payment(self):
        for rec in self:
            # if rec.date_from and rec.date_to:
            #     previous_year_date_from = rec.date_from - timedelta(days=365)
            #     previous_year_date_to = rec.date_to - timedelta(days=365)
            #     payment_line_amount = self.env['account.payment.line'].search([
            #         ('item_budget_id', '=', rec.item_budget_id.id),
            #         ('payment_id.date', '>=', previous_year_date_from),
            #         ('payment_id.date', '<=', previous_year_date_to),
            #         ('payment_id.state', '=', 'posted')
            #     ]).mapped('amount')
            #     rec.previous_year_payment = sum(payment_line_amount) if payment_line_amount else 0.0
            # else:
            rec.previous_year_payment = 0.0

    @api.depends('item_budget_id')
    def _compute_current_year_payment_contract(self):
        for rec in self:
            # payment_line_amount = self.env['account.payment.line'].search([
            #     ('item_budget_id', '=', rec.item_budget_id.id),
            #     ('payment_id.is_related_to_cotract', '=', True),
            #     ('payment_id.date', '>=', rec.date_from),
            #     ('payment_id.date', '<=', rec.date_to),
            #     ('payment_id.state', '=', 'posted')
            # ]).mapped('amount')
            # rec.current_year_payment_contract = sum(payment_line_amount) if payment_line_amount else 0.0
            rec.current_year_payment_contract = 0.0

    @api.depends('after_modification', 'current_year_payment')
    def _compute_available_liquidity(self):
        for line in self:
            line.available_liquidity = line.after_modification - line.current_year_payment - abs(line.transferd_balance)

    @api.depends('after_modification', 'practical_amount', 'contract_reserve', 'initial_reserve')
    def _compute_remaining_amount(self):
        for line in self:
            # non_contract_payment_amount = self.env['account.payment.line'].search([
            #     ('item_budget_id', '=', line.item_budget_id.id),
            #     ('payment_id.is_related_to_cotract', '=', False),
            #     ('payment_id.date', '>=', line.date_from),
            #     ('payment_id.date', '<=', line.date_to),
            #     ('payment_id.state', '=', 'posted')
            # ]).mapped('amount')
            # line.remain = line.after_modification - line.contract_reserve - line.purchase_reserve -  line.initial_reserve - sum(non_contract_payment_amount) - abs(line.transferd_balance)
            line.remain = line.after_modification - line.contract_reserve - line.purchase_reserve -  line.initial_reserve  - abs(line.transferd_balance)

    @api.constrains('item_budget_id')
    def _check_item_budget_id(self):
        for rec in self:
            existing_lines = self.env['crossovered.budget.lines'].search([
                ('item_budget_id', '=', rec.item_budget_id.id),
                ('date_from', '<=', rec.date_from),
                ('date_to', '>=', rec.date_to),
                ('id', '!=', rec.id)
            ])
            if existing_lines:
                raise UserError(_("This budget item account is already exit."))

    @api.onchange('general_budget_id', 'item_budget_id')
    def _onchange_general_budget_id(self):
        if self.general_budget_id:
            return {'domain': {'item_budget_id': [('id', 'in', self.general_budget_id.item_budget_ids.ids)]}}

    @api.model
    def default_get(self, fields_list):
        res = super(CrossoveredBudgetLines, self).default_get(fields_list)
        if 'general_budget_id' in res:
            general_budget = self.env['account.budget.post'].browse(res['general_budget_id'])
            res['domain'] = {'item_budget_id': [('id', 'in', general_budget.item_budget_ids.ids)]}
        return res


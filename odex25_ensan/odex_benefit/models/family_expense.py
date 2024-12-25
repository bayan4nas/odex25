# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ConfirmBenefitExpense(models.Model):
    _name = 'confirm.benefit.expense'
    _description = 'Confirm Benefit Expense'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    family_expense_seq = fields.Char(string="Family Expense Sequence", copy=False, readonly=True, default=lambda x: _('New'))
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('depart_manager', 'Department Manager'),
        ('account_manager', 'Account Manager'),
        ('cancel', 'Cancelled'),
        ('confirm', 'Confirmed'),
    ], string='Status', default='draft', required=True, copy=False,tracking=True)
    expense_type = fields.Selection(selection=[
        ('family_expense', 'Family Expense'),
        ('family_invoice', 'Meal Card Invoice'),
    ], string='Expense Type', default='family_expense', required=True, states={'confirm': [('readonly', True)]})
    journal_id = fields.Many2one(comodel_name='account.journal', string="Journal", required=True,copy=False)

    name = fields.Char(string="Name", states={'confirm': [('readonly', True)]}, copy=False)
    date = fields.Date(string="Date", default=fields.Date.context_today, required=True,
                       states={'confirm': [('readonly', True)]})

    family_ids = fields.Many2many(comodel_name='grant.benefit', relation='benefit_expense_grant_rel',
                                  column1='expense_id',
                                  column2='family_id', string='Families', states={'confirm': [('readonly', True)]},
                                  copy=False)
    cash_expense = fields.Boolean(string='Include Cash Expense', states={'confirm': [('readonly', True)]})
    meal_expense = fields.Boolean(string='Include Meal Expense', states={'confirm': [('readonly', True)]})
    cloth_expense = fields.Boolean(string='Include Clothing Expense', states={'confirm': [('readonly', True)]})

    # payment_method_id = fields.Many2one(comodel_name='account.payment.method.line', string='Payment Method',
    #                                     readonly=False, store=True, copy=False,
    #                                     states={'confirm': [('readonly', True)]},
    #                                     compute='_compute_payment_method_line_id',
    #                                     domain="[('id', 'in', available_payment_method_line_ids)]",
    #                                     help="Manual: Pay or Get paid by any method outside of Odoo.\n"
    #                                          "Payment Providers: Each payment provider has its own Payment Method. Request a transaction on/to a card thanks to a payment token saved by the partner when buying or subscribing online.\n"
    #                                          "Check: Pay bills by check and print it from Odoo.\n"
    #                                          "Batch Deposit: Collect several customer checks at once generating and submitting a batch deposit to your bank. Module account_batch_payment is necessary.\n"
    #                                          "SEPA Credit Transfer: Pay in the SEPA zone by submitting a SEPA Credit Transfer file to your bank. Module account_sepa is necessary.\n"
    #                                          "SEPA Direct Debit: Get paid in the SEPA zone thanks to a mandate your partner will have granted to you. Module account_sepa is necessary.\n")
    available_payment_method_line_ids = fields.Many2many(comodel_name='account.payment.method.line')
    total_moves = fields.Integer(string="Total Move Lines", compute='_get_total_move_lines')
    total_move_lines = fields.Integer(string="Total Move Lines", compute='_get_total_move_lines')
    total_invoices = fields.Integer(string="Total Moves", compute='_get_total_move_lines')

    family_monthly_income = fields.Float(string="Total Monthly Income", compute='_get_family_monthly_values')
    family_monthly_meals = fields.Float(string="Total Monthly Meals", compute='_get_family_monthly_values')
    family_monthly_clotting = fields.Float(string="Total Monthly Clotting", compute='_get_family_monthly_values')
    branch_custom_id = fields.Many2one(comodel_name='branch.settings', string="Branch")
    family_domain_ids = fields.Many2many(comodel_name='grant.benefit', compute='_compute_domain_ids')
    journal_domain_ids = fields.Many2many(comodel_name='account.journal', compute='_compute_domain_ids')

    @api.model
    def create(self, vals):
        res = super(ConfirmBenefitExpense, self).create(vals)
        if not res.family_ids:
            raise UserError(_('Select Family'))
        if not res.family_expense_seq or res.family_expense_seq == _('New'):
            res.family_expense_seq = self.env['ir.sequence'].sudo().next_by_code('family.expense.sequence') or _('New')
        return res

    # @api.onchange('branch_custom_id')  # Specify dependencies
    # def _onchange_family_ids(self):
    #     for record in self:
    #         if record.branch_custom_id :
    #             # Logic to determine the family_ids based on branch_custom_id
    #             related_records = self.env['grant.benefit'].search([('branch_custom_id', '=', record.branch_custom_id.id),('state','=','second_approve')])
    #             if related_records:
    #                 record.family_ids = [(6, 0, related_records.ids)]  # 6 means 'set' in Many2many
    #             else:
    #                 record.family_ids = [(5,)]  # Clear the records if source_field is empty
    #                 raise UserError(_('Select Family'))
    #         else:
    #             record.family_ids = [(5,)]  # Clear the records if source_field is empty

    @api.depends('expense_type', 'date', 'branch_custom_id')
    def _compute_domain_ids(self):
        for rec in self:
            journal_domain = []
            if rec.expense_type == 'family_expense':
                journal_domain = [('type', 'in', ['bank', 'cash'])]
            elif rec.expense_type == 'family_invoice':
                journal_domain = [('type', 'in', ['purchase'])]

            # Define base domain for family selection
            validation_setting = self.env["family.validation.setting"].search([], limit=1)

            # base_domain = [('state', 'in', ('second_approve', 'temporarily_suspend', 'suspend'))]
            base_domain = [('state', 'in', ('second_approve', 'temporarily_suspended', 'suspended_first_approve'))]
            if rec.branch_custom_id:
                base_domain.append(('branch_custom_id', '=', rec.branch_custom_id.id))
            min_income = validation_setting.benefit_category_ids.mapped('mini_income_amount')
            max_income = validation_setting.benefit_category_ids.mapped('max_income_amount')
            base_domain.extend([('member_income', '>=', min(min_income)), ('member_income', '<=', max(max_income))])
            base_domain.extend([('benefit_category_id', '!=', False)])
            if rec.expense_type == 'family_invoice':
                base_domain.append(('meal_card', '=', True))

            if rec.date:
                # Calculate the start date for the past month range
                month_ago = rec.date - relativedelta(months=1)

                # Search for conflicting records of the same expense type within the past month
                conflicting_records = self.search([
                    ('date', '>=', month_ago),
                    ('date', '<=', rec.date),
                    ('expense_type', '=', rec.expense_type),
                ])

                if conflicting_records:
                    # Gather the family IDs that are already associated with the same expense type
                    conflicting_family_ids = conflicting_records.mapped('family_ids').ids
                    base_domain.append(('id', 'not in', conflicting_family_ids))

            rec.family_domain_ids = self.env['grant.benefit'].search(base_domain)
            # related_records = self.family_ids = self.env['grant.benefit'].search(base_domain)
            # if related_records:
            #     self.family_ids = [(6, 0, related_records.ids)]  # 6 means 'set' in Many2many
            # else:
            #     self.family_ids = [(5,)]  # Clear the records if source_field is empty
            # rec.family_ids = self.env['grant.benefit'].search(base_domain).ids
            rec.journal_domain_ids = self.env['account.journal'].search(journal_domain)

    # def unlink(self):
    #     for rec in self:
    #         if rec.state not in ['draft']:
    #             raise UserError(_('This record can only be deleted in draft state.'))
    #     return super(ConfirmBenefitExpense, self).unlink()

    @api.depends('family_ids', 'expense_type')
    def _get_family_monthly_values(self):
        for rec in self:
            rec.family_monthly_income = sum(rec.family_ids.mapped('family_monthly_income'))
            rec.family_monthly_meals = sum(rec.family_ids.filtered(lambda record: not record.meal_card).mapped(
                'family_monthly_meals')) if rec.expense_type == 'family_expense' else sum(
                rec.family_ids.mapped('family_monthly_meals'))
            rec.family_monthly_clotting = sum(rec.family_ids.mapped('family_monthly_clotting'))

    @api.onchange('expense_type')
    def _onchange_journal_id(self):
        if self.expense_type == 'family_expense':
            self.journal_id = self.env["family.validation.setting"].search([], limit=1).journal_id.id
        else:
            self.journal_id = False

    def action_depart_manager(self):
        self.state = 'depart_manager'

    def action_accounting_manager(self):
        self.state = 'account_manager'

    def action_cancel(self):
        self.state = 'cancel'

    def action_reset_to_draft(self):
        self.state = 'draft'

    @api.constrains('expense_type', 'cash_expense', 'meal_expense', 'cloth_expense')
    def _constraint_check_at_least_one_expense(self):
        for rec in self:
            if rec.expense_type == 'family_expense':
                if not rec.cash_expense and not rec.meal_expense and not rec.cloth_expense:
                    raise UserError(_("At least one expense type should be selected."))

    def _get_total_move_lines(self):
        for rec in self:
            rec.total_moves = self.env['account.move'].search_count([
                ('family_confirm_id', '=', rec.id), ('move_type', '!=', 'in_invoice')
            ])
            rec.total_invoices = self.env['account.move'].search_count([
                ('family_confirm_id', '=', rec.id), ('move_type', '=', 'in_invoice')
            ])
            rec.total_move_lines = len(self.env['account.move'].search([
                ('family_confirm_id', '=', rec.id), ('move_type', '!=', 'in_invoice')
            ]).mapped('line_ids').ids)

    def action_open_related_move_records(self):
        """ Opens a tree view with related records filtered by a dynamic domain """
        moves = self.env['account.move'].search([
            ('family_confirm_id', '=', self.id), ('move_type', '!=', 'in_invoice')
        ]).ids

        return {
            'name': _('Moves'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', moves)],
        }

    def action_open_related_move_line_records(self):
        """ Opens a tree view with related records filtered by a dynamic domain """
        move_lines = self.env['account.move'].search([
            ('family_confirm_id', '=', self.id), ('move_type', '!=', 'in_invoice')
        ]).mapped('line_ids').ids

        return {
            'name': _('Moves'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.line',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', move_lines)],
        }

    def action_open_related_invoice_records(self):
        """ Opens a tree view with related records filtered by a dynamic domain """
        invoices = self.env['account.move'].search([
            ('family_confirm_id', '=', self.id), ('move_type', '=', 'in_invoice')
        ]).ids

        return {
            'name': _('Vendor Bills'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', invoices)],
        }

    # @api.depends('available_payment_method_line_ids')
    # def _compute_payment_method_line_id(self):
    #     ''' Compute the 'payment_method_line_id' field.
    #     This field is not computed in '_compute_payment_method_line_fields' because it's a stored editable one.
    #     '''
    #     for pay in self:
    #         available_payment_method_lines = pay.available_payment_method_line_ids
    #
    #         # Select the first available one by default.
    #         if pay.payment_method_id in available_payment_method_lines:
    #             pay.payment_method_id = pay.payment_method_id
    #         elif available_payment_method_lines:
    #             pay.payment_method_id = available_payment_method_lines[0]._origin
    #         else:
    #             pay.payment_method_id = False

    # @api.depends('journal_id')
    # def _compute_payment_method_line_fields(self):
    #     for pay in self:
    #         pay.available_payment_method_line_ids = pay.journal_id._get_available_payment_method_lines('outbound')

    @api.onchange('expense_type', 'date', 'branch_custom_id')
    def _onchange_expense_type(self):
        """Restrict families to a single expense type per month."""
        journal_domain = []

        # Define journal domains based on expense type
        if self.expense_type == 'family_expense':
            journal_domain = [('type', 'in', ['bank', 'cash'])]
        elif self.expense_type == 'family_invoice':
            journal_domain = [('type', 'in', ['purchase'])]

        # Define base domain for family selection
        validation_setting = self.env["family.validation.setting"].search([], limit=1)

        base_domain = [('state', 'in', ('second_approve', 'temporarily_suspended', 'suspended_first_approve'))]
        if self.branch_custom_id:
            base_domain.append(('branch_custom_id', '=', self.branch_custom_id.id))
        min_income = validation_setting.benefit_category_ids.mapped('mini_income_amount')
        max_income = validation_setting.benefit_category_ids.mapped('max_income_amount')
        base_domain.extend([('member_income', '>=', min(min_income)), ('member_income', '<=', max(max_income))])
        base_domain.extend([('benefit_category_id', '!=', False)])
        if self.expense_type == 'family_invoice':
            base_domain.append(('meal_card', '=', True))

        if self.date:
            # Calculate the start date for the past month range
            month_ago = self.date - relativedelta(months=1)

            # Search for conflicting records of the same expense type within the past month
            conflicting_records = self.search([
                ('date', '>=', month_ago),
                ('date', '<=', self.date),
                ('expense_type', '=', self.expense_type),
            ])

            if conflicting_records:
                # Gather the family IDs that are already associated with the same expense type
                conflicting_family_ids = conflicting_records.mapped('family_ids').ids
                base_domain.append(('id', 'not in', conflicting_family_ids))
        related_records = self.family_ids = self.env['grant.benefit'].search(base_domain)
        if related_records and self.branch_custom_id:
            self.family_ids = [(6, 0, related_records.ids)]  # 6 means 'set' in Many2many
        else:
            self.family_ids = [(5,)]  # Clear the records if source_field is empty
        # self.family_ids = self.env['grant.benefit'].search(base_domain).ids


        # Return domain restrictions
        return {
            'domain': {
                'family_ids': base_domain,
                'journal_id': journal_domain,
            }
        }

    def action_confirm_selected(self):
        for rec in self:
            if rec.expense_type == 'family_expense':
                benefits = rec.family_ids
                if any(benefit.state not in ('second_approve', 'temporarily_suspended', 'suspended_first_approve') for benefit in
                       benefits):
                    raise UserError(_("All selected benefits should be either state of "
                                      "'second_approve','temporarily_suspended','suspended_first_approve' state."))

                validation_setting = self.env["family.validation.setting"].search([], limit=1)

                # payment_method_line = rec.payment_method_id

                if not validation_setting.cash_expense_account_id or not validation_setting.meal_expense_account_id or not validation_setting.clothing_expense_account_id:
                    raise UserError(_("Please configure the expense accounts in the validation settings."))
                # if not payment_method_line:
                #     raise UserError(_("Payment method is not configured for the selected journal."))

                # credit_account_id = payment_method_line.payment_account_id.id
                credit_account_id = self.env["family.validation.setting"].search([], limit=1).account_id.id


                if not credit_account_id:
                    raise UserError(_("Please select credit account."))

                if benefits:
                    lines = []
                    total_credit = 0
                    credit_line_name = _("Total Credit for Family Expenses")
                    for benefit in benefits:
                        sum_line, credit_total = rec._prepare_entry_lines(benefit, validation_setting,
                                                                          credit_account_id)
                        total_credit += credit_total
                        lines += sum_line
                    lines.append(self._create_credit_line(credit_account_id, total_credit, credit_line_name))

                    rec.create_entry(rec.journal_id.id, lines)
            else:
                if not rec.family_ids:
                    raise UserError(_("Please select at least one family to create an invoice."))
                validation_setting = self.env["family.validation.setting"].search([], limit=1)
                account_id = validation_setting.meal_expense_account_id
                invoice_lines = []
                for family in rec.family_ids:
                    invoice_lines.append((0, 0, {
                        'name': f'{family.name}/{family.code}',  # Family name as the description
                        'account_id': account_id.id,  # The same account for all lines
                        'quantity': 1,  # Qty is 1
                        # The same analytic account
                        'benefit_family_id': family.id,
                        'price_unit': family.benefit_member_count * validation_setting.meal_expense,
                        'analytic_account_id': family.branch_custom_id.branch.analytic_account_id.id
                    }))

                    # Create the invoice
                invoice_vals = {
                    'move_type': 'in_invoice',  # Set this to 'in_invoice' if it's a vendor bill
                    'partner_id': validation_setting.meal_partner_id.id,  # The partner for the invoice
                    'invoice_date': rec.date,  # The date of the invoice
                    'family_confirm_id': rec.id,  # Link to the family expense record
                    'benefit_family_ids': [(6, 0, rec.family_ids.ids)],  # Link to the families
                    'journal_id': rec.journal_id.id,  # The journal for the invoice
                    'invoice_line_ids': invoice_lines,  # The invoice lines
                    'ref': rec.name,  # The reference for the invoice
                }

                invoice = self.env['account.move'].create(invoice_vals)
                invoice.action_confirm()
            rec.state = 'confirm'

        return True

    def _prepare_entry_lines(self, benefit, validation_setting, credit_account_id):
        """Prepare debit and credit lines for a benefit"""
        entry_lines = []
        total_credit_amount = 0  # To accumulate the total credit amount

        expense_types = [
            ('meal', 'meal_expense', validation_setting.meal_expense_account_id.id),
            ('cash', 'cash_expense', validation_setting.cash_expense_account_id.id),
            ('clothing', 'clothing_expense', validation_setting.clothing_expense_account_id.id),
        ]

        for expense_type, field, debit_account_id in expense_types:
            amount = benefit.benefit_member_count * getattr(validation_setting, field, 0.0)

            # Skip conditions based on expense type
            if (benefit.district_id.meal_card and expense_type == 'meal') or (
                    not self.meal_expense and expense_type == 'meal'):
                continue
            if not self.cash_expense and expense_type == 'cash':
                continue
            if not self.cloth_expense and expense_type == 'clothing':
                continue

            # If there's an amount, create a debit line and accumulate the credit amount
            if amount:
                name = _("Family Code - %s Family Expense - %s - %s/%s") % (benefit.code ,expense_type, self.name,self.family_expense_seq)
                entry_lines.append(self._create_debit_line(benefit, debit_account_id, amount, name))
                total_credit_amount += amount

        return entry_lines, total_credit_amount

    def _create_debit_line(self, benefit, account_id, amount, name):
        """Create a debit line"""
        return (0, 0, {
            'name': name,
            'family_confirm_id': self.id,
            'benefit_family_id': benefit.id,
            'partner_id': benefit.partner_id.id,
            'analytic_account_id': benefit.branch_custom_id.branch.analytic_account_id.id,
            'account_id': account_id,
            'debit': amount,
            'credit': 0.0,
        })

    def _create_credit_line(self, account_id, amount, name):
        """Create a credit line"""
        return (0, 0, {
            'name': name,
            'family_confirm_id': self.id,
            'account_id': account_id,
            'debit': 0.0,
            'credit': amount,
        })

    def create_entry(self, journal_id, lines):
        """Create an account move entry"""
        move_vals = {
            'journal_id': journal_id,
            'date': self.date,
            # 'ref': self.name,
            'ref': f'{self.name}/{self.family_expense_seq}',
            'family_confirm_id': self.id,
            'benefit_family_ids': [(6, 0, self.family_ids.ids)],
            'line_ids': lines,
        }
        move_id = self.env['account.move'].create(move_vals)
        move_id.action_post()
        return True

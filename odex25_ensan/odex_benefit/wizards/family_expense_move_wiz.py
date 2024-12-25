from datetime import date

from odoo import models, fields, _
from odoo.exceptions import UserError


class ConfirmBenefitWizard(models.TransientModel):
    _name = 'confirm.benefit.wizard'
    _description = 'Confirm Benefit Wizard'

    journal_id = fields.Many2one(comodel_name='account.journal', string="Journal", required=True)
    payment_method_id = fields.Many2one(comodel_name='account.payment.method', string='Payment Type', required=True)

    name = fields.Char(string="Name", default=lambda self: "Family Expense -%s" % date.today())
    date = fields.Date(string="Date", default=fields.Date.context_today, required=True)

    def action_confirm_selected(self):
        active_ids = self.env.context.get('default_benefit_ids', [])
        benefits = self.env['grant.benefit'].browse(active_ids)

        if any(benefit.state not in ('second_approve', 'temporarily_suspend', 'suspend') for benefit in benefits):
            raise UserError(_("All selected benefits should be either state of "
                              "'second_approve','temporarily_suspend','suspend' state."))

        validation_setting = self.env["family.validation.setting"].search([], limit=1)

        payment_method_line = self.env['account.payment.method.line'].search(
            [('payment_method_id', '=', self.payment_method_id.id)], limit=1)

        if not validation_setting.cash_expense_account_id or not validation_setting.meal_expense_account_id or not validation_setting.clothing_expense_account_id:
            raise UserError(_("Please configure the expense accounts in the validation settings."))
        if not payment_method_line:
            raise UserError(_("Payment method is not configured for the selected journal."))

        credit_account_id = payment_method_line.payment_account_id.id

        if not credit_account_id:
            raise UserError(_("Payment method is not configured for the selected journal."))

        if benefits:
            lines = []
            for benefit in benefits:
                lines += self._prepare_entry_lines(benefit, validation_setting, credit_account_id)

            self.create_entry(self.journal_id.id, lines)
        return {'type': 'ir.actions.act_window_close'}

    def _prepare_entry_lines(self, benefit, validation_setting, credit_account_id):
        """Prepare debit and credit lines for a benefit"""
        entry_lines = []

        expense_types = [
            ('meal', 'family_monthly_meals', validation_setting.meal_expense_account_id.id),
            ('cash', 'family_monthly_income', validation_setting.cash_expense_account_id.id),
            ('clothing', 'family_monthly_clotting', validation_setting.clothing_expense_account_id.id),
        ]

        for expense_type, field, debit_account_id in expense_types:
            amount = getattr(benefit, field, 0.0)
            if benefit.district_id.meal_card and expense_type == 'meal':
                continue
            if amount:
                name = _("Family Expense - %s") % expense_type
                entry_lines.append(self._create_debit_line(benefit, debit_account_id, amount, name))
                entry_lines.append(self._create_credit_line(benefit, credit_account_id, amount, name))

        return entry_lines

    def _create_debit_line(self, benefit, account_id, amount, name):
        """Create a debit line"""
        return (0, 0, {
            'name': name,
            'benefit_family_id': benefit.id,
            'partner_id': benefit.partner_id.id,
            'analytic_account_id': benefit.branch_custom_id.analytic_account_id.id,
            'account_id': account_id,
            'debit': amount,
            'credit': 0.0,
        })

    def _create_credit_line(self, benefit, account_id, amount, name):
        """Create a credit line"""
        return (0, 0, {
            'name': name,
            'benefit_family_id': benefit.id,
            'partner_id': benefit.partner_id.id,
            'analytic_account_id': benefit.branch_custom_id.analytic_account_id.id,
            'account_id': account_id,
            'debit': 0.0,
            'credit': amount,
        })

    def create_entry(self, journal_id, lines):
        """Create an account move entry"""
        move_vals = {
            'journal_id': journal_id,
            'date': self.date,
            'ref': self.name,
            'line_ids': lines,
        }
        self.env['account.move'].create(move_vals)
        return True

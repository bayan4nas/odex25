from odoo import api, fields, models, _
from odoo.tools import ustr
from odoo.exceptions import UserError, ValidationError
from collections import defaultdict


class CrossoveredBudget(models.Model):
    _inherit = "crossovered.budget"
    _order = "create_date desc"

    amount = fields.Monetary(string='Total Amount')
    reserved_percent = fields.Float(string='Reserved Percent')
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, required=True,
                                  default=lambda self: self.env.user.company_id.currency_id.id)

    def unlink(self):
        for budget in self:
            if budget.state not in 'draft':
                raise UserError(_('You can not delete budget not in draft state'))
        return super(CrossoveredBudget, self).unlink()

    state = fields.Selection([
        ('draft', 'Draft'),
        ('cancel', 'Cancelled'),
        ('confirm', 'Waiting Validation'),
        ('validate', 'Waiting Approval'),
        ('done', 'Approved')
    ], 'Status', default='draft', index=True, required=True, readonly=True, copy=False,tracking=True)


class CrossoveredBudgetLines(models.Model):
    _inherit = "crossovered.budget.lines"

    reserved_percent = fields.Float(related='crossovered_budget_id.reserved_percent', string='Reserved Percent')
    reserved_amount = fields.Float(string='Reserved Amount', readonly=True, compute='_compute_reserved_amount')
    pull_out = fields.Float(string='Pull Out',compute_sudo=True)
    provide = fields.Float(string='Provide',compute_sudo=True)
    remain = fields.Float(string='Remaining of Reliance', compute='_compute_remaining_amount',compute_sudo=True)
    budget_confirm_amount = fields.Float(string='confirmation amount',compute_sudo=True)
    # purchase_remain = fields.Float(store=True, compute='_compute_operations_amount', tracking=True ,compute_sudo=True)
    practical_amount = fields.Float(compute='_compute_practical_amount', string='Practical Amount', digits=0,
                                    store=False)
    theoritical_amount = fields.Float(compute='_compute_theoritical_amount', string='Theoretical Amount', digits=0,
                                      store=True)
    percentage = fields.Float(compute='_compute_percentage', string='Achievement')
    from_operation_ids = fields.One2many('budget.operations', 'from_budget_line_id', string='From Operation')
    to_operation_ids = fields.One2many('budget.operations', 'to_budget_line_id', string='Cost Center')
    budget_confirm_line_ids = fields.One2many('budget.confirmation.line', 'budget_line_id', 'Confirmation')
    reserve = fields.Float(string='Reserve Amount')
    initial_reserve = fields.Float(string='Initial Reserve')
    contract_reserve = fields.Float(string='Contract Amount')
    confirm = fields.Float(string='Confirm Amount')
    year_end = fields.Boolean(compute="get_year_end")

    def _compute_remaining_amount(self):
        for line in self:
            line.remain = line.planned_amount - line.practical_amount - line.contract_reserve - line.initial_reserve

    def _compute_reserved_amount(self):
        for line in self:
            reserved_amount = line.crossovered_budget_id.reserved_percent * \
                              line.planned_amount / 100.0
            reserved_amount -= line.with_context({'reserved': True}).pull_out
            line.reserved_amount = reserved_amount

    @api.depends('from_operation_ids', 'to_operation_ids')
    def _compute_operations_amount(self):
        if not self.ids: return
        for line in self:
            pull_out = provide = budget_confirm_amount = 0.0
            date_to = line.date_to
            date_from = line.date_from
            if line.analytic_account_id.id and date_to and date_from:
                if 'reserved' not in self.env.context:
                    self.env.cr.execute("""
                        SELECT SUM(amount)
                        FROM budget_operations
                        WHERE from_budget_line_id=%s
                            AND (date between %s AND %s)
                            AND state='confirmed'""", (line._origin.id, date_from, date_to,))
                    pull_out = self.env.cr.fetchone()[0] or 0.0

                if 'reserved' in self.env.context:
                    self.env.cr.execute("""
                        SELECT SUM(amount)
                        FROM budget_operations
                        WHERE from_budget_line_id=%s
                            AND (date between %s AND %s)
                            AND state='confirmed' 
                            AND from_reserved=%s""",
                                        (line._origin.id, date_from, date_to, self.env.context['reserved']))
                    pull_out = self.env.cr.fetchone()[0] or 0.0

                self.env.cr.execute("""
                    SELECT SUM(amount)
                    FROM budget_operations
                    WHERE to_budget_line_id=%s
                        AND (date between %s AND %s)
                        AND state='confirmed'""", (line._origin.id, date_from, date_to,))
                provide = self.env.cr.fetchone()[0] or 0.0

                self.env.cr.execute("""
                    SELECT SUM(amount)
                    FROM budget_confirmation_line
                    WHERE budget_line_id=%s
                        AND (date between %s AND %s)
                        AND state='done'""", (line._origin.id, date_from, date_to,))
                budget_confirm_amount = self.env.cr.fetchone()[0] or 0.0

            line.pull_out = pull_out
            line.provide = provide
            line.budget_confirm_amount = budget_confirm_amount
            # line.remain = line.planned_amount + provide - pull_out - line.practical_amount - line.reserved_amount - line.contract_reserve - line.initial_reserve
            # line.purchase_remain = abs(line.reserve + line.initial_reserve + line.practical_amount) - abs(line.practical_amount)

    @api.depends('date_from', 'date_to', 'general_budget_id', 'analytic_account_id')
    def _compute_practical_amount(self):
        for line in self:
            line.practical_amount = 0.0  # Default value
            if not line.date_from or not line.date_to:
                continue
            acc_ids = line.general_budget_id.account_ids.ids
            if not acc_ids:
                continue
            analytic_ids = self.env['account.analytic.account'].search(
                ['|', ('id', '=', line.analytic_account_id.id),
                 ('parent_id', 'child_of', line.analytic_account_id.id)])
            if not analytic_ids:
                continue
            self.env.cr.execute("""
                    SELECT SUM(amount)
                    FROM account_analytic_line
                    WHERE account_id IN %s
                      AND date BETWEEN %s AND %s
                      AND general_account_id = ANY(%s)
                """, (tuple(analytic_ids.ids), line.date_from, line.date_to, acc_ids))

            result = self.env.cr.fetchone()[0] or 0.0
            line.practical_amount = result

    def get_year_end(self):
        for rec in self:
            date = fields.Date.today()
            rec.year_end = False
            if rec.crossovered_budget_id.date_to:
                if rec.crossovered_budget_id.date_to <= date:
                    rec.year_end = True

    def transfer_budget_action(self):
        formview_ref = self.env.ref('account_budget_custom.view_budget_operations', False)
        return {
            'name': _("Budget Transfer"),
            'view_mode': 'form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'budget.operations',
            'type': 'ir.actions.act_window',
            'target': 'new',
            'views': [(formview_ref and formview_ref.id or False, 'form')],
            'context': {
                'default_operation_type': 'transfer',
                'default_from_budget_post_id': self.general_budget_id.id,
                'default_from_crossovered_budget_id': self.crossovered_budget_id.id,
                'default_from_budget_line_id': self.id,
                'default_amount': self.remain,
                'default_date': fields.Date.today(),
            }
        }

    # @api.depends('analytic_account_id', 'planned_amount', 'practical_amount')
    # def name_get(self):
    #     result = []
    #     for line in self:
    #         name = ''
    #         name += line.analytic_account_id and line.analytic_account_id.name or '' + ' ' + _('remaining') + ' '
    #         if self.env.context.get('reserved', False):
    #             name += str(line.reserved_amount)
    #         if not self.env.context.get('reserved', False):
    #             name += str(line.remain)
    #         result.append((line.id, name))
    #     return result

    def _check_amount(self):
        for obj in self:
            # get the original reserved amount
            reserved_amount = obj.crossovered_budget_id.reserved_percent * obj.planned_amount / 100.0
            if obj.with_context({'reserved': True}).pull_out > reserved_amount:
                raise ValidationError(_('''You can not take more than the reserved amount.'''))
            if obj.remain < 0:
                raise ValidationError(_('''You can not take more than the remaining amount'''))

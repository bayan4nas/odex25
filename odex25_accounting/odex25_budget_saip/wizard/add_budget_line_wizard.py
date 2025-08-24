from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class BudgetLineWizard(models.TransientModel):
    _name = 'budget.line.wizard'
    _description = 'Wizard to Add Budget Line'

    general_budget_id = fields.Many2one('account.budget.post', string='General Budget')
    item_budget_id = fields.Many2one('item.budget', 'Budget Item')
    period = fields.Selection(related='item_budget_id.period')
    added_amount = fields.Float(string='Added Amount')
    cost_amount = fields.Float(string='Cost Amount')

    @api.onchange('general_budget_id', 'item_budget_id')
    def _onchange_general_budget_id(self):
        if self.general_budget_id:
            return {'domain': {'item_budget_id': [('id', 'in', self.general_budget_id.item_budget_ids.ids)]}}

    @api.onchange('item_budget_id')
    def _onchange_item_budget_id(self):
        self.added_amount = 0.00
        self.cost_amount = 0.00

    def add_budget_line(self):
        active_id = self.env.context.get('active_id')


        if self.period != 'annually':
            if self.cost_amount <= 0:
                # todo start
                pass
                # raise ValidationError(_('Cost Amount must be greater than zero.'))
        #     todoend
        else:
            if self.added_amount <= 0:
                # todo start
                pass
                # raise ValidationError(_('Planned Amount must be greater than zero.'))
        # todo end
        if active_id:
            budget = self.env['crossovered.budget'].browse(active_id)
            if budget.fiscalyear_id.state == 'closed':
                raise ValidationError(
                    _("This procedure cannot be done due to the closure of the fiscal year for this budget"))
            self.env['crossovered.budget.lines'].create({
                'crossovered_budget_id': budget.id,
                'general_budget_id': self.general_budget_id.id,
                'item_budget_id': self.item_budget_id.id,
                'added_amount': 0.00,
                'cost_amount': self.cost_amount,
                'planned_amount':self.added_amount ,
            })

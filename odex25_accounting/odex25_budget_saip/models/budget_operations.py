from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare
import math

class BudgetOperations(models.Model):
    _inherit = 'budget.operations'
    _order = 'id desc'

    purpose = fields.Char(string='Transfer Purpose', tracking=True)
    budget_id = fields.Many2one('crossovered.budget', string='Budget', tracking=True)
    from_budget_line_id = fields.Many2one('crossovered.budget.lines', string='Budget Item', tracking=True)
    transfer_from_budget_id = fields.Many2one('crossovered.budget', string='Transfer From Budget')
    transfer_to_budget_id = fields.Many2one('crossovered.budget', string='Transfer To Budget', tracking=True)
    company_id = fields.Many2one(related='budget_id.company_id', readonly=True)
    currency_id = fields.Many2one(related='company_id.currency_id', readonly=True)
    general_budget_id = fields.Many2one('account.budget.post', 'Budgetary Position', tracking=True)
    line_ids = fields.One2many('budget.operations.line', 'operation_id', string='Details', tracking=True)
    total_percentage = fields.Float(string="Total Percentage", compute="_compute_total_percentage")
    transfer = fields.Boolean(compute="_compute_transfer")
    between_position = fields.Boolean()
    budget_support = fields.Boolean()
    transfer_type = fields.Selection(selection=[('between_position', 'Between Position'), ('same_position', 'Same Position')], string='Transfer Type', tracking=True)
    state = fields.Selection(selection=[('draft', 'Budget Management'), ('budget_manager', 'Budget Manager'), ('finance_ceo', 'Finance CEO'),
                   ('vice_president', 'Vice President'), ('president', 'President'), ('confirmed', 'Confirmed'),
                   ('refused', 'Refused')], default='draft', string='Status', tracking=True)
    type = fields.Selection(selection=[('unlock', 'Unlock'), ('support', 'Support'), ('transfer', 'Transfer'),
                                       ('transfer_budget', 'Transfer Budgets Balance')], string='Type', readonly=True, tracking=True)


    @api.depends('transfer_type')
    def _compute_transfer(self):
        for record in self:
            if record.transfer_type == 'same_position':
                record.transfer = True
            else:
                record.transfer = False

    @api.depends('line_ids.percentage')
    def _compute_total_percentage(self):
        for record in self:
            if record.state != 'confirmed':
                record.total_percentage = sum(line.percentage for line in record.line_ids)
            else:
                record.total_percentage = sum(line.percentage_after_confirm for line in record.line_ids)

    @api.constrains('budget_id')
    def _check_closed_fiscal_year(self):
        for record in self:
            if record.type in ['transfer','support']:
                if record.budget_id.fiscalyear_id.state == 'closed':
                    raise ValidationError(_("This procedure cannot be done due to the closure of the fiscal year for this budget"))

    @api.constrains('date', 'budget_id')
    def _check_date_within_budget(self):
        for record in self:
            if record.date and record.budget_id:
                if not (record.budget_id.date_from <= record.date <= record.budget_id.date_to):
                    raise ValidationError(_("The date of the budget operation must be within the budget's start and end dates."))

    @api.constrains('line_ids')
    def _check_transfer_sums(self):
        for record in self:
            if record.type == 'transfer':
                if not record.line_ids:
                    raise ValidationError(_("The budget operation must have at least one line."))
                total_debit = sum(line.transfer_debit for line in record.line_ids)
                total_credit = sum(line.transfer_credit for line in record.line_ids)
                if total_debit <= 0 or total_credit <= 0:
                    raise ValidationError(_("Total Transfer Amount Must Be Greater Than 0"))
                if total_debit != total_credit :
                    raise ValidationError(_("The Total Transfer Debit Must Equal The Total Transfer Credit."))

                for line in record.line_ids:
                    budget_lines = self.env['crossovered.budget.lines'].search(
                        [('crossovered_budget_id', '=', record.budget_id.id), ('id', '=', line.budget_line_id.id)])
                    if budget_lines.available_liquidity < 0:
                        raise ValidationError(_("Available Liquidity cannot be negative in any budget line."))
                    if budget_lines.available_liquidity - line.transfer_credit < 0:
                        raise ValidationError(_("Available Liquidity cannot be negative in any budget line."))

    @api.constrains('line_ids', 'transfer_type')
    def _check_same_general_budget(self):
        for record in self:
            if record.transfer_type == 'same_position':
                general_budget_ids = record.line_ids.mapped('general_budget_id')
                if len(set(general_budget_ids)) > 1:
                    raise ValidationError(
                        _("When Transfer Type is 'Same Position', all lines must have the same General Budget."))

    @api.constrains('amount')
    def _check_amount_support_budget(self):
        for record in self:
            if record.type == 'support' and record.amount <= 0.00:
                raise ValidationError(_("Amount must be greater than zero"))

    @api.constrains('transfer_from_budget_id', 'transfer_to_budget_id', 'line_ids')
    def _check_matching_budget_lines(self):
        if self.type == 'transfer_budget':

            for line in self.line_ids:
                if line.budget_line_from_id.available_liquidity <= 0:
                    raise ValidationError(_("The available liquidity of budget lines in Transfer From Budget must be greater than zero."))

                if self.transfer_from_budget_id and self.transfer_to_budget_id:
                    from_budget_line = line.budget_line_from_id

                    matching_to_budget_line = self.env['crossovered.budget.lines'].search([
                        ('crossovered_budget_id', '=', self.transfer_to_budget_id.id),
                        ('item_budget_id', '=', from_budget_line.item_budget_id.id),
                        ('general_budget_id', '=', from_budget_line.general_budget_id.id)], limit=1)

                    if not matching_to_budget_line:
                        raise ValidationError(_('The budget line %s does not have a matching line in Transfer To Budget:') % from_budget_line.display_name)

    @api.constrains('transfer_from_budget_id', 'transfer_to_budget_id')
    def _check_budget_dates(self):
        for record in self:
            if record.transfer_from_budget_id and record.transfer_to_budget_id:
                from_budget_date_from = record.transfer_from_budget_id.date_from
                to_budget_date_from = record.transfer_to_budget_id.date_from
                if from_budget_date_from >= to_budget_date_from:
                    raise ValidationError(_("The Transfer From Budget must be older than the Transfer To Budget"))

    @api.onchange('budget_id')
    def _onchange_budget_id(self):
        if self.budget_id:
            general_budget_ids = self.budget_id.crossovered_budget_line.mapped('general_budget_id.id')
            self.line_ids = [(5, 0, 0)]  # Reset line_ids
            return {'domain': {'general_budget_id': [('id', 'in', general_budget_ids)]}}
        else:
            self.general_budget_id = False
            self.line_ids = [(5, 0, 0)]  # Reset line_ids
            return {'domain': {'general_budget_id': []}}

    @api.onchange('line_ids')
    def _onchange_line_ids(self):
        if self.line_ids:
            # Set transfer_credit to 0 for the line with transfer_debit
            for line in self.line_ids:
                if line.transfer_debit and line.transfer_credit != 0:
                    line.transfer_credit = 0

            # Calculate total_debit excluding the last line
            if len(self.line_ids) > 1:
                total_debit = sum(line.transfer_debit for line in self.line_ids[:-1])
                # self.line_ids[-1].transfer_credit = total_debit

    @api.onchange('general_budget_id')
    def _onchange_general_budget_id(self):
        if self.general_budget_id:
            self.line_ids = [(5, 0, 0)]

    @api.onchange('general_budget_id')
    def _compute_domain_from_budget_line_id(self):
        domain = [('id', 'in', [])]
        if self.budget_id:
            self.from_budget_line_id = [(5, 0, 0)]
            search_domain = [('crossovered_budget_id', '=', self.budget_id.id),
                             ('general_budget_id', '=', self.general_budget_id.id)]
            budget_lines = self.env['crossovered.budget.lines'].search(search_domain)
            domain = [('id', 'in', budget_lines.ids)]
        return {'domain': {'from_budget_line_id': domain}}

    @api.onchange('transfer_from_budget_id')
    def _onchange_transfer_from_budget_id(self):
        if self.transfer_from_budget_id:
            return {'domain': {'transfer_to_budget_id': [('id', '!=', self.transfer_from_budget_id.id)]}}
        else:
            return {'domain': {'transfer_to_budget_id': []}}

    @api.onchange('transfer_to_budget_id')
    def _onchange_transfer_to_budget_id(self):
        if self.transfer_to_budget_id:
            return {'domain': {'transfer_from_budget_id': [('id', '!=', self.transfer_to_budget_id.id)]}}
        else:
            return {'domain': {'transfer_from_budget_id': []}}

    def action_budget_manager(self):

        self.write({'state': 'budget_manager'})

    def action_finance_ceo(self):
        self.write({'state': 'finance_ceo'})

    def action_vice_president(self):
        if self.type == 'transfer':
            if self.transfer_type == 'same_position':
                total_percentage = sum(line.percentage for line in self.line_ids)
                if total_percentage <= 0.50:
                    self.action_budget_confirmed()
                else:
                    self.write({'state': 'vice_president'})
            else:
                self.write({'state': 'vice_president'})
        else:
            self.action_budget_confirmed()

    def action_president(self):
        self.write({'state': 'president'})

    def action_budget_confirmed(self):
        for record in self:
            if record.type == 'transfer':
                for line in record.line_ids:
                    budget_lines = self.env['crossovered.budget.lines'].search(
                        [('crossovered_budget_id', '=', record.budget_id.id), ('id', '=', line.budget_line_id.id)])
                    if line.transfer_debit <= budget_lines.available_liquidity or line.transfer_debit > budget_lines.available_liquidity:
                        if budget_lines.available_liquidity < 0:
                            raise ValidationError(_("Available Liquidity cannot be negative in any budget line."))
                        if budget_lines.available_liquidity - line.transfer_credit < 0:
                            raise ValidationError(_("Available Liquidity cannot be negative in any budget line."))
                        budget_lines.transfer_credit += line.transfer_credit
                        budget_lines.transfer_debit += line.transfer_debit
                        line.available_in_line = line.available_liquidity - line.transfer_debit + line.transfer_credit
                        line.before_modification = line.after_modification - line.transfer_debit + line.transfer_credit

                        if line.available_liquidity - line.transfer_debit != 0:
                             line.percentage_after_confirm = (line.transfer_debit / (line.available_liquidity - line.transfer_debit)) % 100
                        else:
                            line.percentage_after_confirm = 1

            else:
                budget_lines = self.env['crossovered.budget.lines'].search(
                    [('crossovered_budget_id', '=', record.budget_id.id), ('id', '=', record.from_budget_line_id.id)])
                budget_lines.additions += record.amount
            record.state = 'confirmed'
        return True

    def transfer_available_liquidity(self):
        for record in self:
            if record.transfer_from_budget_id.fiscalyear_id.state == 'closed':
                raise ValidationError(
                    _("This procedure cannot be done due to the closure of the fiscal year for this budget"))
            if not record.line_ids:
                raise ValidationError(_("The budget operation must have at least one line."))
            for line in record.line_ids:
                budget_line_from = line.budget_line_from_id
                # Check if a budget line is selected
                if budget_line_from and budget_line_from.available_liquidity > 0:
                    general_budget_id = budget_line_from.general_budget_id.id
                    item_budget_id = budget_line_from.item_budget_id.id
                    # Find matching budget lines in transfer_from_budget_id
                    matching_from_budget_lines = self.env['crossovered.budget.lines'].search([
                        ('crossovered_budget_id', '=', record.transfer_from_budget_id.id),
                        ('general_budget_id', '=', general_budget_id),
                        ('item_budget_id', '=', item_budget_id)
                    ])
                    # Find matching budget lines in transfer_to_budget_id
                    matching_to_budget_lines = self.env['crossovered.budget.lines'].search([
                        ('crossovered_budget_id', '=', record.transfer_to_budget_id.id),
                        ('general_budget_id', '=', general_budget_id),
                        ('item_budget_id', '=', item_budget_id)
                    ])
                    # Transfer the available liquidity and update the opening amount
                    if matching_from_budget_lines and matching_to_budget_lines:
                        for from_line in matching_from_budget_lines:
                            for to_line in matching_to_budget_lines:
                                # Add available liquidity to the opening_amount of the target budget line
                                to_line.write(
                                    {'opening_amount': to_line.opening_amount + from_line.available_liquidity})

                                # Set the available_liquidity to 0 after the transfer
                                from_line.write({'transferd_balance': from_line.available_liquidity,'is_transferd': True})

            record.state = 'confirmed'

    def action_budget_draft(self):
        return {
            'name': _('Re-Budget Management Budget Operation'),
            'type': 'ir.actions.act_window',
            'res_model': 'operation.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_reason': '', 'default_action': 'draft'}
        }

    def action_budget_refused(self):
        return {
            'name': _('Reject Budget Operation'),
            'type': 'ir.actions.act_window',
            'res_model': 'operation.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_reason': '', 'default_action': 'refused'}
        }

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(_('You cannot delete a record not in draft state'))
        return super(BudgetOperations, self).unlink()


class BudgetOperationsLine(models.Model):
    _name = 'budget.operations.line'
    _description = 'Budget Operations Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Inherit from mail.thread for tracking
    currency_id = fields.Many2one('res.currency', related='budget_line_id.currency_id', readonly=True)
    operation_id = fields.Many2one('budget.operations', string='Operation', ondelete='cascade')
    state = fields.Selection(related='operation_id.state')
    budget_line_id = fields.Many2one('crossovered.budget.lines', string='Budget Position', ondelete='cascade', tracking=True)
    item_budget_id = fields.Many2one(related='budget_line_id.item_budget_id', readonly=False)
    general_budget_id = fields.Many2one(related='budget_line_id.general_budget_id', readonly=False)
    transfer_debit = fields.Monetary(currency_field='currency_id', readonly=False, tracking=True)
    transfer_credit = fields.Monetary(currency_field='currency_id', readonly=False, tracking=True)
    after_modification = fields.Monetary(related='budget_line_id.after_modification', currency_field='currency_id')
    before_modification = fields.Monetary('Before Modification', currency_field='currency_id')
    planned_amount = fields.Monetary(related='budget_line_id.planned_amount', currency_field='currency_id')
    available_liquidity = fields.Monetary(related='budget_line_id.available_liquidity', currency_field='currency_id')
    available_in_line = fields.Monetary('Available in Line', currency_field='currency_id')
    percentage = fields.Float(compute='_compute_operations_percentage', string='Percentage')
    percentage_after_confirm = fields.Float(string='Percentage')
    budget_line_from_id = fields.Many2one('crossovered.budget.lines', string='Budget Line (From)')
    available = fields.Monetary('Available Liquidity', related='budget_line_from_id.available_liquidity')
    transferd_balance = fields.Monetary(related='budget_line_from_id.transferd_balance')
    transfer_amount = fields.Monetary('Transfer Amount')

    @api.onchange('budget_line_from_id')
    def _onchange_transfer_from_budget_id(self):
        domain = [('id', 'in', [])]
        if self.operation_id and self.operation_id.transfer_from_budget_id:
            selected_budget_line_ids = self.operation_id.line_ids.mapped('budget_line_from_id.id')
            search_domain = [('crossovered_budget_id', '=', self.operation_id.transfer_from_budget_id.id),('is_transferd','=',False),
                             ('id', 'not in', selected_budget_line_ids), ('period', '=', 'not_annually'), ('available_liquidity', '>', 0)]
            budget_lines = self.env['crossovered.budget.lines'].search(search_domain)
            domain = [('id', 'in', budget_lines.ids)]
        return {'domain': {'budget_line_from_id': domain}}

    @api.onchange('transfer_debit')
    def _onchange_transfer_debit(self):
        if self.transfer_debit:
            self.transfer_credit = 0
        self.operation_id._onchange_line_ids()  # Ensure the parent model recalculates the last line's credit

    @api.depends('transfer_debit')
    def _compute_operations_percentage(self):
        total_transfer_debit = sum(line.transfer_debit for line in self if line.transfer_debit)
        for line in self:
            line.percentage = 0.00
            if total_transfer_debit > 0.00 and line.transfer_debit and line.available_liquidity:
                line.percentage = (line.transfer_debit / line.available_liquidity) % 100
    #         todo start
            if total_transfer_debit > 0.00  and line.available_liquidity==0.00:
                line.percentage = 1
            # todo end

    @api.onchange('budget_line_id')
    def _compute_domain_budget_line_id(self):
        domain = [('id', 'in', [])]
        if self.operation_id.budget_id:
            selected_budget_line_ids = self.operation_id.line_ids.mapped('budget_line_id.id')
            search_domain = [('crossovered_budget_id', '=', self.operation_id.budget_id.id),
                             ('id', 'not in', selected_budget_line_ids)]
            if self.operation_id.transfer_type == 'same_position' and self.operation_id.general_budget_id:
                search_domain.append(('general_budget_id', '=', self.operation_id.general_budget_id.id))
            budget_lines = self.env['crossovered.budget.lines'].search(search_domain)
            domain = [('id', 'in', budget_lines.ids)]
        return {'domain': {'budget_line_id': domain}}

    @api.model
    def create(self, values):
        record = super(BudgetOperationsLine, self).create(values)
        record._post_budget_line_change_message(values, 'create')
        return record

    def write(self, values):
        res = super(BudgetOperationsLine, self).write(values)
        self._post_budget_line_change_message(values, 'write')
        return res

    def _post_budget_line_change_message(self, values, operation_type):
        for record in self:
            msg = ""
            changes = False
            if 'budget_line_id' in values:
                old_budget_line = record.budget_line_id.display_name if record.budget_line_id else _('N/A')
                new_budget_line = self.env['crossovered.budget.lines'].browse(values['budget_line_id']).display_name
                msg = _("<li> Budget Line: %(old)s -> %(new)s", old=old_budget_line, new=new_budget_line) + "<br/>"
                changes = True
            if 'transfer_debit' in values:
                msg += _("<li> Transfer Debit: %(old)s -> %(new)s", old=record.transfer_debit,
                         new=values['transfer_debit']) + "<br/>"
                changes = True
            if 'transfer_credit' in values:
                msg += _("<li> Transfer Credit: %(old)s -> %(new)s", old=record.transfer_credit,
                         new=values['transfer_credit']) + "<br/>"
                changes = True
            if 'general_budget_id' in values:
                old_general_budget = record.general_budget_id.display_name if record.general_budget_id else _('N/A')
                new_general_budget = self.env['crossovered.budget.lines'].browse(
                    values['general_budget_id']).display_name
                msg += _("<li> General Budget: %(old)s -> %(new)s", old=old_general_budget,
                         new=new_general_budget) + "<br/>"
                changes = True
            msg += "</ul>"
            if changes:
                record.operation_id.message_post(body=msg)
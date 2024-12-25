# -*- coding: utf-8 -*-
from odoo import api, models, fields, tools, _
from odoo.exceptions import UserError, ValidationError


class ProjectBudget(models.Model):
    _inherit = "crossovered.budget"

    fiscalyear_id = fields.Many2one(required=False)
    project_id = fields.Many2one('project.project', 'Project', required=False,tracking=True)
    project_no = fields.Char("Project Number", related="project_id.project_no", tracking=True)
    sale_order_id = fields.Many2one('sale.order', related="project_id.sale_order_id", string="Proposal")
    sale_order_amount = fields.Monetary("Total Amount", related="project_id.sale_order_amount",tracking=True)
    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account",
                                          related="project_id.analytic_account_id")
    hour_line_ids = fields.One2many('crossovered.budget.lines', 'crossovered_budget_id', string='Hour lines',
                                    copy=False,domain=[('is_timesheet_hours', '=', True)])
    expensess_line_ids = fields.One2many('crossovered.budget.lines', 'crossovered_budget_id', string='Hour lines',
                                    copy=False,domain=[('is_timesheet_hours', '=', False)])

    project_user_id = fields.Many2one("res.users", related="project_id.user_id", string="Project Manager", store=True)

    total_budget_cost = fields.Monetary('Total Cost', compute='_compute_budget_amounts',
                                        help="Total Cost", tracking=True)
    projected_profit = fields.Monetary('Projected Profit', compute='_compute_budget_amounts',
                                       help="Contract Value(With VAT & other taxes) - Total Cost",
                                       tracking=True)
    man_hours = fields.Boolean('Man hours' , related="project_id.man_hours",default=False)


    @api.depends("crossovered_budget_line", "crossovered_budget_line.planned_amount",
                 "crossovered_budget_line.project_planned_amount")
    def _compute_budget_amounts(self):
        """
        Get Total Budget amounts
        """
        for rec in self:
            total_budget_cost = 0.0
            projected_profit = 0.0
            if rec.crossovered_budget_line:
                total_budget_cost = sum(rec.crossovered_budget_line.mapped("project_planned_amount"))
                projected_profit = rec.sale_order_amount - total_budget_cost
            rec.total_budget_cost = total_budget_cost
            rec.projected_profit = projected_profit
            

    @api.onchange('project_id')
    def _onchange_project(self):
        """
        set budget name by project name
        """
        if self.project_id:
            self.name = self.project_id.display_name or "/"
            self.date_from = self.project_id.start
            self.date_to = self.project_id.date

        else:
            pass


    @api.constrains('date_from', 'date_to', 'fiscalyear_id')
    def _check_dates_fiscalyear(self):
        """ 
        pass fiscalyear constrain in case of project budget
        """
        if not self.project_id:
            return super(ProjectBudget, self)._check_dates_fiscalyear()
        else:
            pass

    @api.constrains('project_id')
    def _check_project_id(self):
        """
        make sure that the project have just one budget
        """
        if self.project_id:
            projects = self.env['crossovered.budget'].search(
                [('project_id', '=', self.project_id.id), ('id', '!=', self.id)])
            if len(projects) > 0:
                raise ValidationError("The Project Must have just only one budget")

    @api.constrains('project_id','crossovered_budget_line','crossovered_budget_line.qty')
    def _check_project_hours(self):
        """
        Make sure that budget hours not more than project Allocated hours
        """
        if self.project_id:
            project_hours = sum(self.project_id.project_phase_ids.mapped("estimated_hours"))
            budget_hours = sum(self.hour_line_ids.mapped("qty"))
            if project_hours > budget_hours:
                raise ValidationError("Project Allocated hours must not be more than Man-Hours in budget!")

    def action_budget_confirm(self):
        self._check_project_hours()
        self.write({'state': 'confirm'})

    def action_budget_approve(self):
        self._check_project_hours()
        self.write({'state': 'approve'})

    def action_budget_edit(self):
        self.write({'state': 'draft'})

    def action_budget_validate(self):
        self.write({'state': 'validate'})


    @api.constrains('sale_order_amount', 'crossovered_budget_line','crossovered_budget_line.project_planned_amount')
    def budget_total(self):
        for item in self:
            if item.project_id and item.project_id.sale_order_id and sum(
                    item.crossovered_budget_line.mapped('project_planned_amount')) > item.sale_order_amount:
                raise ValidationError(_('The Budget Total Amount Must Not Exceed Project Sale Value'))

    def open_sale_order(self):
        return {
            'name': 'Sale Order',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'sale.order',
            'type': 'ir.actions.act_window',
            'domain': [('id', '=', self.project_id.sale_order_id.id)],
            "res_id": self.project_id.sale_order_id.id,
        }

    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise UserError(_('You cannot remove the Budget in %s state.' % (record.state)))
        return super(ProjectBudget, self).unlink()


class ProjectBudgetPost(models.Model):
    _inherit = "account.budget.post"

    is_timesheet_hours = fields.Boolean(string='Is Timesheet Hours')

    def _check_account_ids(self, vals):
        # Inherit to pass the check in case of timesheet.
        if ('is_timesheet_hours' in vals and not vals['is_timesheet_hours']):
            return super(ProjectBudgetPost, self)._check_account_ids(vals)
        else:
            pass

class ProjectBudgetLine(models.Model):
    _name = "crossovered.budget.lines"
    _inherit = ["crossovered.budget.lines","mail.thread"]

    project_id = fields.Many2one("project.project", related='crossovered_budget_id.project_id',store=True,string='Project')
    is_timesheet_hours = fields.Boolean(related='general_budget_id.is_timesheet_hours',string='Is Timesheet Hours')
    qty = fields.Float(string="qty/hours", tracking=True)
    amount = fields.Float(string="Unit cost", tracking=True)
    timesheet_hours = fields.Float(string="Consumed Hours", tracking=True)
    planned_amount = fields.Monetary('Planned Amount', required=True, tracking=False)
    project_planned_amount = fields.Monetary('Budget Amount', tracking=True)
    project_remaining_amount = fields.Monetary('Remaining Amount', compute="_compute_project_remaining_amount",tracking=False)
    date_from = fields.Date('Start Date', tracking=True)
    date_to = fields.Date('End Date', tracking=True)
    man_hours = fields.Boolean('Man hours' , related="project_id.man_hours",default=False)

    @api.onchange('qty', 'amount','practical_amount')
    def _onchange_budget_amount(self):
        for rec in self:
            rec.planned_amount = (rec.qty * rec.amount) * -1
            rec.project_planned_amount = abs(rec.planned_amount)

    def _compute_project_remaining_amount(self):
        for rec in self:
            rec.project_remaining_amount = 0.0
            rec.planned_amount = (rec.qty  * rec.amount) * -1
            rec.project_planned_amount = abs(rec.planned_amount)
            rec.project_remaining_amount = rec.project_planned_amount + rec.practical_amount

    # todo review this funtion
    def _compute_practical_amount(self):
        for line in self:
            if line.general_budget_id.is_timesheet_hours:
                hours_domain = [('project_id', '=', line.crossovered_budget_id.project_id.id),
                                         # ('date', '>=', line.date_from),
                                         # ('date', '<=', line.date_to),
                                         # ('sheet_id.state', '=', 'done')
                                         ]
                total_canceled_hours = sum(
                    self.env['account.analytic.line'].search(hours_domain).mapped('unit_amount'))
                line.timesheet_hours = total_canceled_hours
                line.practical_amount = - (line.timesheet_hours * line.amount)
            else:
                # return super(ProjectBudgetLine, self)._compute_practical_amount()
                acc_ids = line.general_budget_id.account_ids.ids
                date_to = line.date_to
                date_from = line.date_from
                if line.analytic_account_id.id:
                    analytic_line_obj = self.env['account.analytic.line']
                    domain = [('account_id', '=', line.analytic_account_id.id),
                              ('date', '>=', date_from),
                              ('date', '<=', date_to),
                              ]
                    if acc_ids:
                        domain += [('general_account_id', 'in', acc_ids)]

                    where_query = analytic_line_obj._where_calc(domain)
                    analytic_line_obj._apply_ir_rules(where_query, 'read')
                    from_clause, where_clause, where_clause_params = where_query.get_sql()
                    select = "SELECT SUM(amount) from " + from_clause + " where " + where_clause

                else:
                    aml_obj = self.env['account.move.line']
                    domain = [('account_id', 'in',
                               line.general_budget_id.account_ids.ids),
                              ('date', '>=', date_from),
                              ('date', '<=', date_to),
                              ('move_id.state', '=', 'posted')
                              ]
                    where_query = aml_obj._where_calc(domain)
                    aml_obj._apply_ir_rules(where_query, 'read')
                    from_clause, where_clause, where_clause_params = where_query.get_sql()
                    select = "SELECT sum(credit)-sum(debit) from " + from_clause + " where " + where_clause
                self.env.cr.execute(select, where_clause_params)
                line.practical_amount = self.env.cr.fetchone()[0] or 0.0

    @api.constrains('project_id','planned_amount','practical_amount')
    def _check_project_amounts(self):
        for rec in self:
            if rec.project_id:
                if abs(rec.planned_amount) < abs(rec.practical_amount):
                    raise ValidationError(_("Budget amount can't be less than actual amount!"))

    @api.constrains('general_budget_id', 'analytic_account_id')
    def _must_have_analytical_or_budgetary_or_both(self):
        for record in self:
            if not record.analytic_account_id and not record.general_budget_id:
                raise ValidationError(
                    _("You have to enter at least a budgetary position or analytic account on a budget line."))

    def open_line(self):
        self.ensure_one()
        return {
            'name': _('Budget Line'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'crossovered.budget.lines',
            'res_id': self.id,
            'views': [(self.env.ref('project_budget.crossovered_budget_line_log_form').id, 'form'), ],
            'target': 'current',
            'type': 'ir.actions.act_window',
        }



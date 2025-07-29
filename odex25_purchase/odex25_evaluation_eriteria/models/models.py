# -*- coding: utf-8 -*-
from odoo import models, fields, api,_
from odoo.exceptions import ValidationError

from odoo import models, fields, api
class CommitteeTypesInherit(models.Model):
    _inherit = 'purchase.committee.type'

    # type = fields.Selection([('operational', 'Operational'), ('strategic', 'Strategic')], string='Type')

    purchase_committee_type_line = fields.One2many('purchase.committee.type.line', 'purchase_committee_type')
    available_types = fields.Selection(
        selection=[
            ('project', 'Project'),
            ('strategic', 'Strategic'),
            ('operational', 'Operational'),
        ],
        string="Available Types",
    )

    @api.constrains('purchase_committee_type_line', 'purchase_committee_type_line.degree')
    def _check_degree(self):
        for rec in self:
            if rec.purchase_committee_type_line and sum(rec.purchase_committee_type_line.mapped('degree')) > 100:
                raise ValidationError(_("The Sum of all degrees can't be equal or greater than 100"))

    # @api.onchange('available_types')
    # def _onchange_available_types(self):
    #     if self.available_types == 'operational':
    #         self.available_types = False
    #
    # @api.onchange('available_types')
    # def _onchange_available_types(self):
    #     if self.available_types == 'operational':
    #         self.available_types = False
class CommitteeTypesInheritLine(models.Model):
    _name = 'purchase.committee.type.line'

    purchase_committee_type = fields.Many2one('purchase.committee.type')
    sequence = fields.Integer(string="Sequence")
    evaluation = fields.Float(string="Evaluation")
    evaluation_criteria = fields.Char(string="Evaluation criteria")
    degree = fields.Float(string="Degree")

    @api.constrains('evaluation')
    def _check_evaluation(self):
        for rec in self:
            if rec.evaluation and rec.degree and rec.evaluation > rec.degree:
                raise ValidationError(_("Evaluation can't be greater than Degree"))
class PurchaseRequisitionCustomInherit(models.Model):
    _inherit = 'purchase.requisition'

    type = fields.Selection([
        ('project', 'Project'),
        ('operational', 'Operational'),
        ('strategic', 'Strategic')
    ], default='operational')

    committee_type_id = fields.Many2one(
        'purchase.committee.type',
        string='Committee Type',
        domain="[('available_types', '=', type)]"
    )

    @api.onchange('type')
    def _onchange_type(self):
        if self.type:
            committees = self.env['purchase.committee.type'].search([('available_types', '=', self.type)])
            if committees:
                self.committee_type_id = committees[0]
            else:
                self.committee_type_id = False
        else:
            self.committee_type_id = False

class PurchaseOrderCustomSelect(models.Model):
    _inherit = "purchase.order"
    eval_date = fields.Date(string='date',)

    initial_evaluation_lines = fields.One2many(comodel_name='initial.evaluation.criteria', inverse_name='po_id', string='Initial Evaluation Criteria',)

    total_evaluation = fields.Float(string='Total Evaluation', compute='_compute_evaluation')
    avg_evaluation = fields.Float(string='Average Evaluation', compute='_compute_evaluation')

    committee_members = fields.Many2many(comodel_name='res.users', compute='_compute_committee_members', string='Committee Members')

    def analytic_id_poa(self):
        print('re = ',self.requisition_id)
        for rec in self.order_line:
            analytic_account_id = rec.account_analytic_id
            return analytic_account_id


    def get_budget_id(self):
        budget_id = self.env['budget.confirmation'].search([
            '|', '|',
            ('po_id', '=', self.id),
            ('ref', '=', self.name),
            ('ref', '=', self.requisition_id.name)
        ], limit=1)
        return budget_id

    def get_remain_last(self):
        res = self.get_budget_id()
        if res :
            for rec in res.lines_ids:
                return rec.remain

    def get_band_name(self):
        res = self.get_budget_id()
        if res:
            for rec in res.lines_ids:
                return rec.account_id.name

    def get_remain(self):
        res = self.get_budget_id()
        if res:
         for rec in res.lines_ids:
            # res = rec.crossovered_budget_id
                return rec.new_balance

    def get_user_approve_budget_id(self):
        res = self.get_budget_id()
        return res.approved_by_id
    def get_date_approve_budget_id(self):
            res = self.get_budget_id()
            return res.approved_date

    def get_evaluation_summary(self):
        member_totals = {}  # {member_name: total_evaluation}
        for line in self.initial_evaluation_lines:
            name = line.user_id.name
            member_totals[name] = member_totals.get(name, 0) + line.evaluation
        return {
            'members': list(member_totals.keys()),
            'totals': member_totals,
        }
    @api.depends('initial_evaluation_lines', 'initial_evaluation_lines.user_id')
    def _compute_committee_members(self):
        for rec in self:
            members = []
            rec.committee_members = False
            if rec.initial_evaluation_lines:
                members = rec.initial_evaluation_lines.mapped('user_id')
            if members:
                rec.committee_members = members.ids


    @api.depends('initial_evaluation_lines', 'initial_evaluation_lines.evaluation')
    def _compute_evaluation(self):
        for rec in self:
            total = 0
            avg = 0
            if rec.initial_evaluation_lines:
                evaluations = rec.initial_evaluation_lines.mapped('evaluation')
                total = sum(evaluations)
                avg = sum(evaluations)/len(evaluations)
            rec.total_evaluation = total
            rec.avg_evaluation = avg

    def action_select(self):
        for member in self.committe_members:
            if member.user_id.id == self.env.user.id and member.select == True:
                raise ValidationError(_('You have already select this Quotation'))
        self.requisition_id.actual_vote += 1
        self.eval_date = fields.Date.today()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Select Reason',
            'res_model': 'select.reason',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_order_id': self.id, 'default_purchase_committee_type': self.requisition_id.committee_type_id.id if self.requisition_id else False}
        }
class SelectReason(models.TransientModel):
    _inherit = "select.reason"

    purchase_committee_type = fields.Many2one('purchase.committee.type', string='Committee Type')
    purchase_committee_type_line = fields.One2many('purchase.committee.type.line', related='purchase_committee_type.purchase_committee_type_line', readonly=False)

    def action_select(self):
        self.env['committe.member'].create({
            'po_id': self.order_id,
            'user_id': self.env.user.id,
            'selection_reason': self.select_reason,
            'select': True})
        order_id = self.env['purchase.order'].browse(self.order_id)
        order_id.select = True

        for rec in self.purchase_committee_type_line:
            self.env['initial.evaluation.criteria'].create({
                'po_id': self.order_id,
                'user_id': self.env.user.id,
                'evaluation_criteria': rec.evaluation_criteria,
                'evaluation': rec.evaluation,
                'degree': rec.degree
            })
            rec.evaluation = 0.0

class InitialEvaluationCriteria(models.Model):
    _name = "initial.evaluation.criteria"
    _description = "Initial Evaluation Criteria"

    po_id = fields.Many2one('purchase.order')
    req_id = fields.Many2one('purchase.request')
    user_id = fields.Many2one('res.users', "Member Name")
    sequence = fields.Integer(string="Sequence")
    evaluation_criteria = fields.Char(string="Evaluation criteria")
    evaluation = fields.Float(string="Evaluation")
    degree = fields.Float(string="Degree")
        
    
class BudgetConfirmation(models.Model):
    _inherit = 'budget.confirmation'
    # add user sign
    approved_by_id = fields.Many2one('res.users', string='Approved By')
    approved_date = fields.Date(string='Approval Date')

    def confirm(self):
        """
        change state to confirm and check budget
        """
        super(BudgetConfirmation, self).confirm()
        # add user sign
        self.approved_by_id = self.env.user
        self.approved_date = fields.Date.today()
        # end

# -*- coding: utf-8 -*-
from odoo import models, fields, api,_
from odoo.exceptions import ValidationError


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
            if rec.purchase_committee_type_line and sum(rec.purchase_committee_type_line.mapped('degree')) >= 100:
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

    initial_evaluation_lines = fields.One2many(comodel_name='initial.evaluation.criteria', inverse_name='po_id', string='Initial Evaluation Criteria',)

    def action_select(self):
        for member in self.committe_members:
            if member.user_id.id == self.env.user.id and member.select == True:
                raise ValidationError(_('You have already select this Quotation'))
        self.requisition_id.actual_vote += 1
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
    evaluation = fields.Float(string="Evaluation")
    degree = fields.Float(string="Degree")



# class SelectReasonCommittee(models.TransientModel):
#     _inherit = "select.reason"
#
#     evaluation_criteria_lines = fields.One2many(
#         'select.reason.evaluation.line',
#         'wizard_id',
#         string="Evaluation Criteria"
#     )
#     purchase_committee_type_line = fields.One2many(
#         'purchase.committee.type.line', 'purchase_committee_type',
#         string="Evaluation Criteria"
#     )
#
#     def action_select(self):
#         self.env['committe.member'].create({
#             'po_id': self.order_id,
#             'user_id': self.env.user.id,
#             'selection_reason': self.select_reason,
#             'select': True})
#         order_id = self.env['purchase.order'].browse(self.order_id)
#         order_id.select = True

# class SelectReasonEvaluationLine(models.TransientModel):
#     _name = 'select.reason.evaluation.line'
#     _description = 'Evaluation Criteria Lines'
#
#     wizard_id = fields.Many2one('select.reason', string="Wizard")
#     sequence = fields.Integer(string="Sequence", readonly=True)
#     criteria = fields.Char(string="Evaluation Criteria", readonly=True)
#     degree = fields.Float(string="Degree (%)", readonly=True)
#     evaluation = fields.Float(string="Evaluation", required=True)
# access_select_reason_evaluation_line,select.reason.evaluation.line access,model_select_reason_evaluation_line,,1,1,1,1

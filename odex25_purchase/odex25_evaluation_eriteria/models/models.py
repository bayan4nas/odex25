# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError


class CommitteeTypesInherit(models.Model):
    _inherit = 'purchase.committee.type'

    type = fields.Selection([('operational', 'Operational'), ('strategic', 'Strategic')], string='Type')

    purchase_committee_type_line = fields.One2many('purchase.committee.type.line', 'purchase_committee_type')


class CommitteeTypesInheritLine(models.Model):
    _name = 'purchase.committee.type.line'

    purchase_committee_type = fields.Many2one('purchase.committee.type')
    sequence = fields.Integer(string="Sequence")
    evaluation_criteria = fields.Char(string="Evaluation criteria")
    degree = fields.Float(string="Degree")


class PurchaseRequisitionCustomInherit(models.Model):
    _inherit = 'purchase.requisition'

    type = fields.Selection([
        ('project', 'Project'),
        ('operational', 'Operational'),
        ('strategic', 'Strategic')
    ], default='operational')

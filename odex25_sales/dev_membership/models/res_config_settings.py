# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    days_before = fields.Integer(
        string='Days Before First Reminder',
        config_parameter='dev_membership.days_before'
    )

    # Add new fields
    days_before_second = fields.Integer(
        string="Days Before Second Reminder",
        config_parameter='dev_membership.days_before_second'
    )

    membership_registration_evaluation = fields.Boolean(
        string="Evaluate Membership Registration",
        default=True,
        config_parameter='dev_membership.membership_registration_evaluation'
    )

    registration_evaluation_form = fields.Many2one(
        'survey.survey',
        string="Evaluation Form",
        config_parameter='dev_membership.registration_evaluation_form'
    )

    membership_renewal_evaluation = fields.Boolean(
        string="Evaluate Membership Renewal",
        default=True,
        config_parameter='dev_membership.membership_renewal_evaluation'
    )

    renewal_evaluation_form = fields.Many2one(
        'survey.survey',
        string="Evaluation Form",
        config_parameter='dev_membership.renewal_evaluation_form'
    )

    post_expiry_period = fields.Integer(
        string="Period After Expiry",
        config_parameter='dev_membership.post_expiry_period'
    )

    cancellation_reason = fields.Many2one(
        'cancellation.reason',
        string="Cancellation Reason",
        config_parameter='dev_membership.cancellation_reason'
    )
    interval = fields.Selection(string="Interval", selection=([('days', 'Days'),('month', 'Month')]),default='days')

class CancellReason(models.Model):
    _name = 'cancellation.reason'
    _description = 'Cancellation Reason'
    _order = 'sequence'

    name = fields.Char(string='Reasone of Cancellation')
    reasone_no = fields.Char("Number",tracking=True,copy=False)
    sequence = fields.Integer(string="Sequence", help="Define the display order")
    company_id = fields.Many2one('res.company', string='Company', readonly=True,default=lambda self: self.env.company)
    active = fields.Boolean(default=True)


# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class Refues(models.TransientModel):

    _name = "request.cancel.wizard"
    _description = "refuse Reason wizard"

    reason = fields.Text(string='Cancel Request Reason', required=True)
    request_id = fields.Many2one('family.member')
    # user_id = fields.Many2one('res.users', string='Scheduler User', default=lambda self: self.env.user, required=True)

    @api.model
    def default_get(self, fields):
        res = super(Refues, self).default_get(fields)
        active_ids = self.env.context.get('active_ids', [])
      
        res.update({'request_id': active_ids[0] if active_ids else False})
        return res

    def request_cancel_reason(self):
        self.ensure_one()
        self.request_id.write({'state':'cancelled','cancel_reason':self.reason})
        return {'type': 'ir.actions.act_window_close'}

class RefuesFile(models.TransientModel):


    _name = "request.canceld.wizard"
    _description = "refuse wizard"

    reason = fields.Text(string='Cancel Request Reason', required=True)
    request_id = fields.Many2one('detainee.file')

    @api.model
    def default_get(self, fields):
        res = super(RefuesFile, self).default_get(fields)
        active_ids = self.env.context.get('active_ids', [])

        res.update({'request_id': active_ids[0] if active_ids else False})
        return res

    def request_cancel_reason(self):
        self.ensure_one()
        self.request_id.write({'state':'rejected','cancel_reason':self.reason})
        return {'type': 'ir.actions.act_window_close'}

class RejectionReasonWizard(models.TransientModel):
    _name = 'benefit.rejection.wizard'

    reason = fields.Text("Reason")
    benefit_id = fields.Many2one('grant.benefit')

    @api.model
    def default_get(self, fields):
        res = super(RejectionReasonWizard, self).default_get(fields)
        active_ids = self.env.context.get('active_ids', [])
        res.update({'benefit_id': active_ids[0] if active_ids else False})
        return res

    def request_cancel_reason(self):
        self.benefit_id.message_post(body=f"السبب: {self.reason}")
        self.benefit_id.state = 'cancelled'
        return {'type': 'ir.actions.act_window_close'}

# models/wizard/revert_state_wizard.py
class RevertStateWizard(models.TransientModel):
    _name = 'revert.state.wizard'
    _description = 'Revert State Wizard'

    benefit_id = fields.Many2one('grant.benefit', string="Benefit",)
    reason = fields.Text("Reason")


    @api.model
    def default_get(self, fields):
        res = super(RevertStateWizard, self).default_get(fields)
        active_ids = self.env.context.get('active_ids', [])
        records = self.env['grant.benefit'].browse(active_ids)
        res.update({'benefit_id': records[0].id if records else False})
        return res

    def confirm_revert(self):
        self.benefit_id.reason_revert = self.reason
        self.benefit_id.state = self.benefit_id.previous_state
        self.benefit_id.message_post(body=f"السبب: {self.reason}")
        return {'type': 'ir.actions.act_window_close'}




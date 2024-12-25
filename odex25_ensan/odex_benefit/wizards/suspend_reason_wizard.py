# -*- coding: utf-8 -*-

from odoo import models, fields


class SuspendReasonWizard(models.TransientModel):
    _name = 'suspend.reason.wizard'

    _description = "Suspend Reason Wizard"

    def _default_entity(self):
        if self._context.get('active_model') == 'grant.benefit':
            return self._context.get('active_id')

    def _default_member(self):
        if self._context.get('active_model') == 'family.member':
            return self._context.get('active_id')

    def _default_state(self):
        return self._context.get('state')

    entity_id = fields.Many2one("grant.benefit", string="Entity", default=_default_entity)
    member_id = fields.Many2one("family.member", string="Member", default=_default_member)
    suspend_reason = fields.Many2one('suspend.reason',string='Suspend Reason')
    suspend_description = fields.Text(string='Suspend Description')
    suspend_attachment = fields.Binary(string='Suspend Attachment',attachment = True)
    suspend_type = fields.Selection(selection=[('temporarily_suspend', 'Temporarily Suspended'), ('suspend', 'Suspend')], string="Suspend Type")

    def action_submit(self):
        for rec in self:
            rec.entity_id.state = 'temporarily_suspended'
            rec.entity_id.suspend_reason = rec.suspend_reason
            rec.entity_id.suspend_description = rec.suspend_description
            rec.entity_id.suspend_type = rec.suspend_type
            rec.entity_id.suspend_attachment = rec.suspend_attachment
            rec.entity_id.suspend_method = 'manual'

    def action_member_submit(self):
        for rec in self:
            rec.member_id.state_a = 'temporarily_suspended'
            rec.member_id.suspend_reason = rec.suspend_reason
            rec.member_id.suspend_description = rec.suspend_description
            rec.member_id.suspend_type = rec.suspend_type
            rec.member_id.suspend_attachment = rec.suspend_attachment
            rec.member_id.suspend_method = 'manual'

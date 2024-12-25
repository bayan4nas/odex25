# -*- coding: utf-8 -*-

from odoo import models, fields


class ExceptionWizard(models.TransientModel):
    _name = 'exception.wizard'

    _description = "Exception Wizard"

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
    exception_reason = fields.Many2one('exception.reason',string='Exception Reason')
    exception_description = fields.Text(string='Exception Description')
    exception_type = fields.Selection(selection=[('temporarily_exception', 'Temporarily Exception'), ('permanent_exception', 'Permanent Exception')], string="Exception Type")
    exception_attachment = fields.Binary(string='Exception Attachment',attachment = True)
    exception_start_date = fields.Datetime(string='Exception Start Date')
    exception_end_date = fields.Datetime(string='Exception End Date')


    def action_submit(self):
        for rec in self:
            rec.entity_id.state = 'temporarily_exception'
            rec.entity_id.exception_start_date = rec.exception_start_date
            rec.entity_id.exception_end_date = rec.exception_end_date
            rec.entity_id.exception_reason = rec.exception_reason
            rec.entity_id.exception_description = rec.exception_description
            rec.entity_id.exception_type = rec.exception_type
            rec.entity_id.exception_attachment = rec.exception_attachment

    def action_member_submit(self):
        for rec in self:
            rec.member_id.state_a = 'temporarily_exception'
            rec.member_id.state = 'temporarily_exception'
            rec.member_id.exception_start_date = rec.exception_start_date
            rec.member_id.exception_end_date = rec.exception_end_date
            rec.member_id.exception_reason = rec.exception_reason
            rec.member_id.exception_description = rec.exception_description
            rec.member_id.exception_type = rec.exception_type
            rec.member_id.exception_attachment = rec.exception_attachment

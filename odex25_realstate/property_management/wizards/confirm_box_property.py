# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, tools, _


class ConfirmWizard(models.TransientModel):
    _name = 'confirm.wizard'
    _description = "Confirm Wizard"

    message = fields.Char(default='Do you want to proceed?')

    @api.model
    def default_get(self, fields):
        rec = super(ConfirmWizard, self).default_get(fields)
        active_id = self.env[self._context.get('active_model')].browse(self._context.get('active_id'))
        if self._context.get('rent_payment'):
            rec['message'] = _('There are a previous rent payment record if you proceed this will be removed !!')
        if not active_id:
            raise exceptions.ValidationError(_("Programming error: wizard action executed without active_id in context."))
        return rec

    def action_confirm(self):
        active_id = self.env[self._context['active_model']].browse(self._context['active_id'])
        if self._context.get('rent_payment'):
            active_id.remove_payment()
            active_id.generate_payments()
        return True

    def action_cancel(self):
        return False


# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.misc import format_date, formatLang


class OperationRejectWizard(models.TransientModel):
    _name = 'operation.reject.wizard'
    _description = 'Operation Reject Wizard'

    reason = fields.Text(string='Reason', required=True)
    confirmation = fields.Boolean()
    action = fields.Selection(selection=[('draft', 'draft'), ('refused', 'refused')])

    def action_confirmation_reject(self):
        global message
        self.ensure_one()
        confirmation = self.env['budget.confirmation'].browse(self._context.get('active_id'))
        if confirmation:
            confirmation.write({'state': 'cancel'})
            confirmation.cancel()
            message = _("Budget Confirmation Rejected: {}").format(self.reason)
            confirmation.message_post(body=message)
            if confirmation.type =='contract.contract':
                message_co = _("The contract has been cancelled: {}").format(self.reason)

                confirmation.contract_id.message_post(body=message_co)
            elif confirmation.type == 'purchase.request':
                message_po = _("The Purchase Request has been cancelled: {}").format(self.reason)
                confirmation.request_id.message_post(body=message_po)

    def action_reject(self):
        global message
        self.ensure_one()
        budget_operation = self.env['budget.operations'].browse(self._context.get('active_id'))
        if self.action == 'draft':
            budget_operation.write({'state': 'draft'})
            message = _("Budget operation moved to draft: {}").format(self.reason)
        elif self.action == 'refused':
            budget_operation.write({'state': 'refused'})
            message = _("Budget operation rejected: {}").format(self.reason)
        budget_operation.message_post(body=message)

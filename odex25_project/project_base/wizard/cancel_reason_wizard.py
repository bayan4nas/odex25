from odoo import models, fields, _
from odoo.exceptions import UserError, ValidationError


class CancelReasonWizard(models.TransientModel):
    _name = 'cancel.reason.wizard'
    _description = 'Cancel Reason Wizard'
    reason = fields.Text(string="Reason", required=True)
    certificate_id = fields.Many2one('completion.certificate', string="Certificate")

    def apply_reason_cancel(self):
        self.ensure_one()
        cert = self.certificate_id
        cert.message_post(body=_("❌ Cancellation applied. Reason: %s") % self.reason)
        cert.state = 'cancelled'


class GoBackReasonWizard(models.TransientModel):
    _name = 'go.back.reason.wizard'
    _description = 'Go Back Reason Wizard'
    reason = fields.Text(string="Reason", required=True)
    certificate_id = fields.Many2one('completion.certificate', string="Certificate")

    def apply_reason_go_back(self):
        self.ensure_one()
        cert = self.certificate_id
        previous_state = {
            'project_owner_approval': 'project_manager_preparation',
            'project_manager_review': 'project_owner_approval',
            'strategy_office_review': 'project_manager_review',
            'secretary_general_approval': 'strategy_office_review',
        }.get(cert.state)

        if previous_state:
            cert.message_post(body=_("↩️ Reverted to the previous state. Reason: %s" )% (self.reason))
            cert.state = previous_state
        else:
            raise UserError(_("Cannot revert from the current state: %s") % cert.state)

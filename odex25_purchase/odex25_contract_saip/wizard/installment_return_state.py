# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
from odoo.exceptions import ValidationError
from markupsafe import Markup
import json


class InstallmentReturnState(models.TransientModel):
    _name = 'installment.return.wizard'
    _description = "Installment Return State"

    installment_id = fields.Many2one(string="contract", comodel_name="line.contract.installment")
    note = fields.Text(string="Note")
    old_state = fields.Selection(related="installment_id.state", store=True)
    new_state = fields.Char(string="New State")
    state = fields.Selection([
        ('coc', 'COC'),
        ('confirmed', 'Confirmed'),
        ('not_invoiced', 'Not Invoiced'),
        ('invoiced', 'Invoiced'),
        ('paid', 'Paid'), ('cancel', 'Cancel')], tracking=True, string="Status", default="coc")
    check = fields.Boolean(string='Check')

    @api.onchange("state")
    def _onchange_state(self):
        self.new_state = self.state
        if not self.old_state:
            self.old_state = self.state

    def confirm_return(self):
        for rec in self:
            state_history = json.loads(rec.installment_id.state_history)
            if rec.installment_id.state not in state_history:
                state_history.append(self.installment_id.state)
            rec.installment_id.state_history = json.dumps(state_history)

            current_state = rec.installment_id.state
            target_state = rec.state

            self._check_valid_state_transition(current_state, target_state)

            rec.installment_id.write({
                "note": rec.note,
                "old_state": rec.old_state,
                "state": rec.new_state,
                "check": True,

            })

            message_body = rec._generate_message_body()
            rec.installment_id.message_post(body=Markup(message_body))

        return {"type": "ir.actions.act_window_close"}

    def _generate_message_body(self):
        old_state_label = self._get_label(self.old_state)
        new_state_label = self._get_label(self.state)
        title = _('Note return installment')

        return f"""
            <div role='alert' class='alert alert-warning'>
                <h4 class='alert-heading'>{title}</h4>
                <br/>
                <h5>{self.note}</h5>
                <h5>{old_state_label} ----> {new_state_label}</h5>
            </div>
        """

    def _get_label(self, key):
        return dict(self.installment_id._fields["state"]._description_selection(self.env)).get(key)

    def _check_valid_state_transition(self, current_state, target_state):
        if current_state == target_state:
            raise ValidationError(_("Cannot return to the same state: %s.") % self._get_label(current_state))
        state_sequence = ["coc", "confirmed", "not_invoiced", "invoiced", "paid", "cancel"]

        state_history = json.loads(self.installment_id.state_history)
        if target_state in state_history:
            return  # Allow transition to a previously visited state

        self._validate_transition(state_sequence, current_state, target_state)

    def _validate_transition(self, sequence, current_state, target_state):
        current_index = sequence.index(current_state)
        target_index = sequence.index(target_state)

        if target_index > current_index:
            raise ValidationError(_("Invalid state transition: cannot move from %s to %s.") % (
            self._get_label(current_state), self._get_label(target_state)))


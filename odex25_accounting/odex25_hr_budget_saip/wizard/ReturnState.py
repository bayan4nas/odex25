# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
from odoo.exceptions import ValidationError
from markupsafe import Markup
import json


class ReturnState(models.TransientModel):
    _name = "return.state.account"
    _description = "ReturnState"

    account_id = fields.Many2one(string="Account Move", comodel_name="account.move")
    # old_state = fields.Selection(related="account_id.state", store=True)
    new_state = fields.Char(string="New State")
    note = fields.Text(string="Note")
    state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("budget_management", "Budget Management"),
            ("accounting_department", "Accounting Department"),
            ("posted", "POST"),
            ("cancel", "Cancel"),
        ]
    )

    @api.onchange("state")
    def _onchange_state(self):
            self.new_state = self.state
            # if not self.old_state:
            #     self.old_state = self.state

    def confirm_return(self):
        state_history = json.loads(self.account_id.state_history)
        if self.account_id.state not in state_history:
            state_history.append(self.account_id.state)
        self.account_id.state_history = json.dumps(state_history)

        current_state = self.account_id.state
        target_state = self.state

        self._check_valid_state_transition(current_state, target_state)

        self.account_id.write({
            "note": self.note,
            # "old_state": self.old_state,
            "state": self.new_state,

        })

        message_body = self._generate_message_body()
        self.account_id.message_post(body=Markup(message_body))

        return {"type": "ir.actions.act_window_close"}

    def _generate_message_body(self):
        # old_state_label = self._get_label(self.old_state)
        new_state_label = self._get_label(self.state)
        return f"""
            <div role='alert' class='alert alert-warning'>
                <h4 class='alert-heading'>{_('Note return Committe expenses')}</h4>
                <br/>
                <h5>{self.note}</h5>
                    </div>
        """

    def _get_label(self, key):
        return dict(self.account_id._fields["state"]._description_selection(self.env)).get(key)

    def _check_valid_state_transition(self, current_state, target_state):
        if current_state == target_state:
            raise ValidationError(_("Cannot return to the same state: %s.") % self._get_label(current_state))
        state_sequence = ["draft", 'budget_management','accounting_department','posted','cancel']
        # market_sequence = ["draft", "dm", "send_budget", "wait_budget", "procurement", "ceo_purchase", "budget_approve", "general_supervisor"]

        state_history = json.loads(self.account_id.state_history)
        if target_state in state_history:
            return  # Allow transition to a previously visited state

        # if self.account_id.purchase_request_type not in ["emarket"]:
        self._validate_transition(state_sequence, current_state, target_state)
        # else:
            # self._validate_transition(market_sequence, current_state, target_state)

    def _validate_transition(self, sequence, current_state, target_state):
        current_index = sequence.index(current_state)
        target_index = sequence.index(target_state)

        if target_index > current_index:
            raise ValidationError(_("Invalid state transition: cannot move from %s to %s.") % (self._get_label(current_state), self._get_label(target_state)))

# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class AccountPayment(models.Model):
    _inherit = 'account.payment'

    state = fields.Selection(selection=[
            ('draft', 'Draft'),
            ('accountant', 'Accountant'),
            ('senior_accountant', 'Senior Accountant'),
            ('budget_management', 'Budget Management'),
            ('head_accounting', 'Head Of Accounting'),
            ('executive_director_finance', 'Executive Director of Finance'),
            ('vice_president_resources', 'Vice President of Corporate Resources '),
            ('chief_executive_officer', 'Chief Executive Officer'),
            ('posted', 'Posted'),
            ('cancel', 'Cancelled')
        ], tracking=True, default='draft')

    def action_draft_accountant(self):
        self.state = 'senior_accountant' if (
            self.amount > self.company_id.payment_approved) else 'accountant'

    def action_accountant(self):
        self.state = 'senior_accountant'


    def action_budget_management(self):
        self.state = 'head_accounting'

    def set_posted_state(self):
        if self.installment_id:
            self.installment_id.write({'state': 'paid'})
        self.state = 'posted'

    def action_head_accounting(self):
        self.state = 'executive_director_finance'

    def action_executive_director_finance(self):
        self.state = 'vice_president_resources'

    def action_vice_president_resources(self):
        if self.amount > self.company_id.payment_approved:
            self.state = 'chief_executive_officer'
        else:
            self.action_post()
            self.set_posted_state()

    def action_chief_executive_officer(self):
        self.action_post()
        self.set_posted_state()



class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    def _create_payments(self):
        self.ensure_one()
        batches = self._get_batches()
        edit_mode = self.can_edit_wizard and (len(batches[0]['lines']) == 1 or self.group_payment)
        to_process = []

        if edit_mode:
            payment_vals = self._create_payment_vals_from_wizard()
            to_process.append({
                'create_vals': payment_vals,
                'to_reconcile': batches[0]['lines'],
                'batch': batches[0],
            })
        else:
            # Don't group payments: Create one batch per move.
            if not self.group_payment:
                new_batches = []
                for batch_result in batches:
                    for line in batch_result['lines']:
                        new_batches.append({
                            **batch_result,
                            'lines': line,
                        })
                batches = new_batches

            for batch_result in batches:
                to_process.append({
                    'create_vals': self._create_payment_vals_from_batch(batch_result),
                    'to_reconcile': batch_result['lines'],
                    'batch': batch_result,
                })

        payments = self._init_payments(to_process, edit_mode=edit_mode)
        # self._post_payments(to_process, edit_mode=edit_mode)
        # self._reconcile_payments(to_process, edit_mode=edit_mode)
        return payments

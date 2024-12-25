# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import AccessError, ValidationError


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        res = super(AccountMove, self).action_post()
        for rec in self:
            payment = self.env['account.payment'].search([('move_id', '=', rec.id),
                                                          ('payment_type', '=', 'outbound')], limit=1)
            if payment and payment.state != 'posted':
                raise ValidationError(_("You can't post this journal entry because the payment is not posted yet."))
        return res


class AccountPayment(models.Model):
    _inherit = "account.payment"

    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('depart_manager', 'Department Manager'),
        ('accounting_manager', 'Accounting Manager'),
        ('general_manager', 'General Manager'),
        ('posted', 'Posted'),
        ('cancel', 'Cancelled'),
    ], default='draft', string='Status', required=True, readonly=True, copy=False, tracking=True)

    state_history = fields.Char(string='State History', default='draft')
    analytic_account_id = fields.Many2one(comodel_name='account.analytic.account', string='Analytic Account', copy=True)

    @api.model
    def create(self, vals):
        vals['state_history'] = 'draft'
        res = super(AccountPayment, self).create(vals)
        if res.analytic_account_id and res.move_id:
            for line in res.move_id.line_ids:
                if line.account_id.id == res.destination_account_id.id:
                    line.analytic_account_id = res.analytic_account_id.id
        return res

    def _check_permission(self, group_xml_id):
        if not self.env.user.has_group(group_xml_id):
            group_name = self.env.ref(group_xml_id).name
            raise AccessError(_("You do not have the necessary permissions (%s) to perform this action.") % group_name)

    def action_post(self):
        if self.payment_type == 'outbound':
            self._check_permission('odex25_account_payment_fix.group_posted')
        res = super(AccountPayment, self).action_post()
        for payment in self:
            payment.state = 'posted'
            if payment.analytic_account_id and payment.move_id:
                for line in payment.move_id.line_ids:
                    if line.account_id.id == payment.destination_account_id.id:
                        line.analytic_account_id = payment.analytic_account_id.id
        return res

    def action_cancel(self):
        payment_state = self.state
        res = super(AccountPayment, self).action_cancel()
        for payment in self:
            if self.payment_type == 'outbound' and payment.state != 'draft':
                self._check_permission(f'odex25_account_payment_fix.group_{payment.state}')
                if payment_state == 'draft':
                    payment.state = 'cancel'
                else:
                    payment.state = self.state_history
                    payment.state_history = 'cancel'
            else:
                payment.state = 'cancel'
            if payment.analytic_account_id and payment.move_id:
                for line in payment.move_id.line_ids:
                    if line.account_id.id == payment.destination_account_id.id:
                        line.analytic_account_id = payment.analytic_account_id.id
        return res

    def action_draft(self):
        res = super(AccountPayment, self).action_draft()
        for payment in self:
            payment.state = 'draft'
            if payment.analytic_account_id and payment.move_id:
                for line in payment.move_id.line_ids:
                    if line.account_id.id == payment.destination_account_id.id:
                        line.analytic_account_id = payment.analytic_account_id.id
            payment.state_history = 'cancel'
        return res

    def action_depart_manager(self):
        self._check_permission('odex25_account_payment_fix.group_depart_manager')
        self.state_history = self.state
        self.state = 'depart_manager'

    def action_accounting_manager(self):
        self._check_permission('odex25_account_payment_fix.group_accounting_manager')
        self.state_history = self.state
        self.state = 'accounting_manager'

    def action_general_manager(self):
        self._check_permission('odex25_account_payment_fix.group_general_manager')
        self.state_history = self.state
        self.state = 'general_manager'

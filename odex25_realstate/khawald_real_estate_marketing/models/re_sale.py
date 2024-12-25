# -*- coding: utf-8 -*-
##############################################################################
#
#   Expert (LCT, Life Connection Technology)
#    Copyright (C) 2021-2022 LCT
#
##############################################################################

from odoo.exceptions import ValidationError
from odoo import models, fields, api, _


class ReSale(models.Model):
    _inherit = "re.sale"

    handover_to_client_date = fields.Date('Handover to Client Date', index=True)
    reservation_id = fields.Many2one('property.reservation', string="Property Reservation")
    contract_id = fields.Many2one('contract.contract', string="Contract")
    invoice_count = fields.Integer(compute="_compute_invoice_count")
    payment_count = fields.Integer(compute="_compute_payment_count")
    installment_count = fields.Integer(compute="compute_installment_count")
    contract_type = fields.Selection(selection=[('sale', 'Customer'), ('purchase', 'Supplier')],
                                     related="contract_id.contract_type", store=True)
    contract_total_amount = fields.Integer(related="contract_id.total_amount", readonly=True)

    def get_related_instalment(self):
        self.ensure_one()
        installments = (self.env['line.contract.installment'].search([('contract_id', '=', self.contract_id.id)]))
        return installments

    def compute_installment_count(self):
        for item in self:
            item.installment_count = len(item.get_related_instalment())

    def _compute_invoice_count(self):
        for rec in self:
            rec.invoice_count = len(rec._get_related_invoices())

    def _compute_payment_count(self):
        for rec in self:
            rec.payment_count = rec._get_related_payment()

    def _get_related_invoices(self):
        self.ensure_one()
        invoices = self.env['account.move'].search([('contract_id', '=', self.contract_id.id)])
        return invoices

    def _get_related_payment(self):
        self.ensure_one()
        contract_payment = self.env['account.payment'].search([('contract_id', '=', self.contract_id.id)])
        invoices = self.env['account.move'].search([('contract_id', '=', self.contract_id.id)]).ids
        inv_payment = self.env['account.payment'].search(
            ['|', ('reconciled_invoice_ids', 'in', invoices), ('reconciled_bill_ids', 'in', invoices)])
        count = len(contract_payment) + len(inv_payment)
        return count

    def action_register(self):
        for rec in self:
            if rec.name == '/' or False:
                rec.name = self.env['ir.sequence'].next_by_code('re.sale')
            if rec.sell_method == 'property':
                rec.property_id.state = 'sold'
            else:
                rec.unit_id.state = 'sold'
            rec.write({'state': 'register'})
        return True

    def _create_contract(self):
        params = self.env['res.config.settings'].get_values()
        if not params['re_sale_journal_id']:
            raise ValidationError(_("Please Configure your Sales Journal in Setting first"))
        for record in self:
            contract = self.env['contract.contract'].sudo().create({
                'sale_id': record.id,
                'property_id': record.property_id.id,
                'unit_id': record.unit_id.id,
                'date_start': record.request_date,
                'type_of_contract': 'sales',
                'contract_type': 'sale',
                'name': record.partner_id.name + '-' + record.name,
                'partner_id': record.partner_id.id,
                'total_sale_amount': record.amount,
                'journal_id': params['re_sale_journal_id'],
            })
            record.contract_id = contract and contract.id
            if record.sell_method == 'property':
                record.property_id.contract_id = contract and contract.id
            else:
                record.unit_id.sale_contract_id = contract and contract.id
        return True

    def action_approve(self):
        #self._create_move_entry()
        for rec in self:
            rec._create_contract()
            if rec.sell_method == 'property':
                rec.property_id.state = 'sold'
            else:
                rec.unit_id.state = 'handover'
                rec.unit_id.handover_to_client_date = rec.handover_to_client_date
            email_template = self.env.ref('khawald_real_estate_marketing.template_sale_request_property')
            email_template.with_env(self.env).with_context(active_model=self._name).send_mail(rec.id)
            rec.state = 'approve'

    def action_show_invoices(self):
        self.ensure_one()
        tree_view_ref = (
            'account.move_supplier_tree'
            if self.contract_type == 'purchase'
            else 'account.move_tree_with_onboarding'
        )
        form_view_ref = (
            'account.move_supplier_form'
            if self.contract_type == 'purchase'
            else 'account.move_form'
        )
        tree_view = self.env.ref(tree_view_ref, raise_if_not_found=False)
        form_view = self.env.ref(form_view_ref, raise_if_not_found=False)
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Invoices',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('contract_id', '=', self.contract_id.id)],
            'context': {'default_contract_id': self.contract_id.id, 'create': False}
        }
        if tree_view and form_view:
            action['views'] = [(tree_view.id, 'tree'), (form_view.id, 'form')]
        return action

    def action_show_payment(self):
        self.ensure_one()
        invoices = self.env['account.move'].search([('contract_id', '=', self.contract_id.id)]).ids
        inv_payment = self.env['account.payment'].search(
            ['|', ('reconciled_invoice_ids', 'in', invoices), ('reconciled_bill_ids', 'in', invoices)]).ids
        tree_view_ref = (
            'account.view_account_supplier_payment_tree'
            if self.contract_type == 'purchase'
            else 'account.view_account_payment_tree'
        )
        form_view_ref = (
            'account.view_account_payment_form'
            if self.contract_type == 'purchase'
            else 'account.view_account_payment_form'
        )
        tree_view = self.env.ref(tree_view_ref, raise_if_not_found=False)
        form_view = self.env.ref(form_view_ref, raise_if_not_found=False)
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Payments',
            'res_model': 'account.payment',
            'context': {'default_contract_id': self.contract_id.id, 'create': False},
            'view_mode': 'tree,kanban,form,calendar,pivot,graph,activity',
            'domain': ['|', ('contract_id', '=', self.contract_id.id), ('id', 'in', inv_payment)],
        }
        if tree_view and form_view:
            action['views'] = [(tree_view.id, 'tree'), (form_view.id, 'form')]
        return action

    def action_show_installment(self):
        installment_ids = self.env['line.contract.installment'].search([('contract_id', '=', self.contract_id.id)])
        form_id = self.env.ref('contract.contract_installment_form_view').id
        tree_id = self.env.ref('contract.contract_installment_tree').id
        domain = [('id', 'in', installment_ids.ids)]
        return {
            'name': _('Contractor Payment'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'line.contract.installment',
            'views': [(tree_id, 'tree'), (form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': domain,
            'context': {'default_contract_id': self.contract_id.id}

        }

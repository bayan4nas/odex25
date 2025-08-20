# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError


class PurchaseOrderCustom(models.Model):
    _inherit = "purchase.order"

    def action_view_contract(self):
        formview_ref = self.env.ref('odex25_contract_saip.inherit_contract_contract_supplier_form_view', False)
        treeview_ref = self.env.ref('contract.contract_contract_tree_view', False)
        return {
            'name': _('Contract'),
            'domain': [('purchase_id', '=', self.id), ('contract_type', '=', 'purchase')],
            'view_mode': 'tree,form',
            'res_model': 'contract.contract',
            'view_id': False,
            'views': [(treeview_ref and treeview_ref.id or False, 'tree'),
                      (formview_ref and formview_ref.id or False, 'form')],
            'type': 'ir.actions.act_window',
        }


class AccountInvoiceCustom(models.Model):
    _inherit = 'account.move'

    coc_count = fields.Integer(string='Cocs', compute="_compute_coc_count")

    def _compute_coc_count(self):
        for rec in self:
            rec.coc_count = self.env['line.contract.installment'].search(
                [('invoice_id', '=', rec.id), ('state', '!=', 'cancel')]).coc_count

    def action_view_coc(self):
        installment_id = self.env['line.contract.installment'].search(
            [('invoice_id', '=', self.id), ('state', '!=', 'cancel')])
        return {
            'type': 'ir.actions.act_window',
            'name': _('CertificateOf Completion'),
            'res_model': 'line.contract.installment.coc',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': [('installment_id', '=', installment_id.id)],
            'context': {'create': False}
        }

    def action_post(self):
        if self.move_type == 'in_invoice':
            context = self.env.context
            po = self.env['line.contract.installment'].search([('invoice_id', '=', self.id), ('state', '!=', 'cancel')])

            if po and po.coc_ids.filtered(lambda coc: coc.coc_stage == 'befor_bill_valid' and coc.state != 'approve'):
                raise ValidationError(_("Sorry You cannot Validate Bill untill CoC Created and Approved."))
            else:
                return super(AccountInvoiceCustom, self).action_post()
        else:
            return super(AccountInvoiceCustom, self).action_post()

    def action_confirm(self):
        if self.move_type == 'in_invoice':
            context = self.env.context
            po = self.env['line.contract.installment'].search(
                [('invoice_id', '=', self.id), ('state', '!=', 'cancel')])
            if po and po.coc_ids.filtered(lambda coc: coc.coc_stage == 'befor_bill_valid' and coc.state != 'approve'):
                raise ValidationError(
                    _("Sorry You cannot Validate Bill untill CoC Created and Approved."))
            else:
                return super(AccountInvoiceCustom, self).action_confirm()
        else:
            return super(AccountInvoiceCustom, self).action_confirm()

    def action_register_payment(self):
        if self.move_type == 'in_invoice':
            context = self.env.context
            po = self.env['line.contract.installment'].search([('invoice_id', '=', self.id), ('state', '!=', 'cancel')])
            if po and po.coc_ids.filtered(lambda coc: coc.coc_stage == 'before_payment' and coc.state != 'approve'):
                raise ValidationError(
                    _("Sorry You cannot Pay For This Vendor untill CoC Created and Approved."))
            else:
                return super(AccountInvoiceCustom, self).action_register_payment()
        else:
            return super(AccountInvoiceCustom, self).action_register_payment()
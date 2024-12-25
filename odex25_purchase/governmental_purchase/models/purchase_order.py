# -*- coding: utf-8 -*-
from odoo.exceptions import  ValidationError
from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta


class PurchaseOrderCustom(models.Model):
    _inherit = "purchase.order"


    billed_amount = fields.Float(store=True, compute='_compute_amount')
    remaining_amount = fields.Float(store=True, compute='_compute_amount')

    @api.depends('invoice_ids','invoice_count')
    def _compute_amount(self):
        for order in self:
            billed_amount = 0.0
            for invoice in order.invoice_ids:
                billed_amount += invoice.amount_total

            currency = order.currency_id or order.partner_id.property_purchase_currency_id or \
                self.env.company.currency_id
            order.update({
                'billed_amount': currency.round(billed_amount),
                'remaining_amount': order.amount_total - billed_amount,
            })


    def action_recommend(self):
        for order in self:
            order.recommendation_order = True

    def button_confirm(self):
        # res = super(PurchaseOrderCustom, self).button_confirm()
        for order in self:
            if order.state not in ['draft', 'sent', 'sign','wait']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order._approval_allowed():
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
        return True

# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class SaleAdvancePaymentInv(models.TransientModel):
    _inherit = "sale.advance.payment.inv"


    advance_down_payment_method = fields.Selection([
        ('percentage', 'Down payment (percentage)'),
        ('fixed', 'Down payment (fixed amount)')
        ], string='Create Down Payment', default='percentage', required=True,
        help="A standard invoice is issued with all the order lines ready for invoicing, \
        according to their invoicing policy (based on ordered or delivered quantity).")

    @api.onchange('advance_down_payment_method')
    def onchange_advance_down_payment_method(self):
        if self.advance_down_payment_method:
            self.advance_payment_method = self.advance_down_payment_method

    def create_invoices(self):
        res = super(SaleAdvancePaymentInv, self).create_invoices()
        project_id = self.env['project.project'].browse(self._context.get('project_id'))
        project_id.is_down_payment = True
        project_id.update_invoices(is_down_payment=True)
        return res
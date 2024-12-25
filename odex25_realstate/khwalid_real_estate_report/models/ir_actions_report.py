# -*- coding: utf-8 -*-
##############################################################################
#
#   Expert (LCT, Life Connection Technology)
#    Copyright (C) 2021-2022 LCT
#
##############################################################################

from odoo import models, api, _
from odoo.exceptions import UserError

class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'


    def _render_qweb_pdf(self, res_ids=None, data=None):

        if self.model == 'property.reservation.payment' and res_ids:
            refund_reports = (self.env.ref('khwalid_real_estate_report.action_refund_request_pdf'))
            if self in refund_reports:
                reservation_payment_ids = self.env['property.reservation.payment'].browse(res_ids)
                if any(pay.state != 'return' for pay in reservation_payment_ids):
                    raise UserError(_("Printed only in state return."))

        if self.model == 'property.reservation' and res_ids:
            property_reservation_ids = self.env['property.reservation'].browse(res_ids)
            voucher_reports = (self.env.ref('khwalid_real_estate_report.action_receipt_voucher_pdf'))
            reservation_cheque_reports = (self.env.ref('khwalid_real_estate_report.action_property_reservation_cheque_pdf'))
            if self in voucher_reports:
                if any(prop.state != 'approve' for prop in property_reservation_ids):
                    raise UserError(_("Printed only in state approve reservation."))

            if self in reservation_cheque_reports:
                if any(prop.state == 'cancel' for prop in property_reservation_ids):
                    raise UserError(_("Printed only in state (draft, approve)."))

        if self.model == 're.sale' and res_ids:
            sale_ids = self.env['re.sale'].browse(res_ids)
            permission_empty_reports = (self.env.ref('khwalid_real_estate_report.action_permission_empty_unit'))
            cancel_sale_reports = (self.env.ref('khwalid_real_estate_report.action_cancel_sale_pdf'))
            receive_unit_reports = (self.env.ref('khwalid_real_estate_report.action_receive_unit_pdf'))
            customer_Identi_reports = (self.env.ref('khwalid_real_estate_report.action_customer_Identi_without_image_pdf'))


            if self in (permission_empty_reports, cancel_sale_reports, receive_unit_reports, customer_Identi_reports):
                if any(sale.sell_method != 'unit' for sale in sale_ids):
                    raise UserError(_("Only sell method in unit could be printed."))

            if self in permission_empty_reports:
                if any(sale.unit_id.state != 'emptied' and sale.state == 'approve' for sale in sale_ids):
                    raise UserError(_("Printed only in unit state emptied."))

            if self in cancel_sale_reports:
                if any(sale.state != 'cancel' for sale in sale_ids):
                    raise UserError(_("Printed only in state cancel."))

            if self in receive_unit_reports:
                if any(sale.state != 'approve' for sale in sale_ids):
                    raise UserError(_("Printed only in state approve."))

            if self in customer_Identi_reports:
                if any(sale.state not in ('register', 'approve') for sale in sale_ids):
                    raise UserError(_("Printed only in state (register, approve)."))


        return super()._render_qweb_pdf(res_ids=res_ids, data=data)

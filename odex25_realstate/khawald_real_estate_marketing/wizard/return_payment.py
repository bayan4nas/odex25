# -*- coding: utf-8 -*-
##############################################################################
#
#   Expert (LCT, Life Connection Technology)
#    Copyright (C) 2021-2022 LCT
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ReturnPayment(models.TransientModel):

	_name = 'return.payment'
	_description = "Return Payment"

	return_type = fields.Selection([('total','Total'), ('partial', 'Partial')], 'Return Type', default="total")
	return_amount = fields.Float('Amount')

	def _prepare_invoice_values(self, reservation_payment_id, journal_id, account_id):
		invoice_vals = {
			'ref': reservation_payment_id.name,
			'move_type': 'out_refund',
			'invoice_origin': reservation_payment_id.name,
			'narration': reservation_payment_id.name,
			'journal_id': journal_id,
			'partner_id': reservation_payment_id.partner_id.id,
			'invoice_line_ids': [(0, 0, {
				'name': reservation_payment_id.name + ' - ' + (str(reservation_payment_id.request_date)),
				'price_unit': reservation_payment_id.payment_amount if self.return_type == 'total' else self.return_amount,
				'quantity': 1.0,
				'account_id': account_id,
			})],
		}
		return invoice_vals

	def create_invoice(self, reservation_payment_id):
		params = self.env['res.config.settings'].get_values()
		if not params['re_sale_journal_id']:
			raise ValidationError(_("Please Configure your Journal in Setting first"))

		account_id = self.env['account.account'].search([
					('user_type_id', '=', self.env.ref('account.data_account_type_revenue').id),
					('company_id', '=', reservation_payment_id.reservation_id.company_id.id)])
		invoice_vals = self._prepare_invoice_values(reservation_payment_id, params['re_sale_journal_id'] or False, account_id)
		move_id = self.env['account.move'].sudo().create(invoice_vals).with_user(self.env.uid)
		move_id.action_post()
		return move_id

	def action_return(self):

		reservation_payment_id = self.env['property.reservation.payment'].browse(self.env.context.get('active_ids', False))
		move_id = self.create_invoice(reservation_payment_id)

		if self.return_amount > reservation_payment_id.payment_amount:
			raise ValidationError(_("Return amount must be less than or equal to down payment amount"))

		reservation_payment_id.return_amount = reservation_payment_id.payment_amount if self.return_type == 'total' else self.return_amount
		reservation_payment_id.move_id = move_id
		reservation_payment_id.state = 'return'


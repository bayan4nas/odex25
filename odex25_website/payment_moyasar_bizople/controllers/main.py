# -*- coding: utf-8 -*-
# Developed by Bizople Solutions Pvt. Ltd.
# See LICENSE file for full copyright and licensing details

from odoo import http
from odoo.http import request, content_disposition
import json
import moyasar
import logging

_logger = logging.getLogger(__name__)

class RedirectPayments(http.Controller):

    @http.route(['/.well-known/apple-developer-merchantid-domain-association'], type='http', auth="public", website=True, sitemap=False)
    def applepay_merchant_file(self,**post):
        ir_attach = request.env['ir.attachment'].sudo().search([('res_model','=','payment.acquirer')],order="id desc",limit=1)
        values={
            'file_data' : ir_attach.raw.decode('ascii'),
        }
        return request.make_response(ir_attach.raw.decode('ascii'), headers=[
            ('Content-Type', 'application/pdf'),
            ('Content-Disposition', content_disposition('apple-developer-merchantid-domain-association')),
        ])

    @http.route(['/payment-status-return'], type='http', auth="public",website=True, sitemap=False)
    def get_moyasar_payment_status(self,**post):
        status = post.get('status')
        payment_id = post.get('id')

        payment_aquirer = request.env['payment.acquirer'].sudo().search([('provider','=','moyasar')])
        moyasar.api_key = payment_aquirer.moyasar_secret_key
        payment = moyasar.Payment.fetch(str(payment_id))
        order = request.website.sale_get_order()
        _logger.info("****************Order Name*************: %s (%s)",order.name, order)
        _logger.info("***************Payment Transaction************** : %s",order.transaction_ids)
        _logger.info("***************** payment Response ****************** %s", payment)
        if status == 'paid':
            last_transaction = order.transaction_ids.search([],order="id desc",limit=1)
            data = {
                'reference': last_transaction.reference,
                'currency' : last_transaction.currency_id.name,
                'return_url' : '/payment/process',
                'amount': last_transaction.amount
            }
            request.env['payment.transaction'].sudo().form_feedback(data,"moyasar")
            tx = request.env['payment.transaction'].sudo().search([('reference', '=', data['reference'])], limit=1)
            tx.write({'moyasar_payment_id' : payment_id })
            tx._set_transaction_done()
            return request.redirect("/payment/process")
        else:
            payment_message = str(payment)
            payment_message_json = json.loads(payment_message)
            error_message = payment_message_json.get('source').get('message')
            value={
                'error' : error_message,
                'redirect' : '/shop/payment/validate',
            }
            last_transaction = order.transaction_ids.search([],order="id desc",limit=1)
            data = {
                'reference': last_transaction.reference,
                'currency' : last_transaction.currency_id.name,
                'return_url' : '/payment/process',
                'amount': last_transaction.amount
            }
            request.env['payment.transaction'].sudo().form_feedback(data,"moyasar")
            tx = request.env['payment.transaction'].sudo().search([('reference', '=', data['reference'])], limit=1)
            tx._set_transaction_cancel()
            return request.render('payment_moyasar_bizople.payment_error_temp',value)

    @http.route(['/get/moyasar/order'], type='json', auth="public", website=True)
    def savepayments(self, **post):
        if 'portal_order' in post:
            portal_order = post.get('portal_order')
            order = request.env['sale.order'].sudo().browse(int(portal_order))
        else:
            order = request.website.sudo().sale_get_order()
        
        amount= ''
        if order.amount_total:
            amount = order.amount_total
        base_url = request.env['ir.config_parameter'].sudo().get_param('web.base.url')
        
        payment_aquirer = request.env['payment.acquirer'].sudo().search([('provider','=','moyasar')])
        values = {
        'amount' : amount,
        'public_key' : payment_aquirer.moyasar_public_key,
        'callback_url' : base_url,
        'currency' : order.currency_id.name,
        'description' : order.name,
        }
        return values
#-*- coding: utf-8 -*-
from odoo import models, fields , api


class ProductInherit(models.Model):
    _inherit = 'product.product'

    quick_donation = fields.Boolean(string='Quick donation')
    zakat_product = fields.Boolean(string='Zakat Product')
    tags_ids = fields.Many2many('website.product.tag',string='Product Tags')

class ProductTempInherit(models.Model):
    _inherit = 'product.template'

    bank_id = fields.Many2many('res.bank',string='Bank Account')
    tags_ids = fields.Many2many('website.product.tag',string='Product Tags')

class WebsiteProductTag(models.Model):
    _name = "website.product.tag"

    name = fields.Char("Name", required=True)
    code = fields.Char("Code", required=True)

class PaymentMethods(models.Model):
    _name = "payment.method"

    method_id = fields.Integer(string="ID",required=True)
    name = fields.Char("Name", required=True)

class SaleInherit(models.Model):
    _inherit = "sale.order"

    quick_donation = fields.Boolean(string='Quick donation')
    payment_methods = fields.Many2one("payment.method")

    # @api.multi
    def force_quotation_send(self):
        for order in self:
            email_act = order.action_quotation_send()
            # order.partner_id.send_sms_notification("توجد فرصة تطوعية مناسبة", order.partner_id.phone)
            mail = self.env['mail.mail'].create({
                'body_html': "تم إهداء هذا المنتج لكم ",
                'subject': "إهداء",
                'email_to': order.partner_id.email,
            })
            mail.send()
            if email_act and email_act.get('context'):
                email_ctx = email_act['context']
                email_ctx.update(default_email_from=order.company_id.email)
                order.with_context(email_ctx).message_post_with_template(email_ctx.get('default_template_id'))
        return True
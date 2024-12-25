# -*- coding: utf-8 -*-
# Developed by Bizople Solutions Pvt. Ltd.
# See LICENSE file for full copyright and licensing details

from odoo import _, api, models, fields

class PaymentTransactionMoyasar(models.Model):
    _inherit = 'payment.transaction'

    moyasar_payment_id = fields.Char("Moyasar Id")
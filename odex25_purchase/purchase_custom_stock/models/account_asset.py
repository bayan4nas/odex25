# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class AccountAssetAsset(models.Model):
    _inherit = 'account.asset'

    purchase_request_id = fields.Many2one('purchase.request', string="Purchase Request", readonly=True, copy=False)

#-*- coding: utf-8 -*-
from odoo import models, fields, api, _, exceptions
from odoo import SUPERUSER_ID


# from datetime import datetime , date

class EmployeeCustodyLine(models.Model):
    _inherit = 'asset.custody.line'

    purchase_request_id = fields.Many2one(comodel_name='purchase.request', string="Purchase Request")

    @api.onchange('asset_id')
    def _onchange_asset_id(self):
        if not self.purchase_request_id:
            return

        selected_asset_ids = self.purchase_request_id.asset_request_line_ids.filtered(
            lambda l: l != self
        ).mapped('asset_id.id')

        domain = [
            ('id', 'not in', selected_asset_ids),
            ('status', 'in', ['new', 'available']),
            ('asset_type', '=', 'purchase'),
            ('product_id', 'in', self.purchase_request_id.line_ids.mapped('product_id.id'))
        ]

        return {'domain': {'asset_id': domain}}
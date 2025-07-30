# -*- coding: utf-8 -*-
from odoo import models, fields, api, _, exceptions
from odoo.exceptions import UserError, ValidationError, Warning


class AccountAssetOperation(models.Model):
    _inherit = 'account.asset.operation'

    purchase_request_id = fields.Many2one(comodel_name='purchase.request', string="Source Document")

    @api.model
    def create(self, vals):
        asset_id = vals.get('asset_id')
        operation_type = vals.get('type')

        if asset_id and operation_type == 'release':
            existing_releases = self.search([
                ('asset_id', '=', asset_id),
                ('type', '=', 'release'),
                ('state', 'not in', ['done', 'cancel'])
            ])
            if existing_releases:
                raise ValidationError(_('An asset release operation already exists for this asset.'))

        if not vals.get('purchase_request_id') and asset_id:
            asset = self.env['account.asset'].browse(asset_id)
            if asset.purchase_request_id:
                vals['purchase_request_id'] = asset.purchase_request_id.id

        return super(AccountAssetOperation, self).create(vals)

    def write(self, vals):
        res = super(AccountAssetOperation, self).write(vals)

        for operation in self:
            if not operation.asset_id or not operation.purchase_request_id:
                continue
            custody_line = self.env['asset.custody.line'].search([
                ('purchase_request_id', '=', operation.purchase_request_id.id),
                ('asset_id', '=', operation.asset_id.id)
            ], limit=1)
            if 'return_date' in vals and vals.get('return_date') is not None:
                if operation.type == 'assignment' and operation.state != 'cancel' and custody_line:
                    custody_line.return_date = operation.return_date
            if vals.get('state') == 'cancel' and custody_line:
                custody_line.return_date = False

            if vals.get('state') == 'done':
                if operation.type == 'assignment':
                    operation.asset_id.write({
                        'purchase_request_id': operation.purchase_request_id.id,
                    })
                elif operation.type == 'release':
                    if operation.asset_id.purchase_request_id == operation.purchase_request_id:
                        operation.asset_id.write({
                            'purchase_request_id': False,
                        })

        return res

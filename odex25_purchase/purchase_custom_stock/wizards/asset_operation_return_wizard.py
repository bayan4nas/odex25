# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AssetOperationReturnWizard(models.TransientModel):
    _name = 'asset.operation.return.wizard'
    _description = 'Asset Operation Return Wizard'

    purchase_request_id = fields.Many2one('purchase.request', string='Purchase Request', required=True)
    operation_ids = fields.One2many('asset.operation.return.line', 'wizard_id', string='Return Operations')

    def action_confirm(self):
        if not self.operation_ids:
            raise ValidationError(_("Please select at least one asset to return"))

        purchase_request = self.purchase_request_id
        operation_vals = []

        for line in self.operation_ids:
            operation_vals.append({
                'name': line.asset_id.name,
                'date': purchase_request.date or fields.Date.today(),
                'asset_id': line.asset_id.id,
                'type': 'release',
                'custody_type': line.custody_type,
                'custody_period': line.custody_period,
                'state': 'draft',
                'user_id': line.user_id.id,
                'current_employee_id': purchase_request.employee_id.id,
                'new_employee_id': purchase_request.employee_id.id,
                'current_department_id': purchase_request.department_id.id,
                'purchase_request_id': purchase_request.id,
            })
        self.env['account.asset.operation'].create(operation_vals)

        return {'type': 'ir.actions.act_window_close'}


class AssetOperationReturnLine(models.TransientModel):
    _name = 'asset.operation.return.line'
    _description = 'Asset Operation Return Line'

    wizard_id = fields.Many2one('asset.operation.return.wizard', ondelete='cascade')
    asset_id = fields.Many2one('account.asset', string='Asset', required=True)
    name = fields.Char(default='/')
    date = fields.Date()
    type = fields.Selection(selection=[('assignment', 'Assignment'), ('release', 'Release'),
                                       ('transfer', 'Transfer')])
    custody_type = fields.Selection([('personal', 'Personal'), ('general', 'General')], string='Custody Type')
    custody_period = fields.Selection([('temporary', 'Temporary'), ('permanent', 'Permanent')], string='Custody Period')
    state = fields.Selection(
        [('draft', 'Draft'), ('submit', 'Submit'), ('done', 'Done'), ('pending', 'Pending'), ('cancel', 'Cancel')],
        default='draft')
    user_id = fields.Many2one('res.users', string='Responsible')
    current_employee_id = fields.Many2one('hr.employee', string='Employee')
    new_employee_id = fields.Many2one('hr.employee', string='Employee')
    current_department_id = fields.Many2one('hr.department', string='Department')
    new_department_id = fields.Many2one('hr.department', string='Department')
    purchase_request_id = fields.Many2one('purchase.request')

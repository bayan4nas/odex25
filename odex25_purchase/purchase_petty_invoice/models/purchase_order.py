# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"
    is_petty_paid = fields.Boolean(string='Paid by Petty Cash', default=False, copy=False)
    petty_employee_id = fields.Many2one('hr.employee', string='Petty Cashier', copy=False)



class AccountMove(models.Model):
    _inherit = 'account.move'


    @api.onchange('purchase_vendor_bill_id', 'purchase_id')
    def _onchange_purchase_auto_complete(self):
        super()._onchange_purchase_auto_complete()
        if self.purchase_id:
            self.is_petty_paid = self.purchase_id.is_petty_paid
            self.petty_employee_id = self.purchase_id.petty_employee_id
        else:
            self.is_petty_paid = False
            self.petty_employee_id = False

    @api.model_create_multi
    def create(self, vals_list):
        moves = super(AccountMove, self).create(vals_list)
        for move in moves:
            if move.purchase_id:
                move.is_petty_paid = move.purchase_id.is_petty_paid
                move.petty_employee_id = move.purchase_id.petty_employee_id.id
        return moves

    def write(self, vals):
        if vals.get('purchase_id'):
            po = self.env['purchase.order'].browse(vals['purchase_id'])
            vals['is_petty_paid'] = po.is_petty_paid
            vals['petty_employee_id'] = po.petty_employee_id.id
        super(AccountMove, self).write(vals)

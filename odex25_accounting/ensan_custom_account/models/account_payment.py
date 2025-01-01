# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields , api , _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import format_date, formatLang



class AccountPayment(models.Model):
    _inherit = "account.payment"

    partner_type = fields.Selection([
        ('customer', 'Customer'),
        ('supplier', 'Vendor'),
        ('GL', 'GL'),  
    ], default='customer', tracking=True, required=True)
    destination_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Destination Account',
        store=True, readonly=False,
        compute='_compute_destination_account_id',
        domain="[('user_type_id.type', 'in', ('receivable', 'payable','view','liquidity')), ('company_id', '=', company_id)]",
        check_company=True)

    def _prepare_payment_display_name(self):
        res = super()._prepare_payment_display_name()
        '''
        Hook method for inherit
        When you want to set a new name for payment, you can extend this method
        '''
        res['outbound-GL'] = _('Disbursement Directly GL')
        res['inbound-GL'] = _('Collect Directly GL')
        return res

    @api.onchange('partner_type','partner_id','payment_type')
    def get_destination_account_id(self):
        if self.partner_type == 'customer':
            domain = [('user_type_id.type', 'in', ('receivable', 'payable')), ('company_id', '=', self.company_id.id)]
        elif self.partner_type == 'supplier':
            domain = [('user_type_id.type', 'in', ('receivable', 'payable')), ('company_id', '=', self.company_id.id)]
        elif self.partner_type == 'GL':
            domain = [('user_type_id.type', 'not in', ('receivable', 'payable','view','liquidity')), ('company_id', '=', self.company_id.id)]
        else:
            domain = [('user_type_id.type', 'not in', ('receivable', 'payable')), ('company_id', '=', self.company_id.id)]
        return {'domain': {'destination_account_id': domain}}

    @api.depends('journal_id', 'partner_id', 'partner_type', 'is_internal_transfer')
    def _compute_destination_account_id(self):
        for rec in self:
            if rec.destination_account_id and rec.partner_type == 'GL':
                return
        super()._compute_destination_account_id()
        for pay in self:
            if pay.partner_type == 'GL' and not pay.destination_account_id:
                domain = [('user_type_id.type', 'not in', ('receivable', 'payable','view','liquidity')), ('company_id', '=', self.company_id.id)]
                pay.destination_account_id = self.env['account.account'].search(domain, limit=1)
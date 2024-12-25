# -*- coding: utf-8 -*-
from odoo import api, models, fields, _
from odoo.addons import decimal_precision as dp
import logging

_logger = logging.getLogger(__name__)


class AccountInvoice(models.Model):
    _inherit = "account.move"

    operation_type = fields.Selection([
        ('in_kind_donation', 'In-Kind Donation'),
        ('financial_donation', 'Financial Donation'),
        ('subscription', 'Subscription'),
        ('sponsorship', 'Sponsorship'),
        ('financial_gift', 'Financial Gift'),
        ('need_contribution', 'Needs Contribution')],
        string='Operation Type',
    )
    operation_id = fields.Integer(readonly=True)


class TakafulAccountMove(models.Model):
    _name = 'takaful.account.move'

    name = fields.Char(string='Order Name')
    remote_id = fields.Char(string='Order Number')
    partner_id = fields.Many2one('res.partner', string='Customer')

    name_of = fields.Char(string='Customer Name', readonly=True)
    email = fields.Char(string='Customer Email', readonly=True)
    note = fields.Text(string='Comment')

    amount = fields.Float(string='Amount With Vat')
    operation_type = fields.Selection([
        ('in_kind_donation', 'In-Kind Donation'),
        ('financial_donation', 'Financial Donation'),
        ('subscription', 'Subscription'),
        ('sponsorship', 'Sponsorship'),
        ('financial_gift', 'Financial Gift'),
        ('need_contribution', 'Needs Contribution')],
        string='Operation Type',
    )
    operation_id = fields.Integer(readonly=True)
    type = fields.Selection(selection=[
        ('card', _('Credit Card')),
        ('transfer', _('Bank Transfer')),
    ], string='Type')
    date = fields.Date('Date', default=fields.Date.context_today)
    qty_ordered = fields.Float(string='Qty Ordered',default=1)
    state = fields.Selection(selection=[
        ('initiated', _('Initiated')),
        ('failed', _('Failed')),
        ('rejected', _('Rejected')),
        ('paid', _('Paid')),
    ], default='paid', string='Status')
    transfer_id = fields.Many2one('takaful.bank.transfer.payment', string='Transfer')
    amount_without_vat = fields.Float(string='Amount Without Vat', compute='_get_vat_amount')
    tax_amount = fields.Float(string='Vat', compute='_get_vat_amount',digits= dp.get_precision('Product Price'))

    # @api.one
    @api.depends('amount', 'type')
    def _get_vat_amount(self):
        for rec in self:
            if not rec.type:
                tax_percent = float(
                    self.env['ir.config_parameter'].sudo().get_param('vat_default_percent', default=0.0))
                rec.amount_without_vat = rec.amount/(1+(tax_percent/100))
                rec.tax_amount = round(rec.amount - rec.amount_without_vat,2)
            else:
                rec.amount_without_vat = rec.amount
                rec.tax_amount = 0

    def get_company(self):
        return self.env.user.company_id


TakafulAccountMove()

"""
vals = {
                'name': _('Server Update'),
                'partner_id': request.env.user.partner_id.id,
                'amount': diff,
                'qty_ordered': num_months,
                'operation_type': 'credit',
                'state': 'paid',
            }
            request.env['takaful.account.move'].sudo().create(vals)
"""
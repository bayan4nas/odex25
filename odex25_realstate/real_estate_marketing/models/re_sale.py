# -*- coding: utf-8 -*-
##############################################################################
#
#   Expert (LCT, Life Connection Technology)
#    Copyright (C) 2021-2022 LCT
#
##############################################################################

from odoo.exceptions import ValidationError, UserError
from odoo import models, fields, api, _
from datetime import date


class ReSale(models.Model):
    _name = "re.sale"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Property Sales"

    name = fields.Char(string='Reference', default='/')
    request_date = fields.Date('Date', index=True, default=fields.Date.context_today)
    sell_method = fields.Selection([('property', 'By Property'), ('unit', 'By Unit')], string="Sell Method", default='property')
    property_id = fields.Many2one('internal.property', string="Property")
    total_property_size = fields.Float(string='Size', digits=(16, 2))
    unit_id = fields.Many2one('re.unit', string="Unit")
    city_id = fields.Many2one('re.city', string="City")
    district_id = fields.Many2one('district', string="District")
    user_id = fields.Many2one('res.users', string="Responsible", default=lambda self: self.env.user)
    partner_id = fields.Many2one('res.partner', string="Client")
    phone = fields.Char(string='Phone', related='partner_id.phone')
    mobile = fields.Char(string='Mobile', related='partner_id.mobile')
    notes = fields.Text(string='Notes')
    state = fields.Selection([('draft', 'Draft'),
                              ('register', 'Registered'),
                              ('approve', 'Approved'),
                              ('cancel', 'Cancel'),
                              ], string="Status", default='draft')
    move_id = fields.Many2one('account.move', string="Customer Invoice")
    amount = fields.Float(string='Amount', digits=(16, 2))
    amount_per_meter = fields.Float(string='Amount Per Meter', digits=(16, 2), compute='_get_amount_per_meter', store=True)
    commission_type = fields.Selection([('fix', 'Fixed'), ('percentage', 'Percentage')], string='Commission type')
    commission_percentage = fields.Float(string='Commission Percentage', digits=(16, 2))
    commission_amount = fields.Float(string='Commission', digits=(16, 2))
    is_intermediary = fields.Boolean(string='Is Intermediary?')
    intermediary_id = fields.Many2one('res.partner', string="Intermediary")
    intermediary_commission_type = fields.Selection([('fix', 'Fixed'), ('percentage', 'Percentage')], string='Intermediary Commission type')
    intermediary_commission_percentage = fields.Float(string='Intermediary Commission Percentage', digits=(16, 2))
    intermediary_commission_amount = fields.Float(string='Intermediary Commission', digits=(16, 2))
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)
    marketer_commission_type = fields.Selection([('fix', 'Fixed'), ('percentage', 'Percentage')], string='Marketer Commission Type')
    marketer_commission_percentage = fields.Float(string='Marketer Commission Percentage')
    marketer_commission_amount = fields.Float(string='Marketer Commission')
    included_by_commission_type = fields.Selection([('fix', 'Fixed'), ('percentage', 'Percentage')], string='Included By Commission Type')
    included_by_commission_percentage = fields.Float(string='Included By Commission Percentage')
    included_by_commission_amount = fields.Float(string='Included By Commission')
    cusomer_confession = fields.Html('Customer Confession')

    @api.model
    @api.depends('amount', 'total_property_size')
    def _get_amount_per_meter(self):
        for rec in self:
            if rec.total_property_size and rec.amount > 0:
                self.amount_per_meter = round(rec.amount/rec.total_property_size, 2)

    @api.onchange('amount')
    def _onchange_amount(self):
        self.commission_amount = 0.0
        self.marketer_commission_amount = 0.0
        self.included_by_commission_amount = 0.0
        self.intermediary_commission_amount = 0.0

    @api.onchange('commission_percentage')
    def on_change_commission_percentage(self):
        for rec in self:
            if rec.commission_percentage > 0 and rec.amount > 0:
                rec.commission_amount = rec.amount * rec.commission_percentage / 100

    @api.onchange('marketer_commission_percentage')
    def on_change_marketer_commission_percentage(self):
        for rec in self:
            if rec.marketer_commission_percentage > 0 and rec.amount > 0:
                rec.marketer_commission_amount = rec.amount * rec.marketer_commission_percentage / 100

    @api.onchange('included_by_commission_percentage')
    def on_change_included_by_commission_percentage(self):
        for rec in self:
            if rec.included_by_commission_percentage > 0 and rec.amount > 0:
                rec.included_by_commission_amount = rec.amount * rec.included_by_commission_percentage / 100

    @api.onchange('intermediary_commission_percentage')
    def on_change_intermediary_commission_percentage(self):
        for rec in self:
            if rec.intermediary_commission_percentage > 0 and rec.amount > 0:
                rec.intermediary_commission_amount = rec.amount * rec.intermediary_commission_percentage / 100

    def action_register(self):
        for rec in self:
            if rec.name == '/' or False:
                rec.name = self.env['ir.sequence'].next_by_code('re.sale')
            if rec.sell_method == 'property':
                rec.property_id.state = 'reserve'
            else:
                rec.unit_id.state = 'reserved'
            rec.write({'state': 'register'})

    def _prepare_invoice_values(self, payment, journal_id, amount, account_id):
        invoice_vals = {
            'ref': payment.name,
            'move_type': 'out_invoice',
            'invoice_origin': payment.name,
            'narration': payment.name,
            'journal_id': journal_id,
            'partner_id': payment.partner_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': payment.name + ' - ' + str(payment.request_date),
                'price_unit': amount,
                'quantity': 1.0,
                'account_id': account_id,
                # 'tax_ids': [(6, 0, [payment.tax_id.id])],
            })],
        }
        return invoice_vals

    def _create_move_entry(self):
        params = self.env['res.config.settings'].get_values()
        if not params['re_sale_journal_id']:
            raise ValidationError(_("Please Configure your Sales Journal in Setting first"))
        account_id = self.env['account.account'].search([
                        ('user_type_id', '=', self.env.ref('account.data_account_type_revenue').id),
                        ('company_id', '=', self.company_id.id)])
        for rec in self:
            invoice_vals = self._prepare_invoice_values(rec, params['re_sale_journal_id'] or False, rec.amount, account_id)
            invoice = self.env['account.move'].sudo().create(invoice_vals).with_user(self.env.uid)
            rec.move_id = invoice and invoice.id

        # move_obj = self.env['account.move']
        # move_line_obj = self.env['account.move.line']
        # params = self.env['res.config.settings'].get_values()
        # if not params['re_sale_journal_id']:
        #     raise ValidationError(_("Please Configure your Sales Journal in Setting first"))
        # for rec in self:
        #     move_values = {
        #         'name': self.name,
        #         'move_type': 'out_invoice',
        #         'invoice_date': date.today(),
        #         'invoice_date_due': date.today(),
        #         'partner_id': self.partner_id and self.partner_id.id,
        #         'journal_id': params['re_sale_journal_id'] or False
        #     }
        #     ctx = {
        #         'move_type': 'out_invoice',
        #     }
        #     move_id = move_obj.with_context(ctx).create(move_values)
        #     move_lines = move_line_obj.create([
        #         {
        #             'name': self.name,
        #             'move_id': move_id.id,
        #             'account_id': self.partner_id.property_account_receivable_id.id or False,
        #             'debit': self.amount or 0,
        #             'credit': 0,
        #         },
        #         {
        #             'name': self.name,
        #             'move_id': move_id.id,
        #             'account_id':self.env['account.account'].search([
        #                 ('user_type_id', '=', self.env.ref('account.data_account_type_revenue').id),
        #                 ('company_id', '=', self.company_id.id)
        #             ], limit=1).id,
        #             'debit': 0,
        #             'credit': self.amount or 0,
        #         }
        #     ])

    def action_approve(self):
        self._create_move_entry()
        for rec in self:
            if rec.sell_method == 'property':
                rec.property_id.state = 'sold'
            else:
                rec.unit_id.state = 'sold'
            rec.state = 'approve'

    def action_draft(self):
        for rec in self:
            if rec.sell_method == 'property':
                rec.property_id.state = 'approve'
            else:
                rec.unit_id.state = 'available'
        self.write({'state': 'draft'})

    def action_cancel(self):
        for rec in self:
            if rec.sell_method == 'property':
                rec.property_id.state = 'approve'
            else:
                rec.unit_id.state = 'available'
        self.write({'state': 'cancel'})

    @api.onchange('sell_method')
    def sell_method_onchange(self):
        self.property_id = False
        self.unit_id = False
        self.district_id = False
        self.city_id = False

    @api.onchange('property_id')
    def property_onchange(self):
        if self.sell_method == 'property':
            self.city_id = self.property_id.city_id and self.property_id.city_id.id or False
            self.district_id = self.property_id.district_id and self.property_id.district_id.id or False
            self.total_property_size = self.property_id.property_space or 0.0
            self.amount = self.property_id.rent_price or 0.0

    @api.onchange('unit_id')
    def unit_onchange(self):
        if self.sell_method == 'unit':
            self.city_id = self.unit_id.city_id and self.unit_id.city_id.id or False
            self.district_id = self.unit_id.district_id and self.unit_id.district_id.id or False
            self.total_property_size = self.unit_id.space or 0.0
            self.amount = self.unit_id.rent_price or 0.0




# -*- coding: utf-8 -*-
##############################################################################
#
#   Expert (LCT, Life Connection Technology)
#    Copyright (C) 2021-2022 LCT
#
##############################################################################

from odoo.exceptions import ValidationError
from odoo import models, fields, api, _
from datetime import datetime, date


class PropertyReservation(models.Model):
    _name = "property.reservation"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Property Reservation"

    name = fields.Char(string='Reference', default='/')
    request_date = fields.Date('Order Date', index=True, default=fields.Date.context_today)
    reserve_type = fields.Selection([('with', 'With Down Payment'), ('without', 'Without Down Payment')], string="Reserve Type", default='with')
    title = fields.Selection([('mr', 'Mr'), ('mrs', 'Mrs')], string="Title", default='mr')
    partner_id = fields.Many2one('res.partner', string="Client")
    client_check_number = fields.Char(string='Client check number')
    phone = fields.Char(string='Phone', related='partner_id.phone')
    mobile = fields.Char(string='Mobile', related='partner_id.mobile')
    date_of_birth = fields.Date(string='Date Of Birth', related='partner_id.date_of_birth')
    country_id = fields.Many2one('res.country', string='Nationality', related='partner_id.country_id')
    email = fields.Char(string='Email', related='partner_id.email')
    street = fields.Char(string="Street Name", related='partner_id.street')
    identification_type = fields.Selection(related="partner_id.identification_type", string='Identification Type')
    identification_number = fields.Char(related="partner_id.identification_number", string='Identification Number')
    search_type = fields.Selection([('property', 'Property'), ('unit', 'Unit')], string="Property Type", default='unit')
    property_id = fields.Many2one('internal.property', string="Property", tracking=True)
    unit_id = fields.Many2one('re.unit', string="Units", tracking=True)
    project_id = fields.Many2one('project.project', string='Project')
    marketer_user_id = fields.Many2one('res.users', string="Marketer", default=lambda self: self.env.user)
    payment_type = fields.Selection([('cash', 'Cash'), ('bank', 'Bank')], string="Payment Type", default='cash')
    bank_id = fields.Many2one('res.bank', string="Bank")
    payment_amount = fields.Float(string='Down Payment Amount', digits=(16, 2))
    user_id = fields.Many2one('res.users', string="Responsible", default=lambda self: self.env.user)
    tax_exemption = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Tax Exemption", default='no')
    price = fields.Float(string='Property Price', digits=(16, 2), compute='get_price', store=True)
    discount = fields.Float(string='Discount', digits=(16, 2))
    final_price = fields.Float(string='Price', digits=(16, 2))
    total_price = fields.Float(string='Final Price', digits=(16, 2), compute='get_total_price', store=True)
    agent_id = fields.Many2one('res.partner', string="Agent")
    end_date = fields.Date('Reserve End Date',)
    state = fields.Selection([('draft', 'Draft'),
                              ('approve', 'Reservation Done'),
                              ('cancel', 'Cancel'),
                              ], string="Status", default='draft')
    total_days = fields.Integer(string="Reserve Days to end", compute="compute_days", store=True)
    client_check = fields.Binary("Client Check", attachment=True)
    receive_check = fields.Binary("Receive Check", attachment=True)
    payment_id = fields.Many2one('property.reservation.payment', string="Down Payment ID")
    sale_contract_id = fields.Many2one('re.sale', string="Sale Request")
    sale_creation = fields.Boolean(compute='get_sale_creation')
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.user.company_id)
    move_id = fields.Many2one('account.move', string="Down Payment Invoice")

    @api.depends('state', 'sale_contract_id')
    def get_sale_creation(self):
        for rec in self:
            if rec.state == 'approve' and not rec.sale_contract_id:
                rec.sale_creation = True
            else:
                rec.sale_creation = False

    @api.depends('request_date', 'end_date')
    def compute_days(self):
        for rec in self:
            days = 0
            today_date = date.today()
            if rec.request_date and rec.end_date:
                d1 = datetime.strptime(str(today_date), '%Y-%m-%d')
                d2 = datetime.strptime(str(rec.end_date), '%Y-%m-%d')
                daysDiff = (d2 - d1).days
                if daysDiff >= 0:
                    days = int(daysDiff) + 1
            rec.total_days = days

    @api.constrains('end_date')
    def _check_dates_constraint(self):
        today_date = date.today()
        for rec in self:
            d1 = datetime.strptime(str(today_date), '%Y-%m-%d')
            d2 = datetime.strptime(str(rec.end_date), '%Y-%m-%d')
            if d2 < d1:
                raise ValidationError(_('The Reserve end date cannot be before Today date.'))

    @api.depends('search_type', 'property_id', 'unit_id')
    def get_price(self):
        for rec in self:
            if rec.search_type == 'property' and rec.property_id:
                rec.price = rec.property_id.rent_price
            elif rec.search_type == 'unit' and rec.unit_id:
                rec.price = rec.unit_id.rent_price
            else:
                rec.price = 0.0

    @api.depends('discount', 'final_price')
    def get_total_price(self):
        for rec in self:
            rec.total_price = rec.final_price - rec.discount or 0.0


    def _prepare_invoice_values(self, journal_id, account_id):
        invoice_vals = {
            'ref': self.name,
            'move_type': 'out_invoice',
            'invoice_origin': self.name,
            'narration': self.name,
            'journal_id': journal_id,
            'partner_id': self.partner_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': self.name + ' - ' + str(self.request_date),
                'price_unit': self.payment_amount,
                'quantity': 1.0,
                'account_id': account_id,
            })],
        }
        return invoice_vals

    def create_invoice(self):
        params = self.env['res.config.settings'].get_values()
        if not params['re_sale_journal_id']:
            raise ValidationError(_("Please Configure your Journal in Setting first"))
        
        account_id = self.env['account.account'].search([
                        ('user_type_id', '=', self.env.ref('account.data_account_type_revenue').id),
                        ('company_id', '=', self.company_id.id)])
        invoice_vals = self._prepare_invoice_values(params['re_sale_journal_id'] or False, account_id)
        move_id = self.env['account.move'].sudo().create(invoice_vals).with_user(self.env.uid)
        move_id.action_post()
        return move_id


    def action_approve(self):
        for rec in self:
            if rec.name == '/' or False:
                rec.name = self.env['ir.sequence'].next_by_code('property.reservation')
            email_template = self.env.ref('khawald_real_estate_marketing.template_property_reservation')
            email_template.with_env(self.env).with_context(active_model=self._name).send_mail(rec.id)
            if rec.reserve_type == 'with':
                payment_values = {}
                payment_seq = self.env['ir.sequence'].next_by_code('property.reservation.payment')
                payment_values ={
                    'name': rec.unit_id.name + '-' + payment_seq,
                    'reservation_id': rec.id,
                    'unit_id': rec.unit_id.id,
                    'bank_id': rec.bank_id.id,
                    'partner_id': rec.partner_id.id,
                    'client_check_number': rec.client_check_number,
                    'payment_amount': rec.payment_amount,
                    'end_date': rec.end_date,
                    'state': 'approve',
                    'client_check': rec.client_check,
                    'receive_check': rec.receive_check,
                }
                payment_id = self.env['property.reservation.payment'].sudo().create(payment_values)
                move_id = rec.create_invoice()
                rec.move_id = move_id
                rec.unit_id.state = 'with'
                rec.payment_id = payment_id and payment_id.id
            else:
                rec.unit_id.state = 'without'
            rec.state = 'approve'

    def action_cancel(self):
        for rec in self:
            rec.unit_id.state = 'available'
            rec.state = 'cancel'
            rec.move_id.button_cancel()

    def action_create_sale(self):
        vals = {}
        sale_obj = self.env['re.sale']
        for record in self:
            # if record.project_id.state not in ['','']:
            #     raise ValidationError(_("Please first Register Your Request"
            #                                        "Then You can Proceed"))
            vals = {
                'name': '/',
                'sell_method': self.search_type,
                'property_id': record.property_id and record.property_id.id or False,
                'state': 'draft',
                'reservation_id': record.id,
                'total_property_size': record.unit_id.space,
                'amount': record.total_price - record.payment_amount,
                'unit_id': record.unit_id and record.unit_id.id or False,
                'partner_id': record.partner_id and record.partner_id.id or False,
            }
            sale_id = sale_obj.create(vals)
            if sale_id:
                sale_id.action_register()
                record.sale_contract_id = sale_id.id
        return True


class PropertyReservationPayment(models.Model):
    _name = "property.reservation.payment"

    name = fields.Char(string='Reference', default='/')
    reservation_id = fields.Many2one('property.reservation', string="Property Reservation")
    unit_id = fields.Many2one('re.unit', string="Units", tracking=True)
    bank_id = fields.Many2one('res.bank', string="Bank")
    partner_id = fields.Many2one('res.partner', string="Client")
    client_check_number = fields.Char(string='Client check number')
    payment_amount = fields.Float(string='Down Payment Amount', digits=(16, 2))
    end_date = fields.Date('Reserve End Date',)
    request_date = fields.Date('Order Date', index=True, default=fields.Date.context_today)
    delivery_date = fields.Date('Delivery Date', index=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('approve', 'Reservation Done'),
                              ('return', 'Down Payment Returned'),
                              ], string="Status", default='draft')
    client_check = fields.Binary("Client Check", attachment=True)
    receive_check = fields.Binary("Receive Check", attachment=True)
    delivery_check = fields.Binary("Delivery Check", attachment=True)
    return_amount = fields.Float('Return Amount')
    move_id = fields.Many2one('account.move', string="Return Invoice")

    def action_return(self):
        for rec in self:
            rec.state = 'return'










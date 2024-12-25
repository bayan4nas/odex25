# -*- coding: utf-8 -*-
import base64
import re
import calendar

import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import exception_to_unicode
from odoo import models, fields, api, exceptions, tools, _
from odoo.addons.property_management.models import amount_to_text_ar
from odoo.exceptions import UserError
from datetime import datetime, timedelta


class RentPayment(models.Model):
    _name = "rent.payment"
    _description = "Rental Contract Payment"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id desc"

    code = fields.Char(string="Sequence")
    collected_from_company = fields.Boolean(string="Is Payment Collected from Company")
    commission_amount = fields.Float(string="Commission Amount", store=True, compute='_compute_commission_amount')
    name = fields.Char(string="Description")
    contract_id = fields.Many2one('rental.contract', string="Rental Contract")
    renter_id = fields.Many2one('res.partner', string="Renter", related='contract_id.partner_id', readonly=1)

    investor_id = fields.Many2one('res.partner', string="Investor", related="contract_id.property_id.owner_id",
                                  store=True)
    partner_id = fields.Many2one('res.partner', string="Customer", related="contract_id.partner_id", store=True)
    property_id = fields.Many2one('internal.property', string="Property", related="contract_id.property_id", store=True)
    unit_ids = fields.Many2many('re.unit', string="Unit/Units", related="contract_id.unit_ids")
    user_id = fields.Many2one('res.users', string="Responsible")
    company_id = fields.Many2one('res.company', string="Company")
    due_date = fields.Date(string="Due Date")
    paid_date = fields.Date(string="Paid Date", )
    payment_method = fields.Selection([('check', 'Bank Check'),
                                       ('cash', 'Cash'),
                                       ('transfer', 'Transfer')], string="Payment Method", default='transfer')
    amount = fields.Float(string="Amount")
    water_cost = fields.Float(string="Water Cost")
    service_cost = fields.Float(string="Service Cost")
    service_note = fields.Char(string="Service Note", related='contract_id.service_note')
    electricity_cost = fields.Float(string="Electricity Cost", related='contract_id.electricity_cost')
    sanitation_cost = fields.Float('Sanitation Cost', related='contract_id.sanitation_cost')

    profit = fields.Float(string="Profit")
    tax_id = fields.Many2one('account.tax', string="Tax")
    untaxed_amount = fields.Float(string="Untaxed Amount", compute="get_untaxed_amount", store=True)
    # tax_amount = fields.Float(string="Tax Amount", compute="get_tax_amount", store=True)
    tax_amount = fields.Float(string="Tax Amount")
    total_amount = fields.Float(string="Total Amount", compute="get_total_amount")
    paid = fields.Boolean(string="Paid", compute='get_invoice_state', default=False)
    amount_in_word = fields.Char(string="Amount In Word", compute="get_amount_in_word")
    state = fields.Selection([('draft', 'Not Due'),
                              ('due', 'Due'),
                              ('invoice', 'Invoice'),
                              ('paid', 'Paid'),
                              ('cancel', 'Canceled')], string="Status", default='draft')
    invoice_id = fields.Many2one('account.move', string="Invoice", readonly=1)
    invoice_commission_id = fields.Many2one('account.move', string="Invoice Commission", readonly=1)
    note = fields.Text(string="Note")

    @api.depends('total_amount')
    def _compute_commission_amount(self):
        for record in self:
            commission_percentage = self.env['ir.config_parameter'].sudo().get_param(
                'property_management.commission_percentage')
            record.commission_amount = record.total_amount * (
                    commission_percentage / 100) if commission_percentage else 0

    @api.depends('contract_id')
    def _compute_renter(self):
        for rec in self:
            if rec.contract_id:
                rec.renter_id = rec.contract_id.partner_id.id
            if rec.invoice_id and rec.invoice_id.payment_state in ['paid', 'in_payment']:
                rec.write({'state': 'paid', 'paid_date': rec.invoice_id.payment_id.date})
                payment_obj = self.env['account.payment'].search([('ref', '=', rec.invoice_id.name)], limit=1)
                rec.paid_date = payment_obj.date

    @api.depends('invoice_id')
    def _compute_payment(self):
        for rec in self:
            if rec.invoice_id and rec.invoice_id.payment_state in ['paid', 'in_payment']:
                rec.write({'state': 'paid', 'paid_date': rec.invoice_id.payment_id.date})
                payment_obj = self.env['account.payment'].search([('ref', '=', rec.invoice_id.name)], limit=1)
                rec.paid_date = payment_obj.date

    def read(self, records):
        res = super(RentPayment, self).read(records)
        for rec in self:
            if rec.invoice_id.payment_state in ['paid', 'in_payment']:
                rec.write({'state': 'paid'})
                payment_obj = self.env['account.payment'].search([('ref', '=', rec.invoice_id.name)], limit=1)
                rec.paid_date = payment_obj.date
        return res

    @api.depends('invoice_id', 'invoice_id.state', 'invoice_id.payment_state', 'invoice_id.amount_residual')
    def get_invoice_state(self):
        self.paid = False
        for rec in self:
            if rec.invoice_id:
                if rec.invoice_id.amount_residual == 0.0:
                    rec.paid = True
                if rec.invoice_id.payment_state in ['paid', 'in_payment']:
                    rec.write({'state': 'paid'})
                    payment_obj = self.env['account.payment'].search([('ref', '=', rec.invoice_id.name)], limit=1)
                    rec.paid_date = payment_obj.date

    def _prepare_invoice_values(self, payment, amount):

        self.renter_id.property_account_receivable_id = payment.contract_id.debit_account_id.id
        unit_name = self.unit_ids[0].name if self.unit_ids else ''  # Check if unit_ids is not empty
        line_invoice = []
        line_journal = []

        if payment.amount > 0.00:
            line_invoice.append((0, 0, {
                'name': _('Reant Amount ') + ' - ' + str(payment.contract_id.name or '') + ' - ' + str(
                    self.property_id.name or '') + ' - ' + unit_name + ' - ' + str(self.name or '') + ' - ' + str(
                    payment.code or '') + ' - ' + str(payment.due_date or ''),
                'quantity': 1.0,
                'price_unit': self.amount,
                'account_id': payment.contract_id.revenue_account_id.id,
                'analytic_account_id': payment.property_id.account_analy_id.id if payment.property_id.account_analy_id else False,
                'tax_ids': [(6, 0, [payment.tax_id.id])] if payment.tax_id else False,  # Assigning tax_id to tax_ids
            }))
        if payment.water_cost > 0.00:
            line_invoice.append((0, 0, {
                'name': _('Water Cost ') + ' - ' + str(payment.contract_id.name or '') + ' - ' + str(
                    self.property_id.name or '') + ' - ' + unit_name + ' - ' + str(self.name or '') + ' - ' + str(
                    payment.code or '') + ' - ' + str(payment.due_date or ''),
                'price_unit': self.water_cost,
                'quantity': 1.0,
                'account_id': payment.contract_id.revenue_account_id.id,
                'analytic_account_id': payment.property_id.account_analy_id.id if payment.property_id.account_analy_id else False,
                'tax_ids': [(6, 0, [payment.tax_id.id])] if payment.tax_id else False,  # Assigning tax_id to tax_ids
            }), )
        if payment.service_cost > 0.00:
            line_invoice.append((0, 0, {
                'name': _('Serviecs Cost') + ' - ' + str(payment.contract_id.name or '') + ' - ' + str(
                    self.property_id.name or '') + ' - ' + unit_name + ' - ' + str(self.name or '') + ' - ' + str(
                    payment.code or '') + ' - ' + str(payment.due_date or ''),
                'price_unit': self.service_cost,
                'quantity': 1.0,
                'analytic_account_id': payment.property_id.account_analy_id.id if payment.property_id.account_analy_id else False,
                'account_id': payment.contract_id.revenue_account_id.id,
                'tax_ids': [(6, 0, [payment.tax_id.id])] if payment.tax_id else False,  # Assigning tax_id to tax_ids
            }))
        if payment.electricity_cost > 0.00:
                line_invoice.append((0, 0, {
                    'name': _('Electricity Cost') + ' - ' + str(payment.contract_id.name or '') + ' - ' + str(
                        self.property_id.name or '') + ' - ' + unit_name + ' - ' + str(self.name or '') + ' - ' + str(
                        payment.code or '') + ' - ' + str(payment.due_date or ''),
                    'price_unit': self.electricity_cost,
                    'quantity': 1.0,
                    'analytic_account_id': payment.property_id.account_analy_id.id if payment.property_id.account_analy_id else False,
                    'account_id': payment.contract_id.revenue_account_id.id,
                    'tax_ids': [(6, 0, [payment.tax_id.id])] if payment.tax_id else False,  # Assigning tax_id to tax_ids
                }))
        if payment.sanitation_cost > 0.00:
                line_invoice.append((0, 0, {
                    'name': _('Sanitation Cost') + ' - ' + str(payment.contract_id.name or '') + ' - ' + str(
                        self.property_id.name or '') + ' - ' + unit_name + ' - ' + str(self.name or '') + ' - ' + str(
                        payment.code or '') + ' - ' + str(payment.due_date or ''),
                    'price_unit': self.sanitation_cost,
                    'quantity': 1.0,
                    'analytic_account_id': payment.property_id.account_analy_id.id if payment.property_id.account_analy_id else False,
                    'account_id': payment.contract_id.revenue_account_id.id,
                    'tax_ids': [(6, 0, [payment.tax_id.id])] if payment.tax_id else False,  # Assigning tax_id to tax_ids
                }))
        if payment.amount == 0.00 and payment.service_cost == 0.00 and payment.water_cost == 0.00:
            line_invoice.append((0, 0, {
                'name': self.name + ' - ' + str(payment.contract_id.name or '') + ' - ' + str(
                    self.property_id.name or '') + ' - ' + unit_name + ' - ' + str(self.name or '') + ' - ' + str(
                    payment.code or '') + ' - ' + str(payment.due_date or ''),
                'price_unit': self.total_amount,
                'quantity': 1.0,
                'analytic_account_id': payment.property_id.account_analy_id.id if payment.property_id.account_analy_id else False,
                'account_id': payment.contract_id.revenue_account_id.id,
                'tax_ids': [(6, 0, [payment.tax_id.id])] if payment.tax_id else False,  # Assigning tax_id to tax_ids
            }))

            # line_journal.append((0, 0, {
            #         'account_id': payment.contract_id.revenue_account_id.id,
            #         'debit': 0.0,
            #         'credit': amount,
            #         'name': payment.contract_id.name + ' - ' + payment.contract_id.seq + ' - ' + str(payment.contract_id.date),
            #         'quantity': 1
            #     }))
            # line_journal.append((0, 0, {
            #         'account_id': payment.contract_id.debit_account_id.id,
            #         'debit': amount,
            #         'credit': 0.0,
            #         'quantity': 1
            #     }))

        invoice_vals = {
            'ref': payment.name,
            'move_type': 'out_invoice',
            'invoice_origin': payment.code,
            'invoice_user_id': payment.user_id.id,
            'narration': payment.note,
            'partner_id': payment.contract_id.partner_id.id,
            'invoice_line_ids': line_invoice,

            # 'tax_ids': [(6, 0, [payment.tax_id.id])],
        }
        return invoice_vals

    def action_invoice(self):
        if not self.contract_id.accrued_account_id:
            raise exceptions.ValidationError(
                _("Kindly, Contact Your Account Manager to set Income Account in contract account page"))
        invoice_vals = self._prepare_invoice_values(self, self.total_amount)
        invoice = self.env['account.move'].sudo().create(invoice_vals).with_user(self.env.uid)
        # Get the ID of the second line
        # line_id = invoice.invoice_line_ids[1].id
        # commands = [(2, line_id, 0)]
        # invoice.write({'invoice_line_ids': commands})

        self.invoice_id = invoice.id
        self.write({'state': 'invoice'})

    @api.depends('total_amount')
    def get_amount_in_word(self):
        self.amount_in_word = amount_to_text_ar.amount_to_text(
            self.total_amount, 'ar')

    def action_cancel(self):
        if self.state != 'due':
            self.write(({'state': 'cancel'}))
        elif self.state == 'due':
            raise exceptions.ValidationError(_('Cannot Cancel This Payment Because it Due'))

    def create_vendor_bill_for_payments(self):
        active_ids = self._context.get('active_ids', [])
        # action = self.env['rent.payment'].browse(context.get('active_ids', []))
        payments_to_invoice = self.env['rent.payment'].sudo().browse(active_ids).filtered(
            lambda p: p.state == 'paid' and p.collected_from_company and not p.invoice_commission_id)
        vendor_id = int(self.env['ir.config_parameter'].sudo().get_param('property_management.collecting_company_id'))
        account_id = int(self.env['ir.config_parameter'].sudo().get_param('property_management.commission_account_id'))
        total_commission_amount = sum(payments_to_invoice.mapped('commission_amount'))
        today_date = datetime.today().strftime('%Y-%m-%d')
        name = (_('Commission for selected payments'))

        # Ensure vendor and account are valid
        if not vendor_id or not account_id:
            raise UserError(_("Vendor or Account not configured properly in settings."))

        if payments_to_invoice:
            vendor_bill = self.env['account.move'].sudo().create({
                'move_type': 'in_invoice',
                'invoice_date': today_date,  # Set the invoice date,
                'partner_id': vendor_id,
                'invoice_line_ids': [(0, 0, {
                    'name': name + ' - ' + str(today_date),
                    'quantity': 1,
                    'price_unit': total_commission_amount,
                    'account_id': account_id
                })],
            })
        for payment in payments_to_invoice:
            payment.invoice_commission_id = vendor_bill.id

    def action_validate2(self):
        for record in self:
            if record.contract_id.state == 'confirm':
                rent_payment = [line for line in record.contract_id.rent_payment_ids.filtered(
                    lambda payment: payment.due_date < record.due_date and
                                    (not payment.invoice_id or
                                     all(invoice.state == 'draft' for invoice in payment.invoice_id))
                )]
                # if len(rent_payment):
                #     raise exceptions.ValidationError(
                #         _("You must validate the previous rent payment and complete the process"))
                if record.code == '/' or not record.code:
                    code = self.env['ir.sequence'].next_by_code('rent.payment') or '/'
                    record.write({'code': code})
                record.write({"state": 'due'})
            else:
                raise exceptions.ValidationError(_("You Must Confirm Contract First"))

    def _check_due_payments(self):
        payments = self.search([('state', '=', 'draft'), ('due_date', '<=', fields.Date.today())])
        for payment in payments:
            if payment.contract_id.state == 'confirm':
                payment.write({'state': 'due'})
            if payment.code == '/' or not payment.code:
                code = self.env['ir.sequence'].next_by_code('rent.payment') or '/'
                payment.write({'code': code})

    def _send_payment_notifications(self):
        today = fields.Date.today()
        next_week = today + timedelta(days=7)

        payments_today = self.search([('due_date', '=', today), ('state', '=', 'draft')])
        payments_next_week = self.search([('due_date', '=', next_week), ('state', '=', 'draft')])

        template_today = self.env.ref('property_management.email_template_due_today')
        template_next_week = self.env.ref('property_management.email_template_due_next_week')
        date_deadline = fields.Date.today()
        note = _("Please Chech the Due Date in rent")
        summary = _("Due Date Rent")

        for payment in payments_today:
            email_list = [payment.renter_id.email, payment.user_id.email]
            email_to = ','.join(email_list)
            payment.message_post_with_template(template_today.id)
            if template_today:
                template_today.send_mail(payment.id, force_send=True, raise_exception=True,
                                         email_values={'email_to': email_to})
            payment.sudo().activity_schedule(
                'mail.mail_activity_data_todo', date_deadline,
                note=note,
                user_id=payment.user_id.id,
                res_id=payment.id,
                summary=summary
            )
            payment.sudo().activity_schedule(
                'mail.mail_activity_data_todo', date_deadline,
                note=note,
                user_id=payment.partner_id.user_id.id,
                res_id=payment.id,
                summary=summary
            )
            # إرسال إشعار إلى المستأجر والمستخدمين
            # يمكنك استخدام notification module للإشعارات أو mail.activity

        for payment in payments_next_week:
            email_list = [payment.renter_id.email, payment.user_id.email]
            email_to = ','.join(email_list)
            payment.message_post_with_template(template_next_week.id)
            if template_next_week:
                template_next_week.send_mail(payment.id, force_send=True, raise_exception=True,
                                             email_values={'email_to': email_to})
            payment.sudo().activity_schedule(
                'mail.mail_activity_data_todo', date_deadline,
                note=note,
                user_id=payment.user_id.id,
                res_id=payment.id,
                summary=summary
            )
            payment.sudo().activity_schedule(
                'mail.mail_activity_data_todo', date_deadline,
                note=note,
                user_id=payment.partner_id.user_id.id,
                res_id=payment.id,
                summary=summary
            )
        return True

    def action_validate(self):
        for record in self:
            if record.contract_id.state == 'confirm':
                rent_payment = [line for line in record.contract_id.rent_payment_ids.filtered(
                    lambda payment: payment.due_date < record.due_date and
                                    (not payment.invoice_id or
                                     all(invoice.state == 'draft' for invoice in payment.invoice_id))
                )]
                if len(rent_payment):
                    pass
                    # raise exceptions.ValidationError(
                    #     _("You must validate the previous rent payment and complete the process"))
                if record.code == '/' or not record.code:
                    code = self.env['ir.sequence'].next_by_code('rent.payment') or '/'
                    record.write({'code': code})
                record.write({"state": 'due'})
            else:
                raise exceptions.ValidationError(_("You Must Confirm Contract First"))

    # @api.depends('untaxed_amount', 'tax_id', 'tax_id.amount')
    # def get_tax_amount(self):
    #     for rec in self:
    #         tax_value = rec.tax_id.amount / 100
    #         rec.tax_amount = rec.untaxed_amount * tax_value

    @api.depends('amount', 'water_cost', 'service_cost', 'tax_id')
    def get_untaxed_amount(self):
        for rec in self:
            rec.untaxed_amount = round(
                rec.amount + rec.water_cost + rec.service_cost + rec.electricity_cost + rec.sanitation_cost, 2)
            rec.tax_amount = round(rec.tax_id.amount / 100 * rec.amount, 2)

    @api.depends('amount', 'water_cost', 'service_cost', 'tax_id')
    def get_total_amount(self):
        for rec in self:
            rec.total_amount = round(rec.untaxed_amount + rec.tax_amount, 2)
            commission_percentage = float(
                self.env['ir.config_parameter'].sudo().get_param('property_management.commission_percentage'))
            rec.commission_amount = rec.total_amount * (commission_percentage) if commission_percentage else 0

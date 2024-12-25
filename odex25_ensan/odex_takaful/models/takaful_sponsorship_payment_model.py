# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from dateutil.parser import parse
from odoo.exceptions import UserError,ValidationError, Warning

import logging

_logger = logging.getLogger(__name__)


class SponsorshipPayment(models.Model):
    _name = 'sponsorship.payment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Payments  for Sponsorship system in Takaful project"
    _rec_name = 'code'
    _order = 'date desc'
   
    sponsorship_id = fields.Many2one(
        'takaful.sponsorship',
        string='Sponsorship'
    )
     
    sponsor_id = fields.Many2one(
        'takaful.sponsor',
        string='Sponsor Name'
    )
    code = fields.Char(string="Sponsorship Number", related="sponsorship_id.code",store=True)

    payment_month_number = fields.Integer(string="Sponsorships Number To Pay")
    month_amount = fields.Float(string="Sponsorship Amount", related="sponsorship_id.contribution_value",store=True, readonly=True)
    amount = fields.Float(string="Total Amount", compute="get_amount_month", store=True)
    iban = fields.Char(string='IBAN / Account Number', tracking=True)
    transfer_receipt = fields.Binary(string='Transfer Receipt')
    bank_id = fields.Many2one('res.bank', string="Bank Name")
    has_bank_account = fields.Boolean(string="Has Another Account?")
    payment_method = fields.Selection(string='Method Of Payment',
        store=True,
        related='sponsorship_id.payment_method',
        readonly=True)

    user_id = fields.Many2one('res.users',string="Issued By", default=lambda self: self.env.user)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('financial', 'Financial'),
        ('paid', 'Paid'),
    ], string='state', default="draft", tracking=True)

    date = fields.Date('Date', readonly=True,default=fields.Date.today())
    invoice_ids = fields.Many2many('account.move', string="Invoices")
    is_invoiced = fields.Boolean(string='Is Invoiced?', compute='check_is_invoiced')

    def check_is_invoiced(self):
        for rec in self:
            if rec.invoice_ids and rec.state == "financial":
                total_paid = 0
                for invoice in rec.invoice_ids:
                    if invoice.state == 'paid':
                        payments = self.env['account.payment'].sudo().search([('invoice_ids', 'in', [invoice.id])])
                        # if len(payments) > 0:
                        for payment in payments:
                            total_paid += payment.amount

                if total_paid >0 and total_paid >= rec.amount:
                    rec.is_invoiced = True
                    rec.state = "paid"
                else:
                    rec.is_invoiced = False

            elif rec.invoice_ids and rec.state == "paid":
                rec.is_invoiced = True

            else:
                rec.is_invoiced = False

    @api.onchange('sponsor_id')
    def onchange_sponsor_id(self):
        res = {}
        sponsorships = self.env['takaful.sponsorship'].sudo().search([('sponsor_id', '=', self.sponsor_id.id)])
        sponsorships_ids = []
        for record in sponsorships:
            sponsorships_ids.append(record.id)

        res['domain'] = {'sponsorship_id': [('id', 'in', sponsorships_ids)]}
        return res
        
    @api.onchange('has_bank_account', 'payment_method')
    def onchange_bank_account(self):
        for rec in self:
            if rec.payment_method and rec.payment_method != "cash" and not rec.has_bank_account:
                self.bank_id = self.sponsor_id.bank_id.id
                self.iban = self.sponsor_id.iban
            else:
                self.bank_id = None
                self.iban = ''

    # @api.constrains('month_amount')
    # def check_month_amount(self):
    #     if int(self.month_amount) <= 0:
    #         raise ValidationError(
    #             _(u'Month Amount Is Invalid'))

    @api.constrains('payment_month_number')
    def check_payment_month_number(self):
        if int(self.month_amount) <= 0:
            raise ValidationError(
                _(u'Payment Month Number should be at least for one month'))

    @api.depends('month_amount', 'payment_month_number')
    def get_amount_month(self):
        for rec in self:
            rec.amount = rec.month_amount * rec.payment_month_number

    def action_pay(self):
        count = 0
        invoices = [] 
        if self.sponsorship_id.state in ['confirmed','wait_pay','progress' , 'to_cancel']:
            if self.sponsorship_id.next_due_date:
                next_date = parse(str(self.sponsorship_id.next_due_date)).date()
                while (count < self.payment_month_number):
                    count +=1
                    invoice_id = self.sponsorship_id.sudo().create_next_invoice(next_date)
                    invoices.append(invoice_id.id)
                    try:
                        next_date = next_date.replace(month=(next_date.month +1))
                    except Exception as  e:
                        next_date = next_date.replace(year=(next_date.year +1), month=1)
        
        # Update invoices Ids
        for _id in invoices:
            self.write({'invoice_ids': [(4, _id)]})

        self.state = 'financial'
       
    # @api.multi
    def open_account_invoice_action(self):
        """Open Sponsorship Payments Entries"""
        domain = []
        if self.invoice_ids:
            domain = [('id', 'in', self.invoice_ids.ids)]
        
        if self.is_invoiced is True:
            self.state ="paid"

        context = dict(self.env.context or {})
        context["create"] = False
        context["edit"] = False
        flags = {'initial_mode': 'readonly'} # default is 'edit'
        return {
            'name': _('Financial'),
            'domain': domain,
            'view_type': 'form',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
            'flags': flags,
            'context': context,
        }


    

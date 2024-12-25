# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime, date, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from ..utils import formats
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse

import logging

_logger = logging.getLogger(__name__)


class MonthPayment(models.Model):
    _name = 'month.payment'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name")
    code = fields.Char(string="Code", copy=False, readonly=True, default=lambda x: _('New'))
    journal_id = fields.Many2one('account.journal')
    account_id = fields.Many2one('account.account', )
    date = fields.Date(string="Date", default=fields.Datetime.now)
    amount = fields.Float(string="Total Amount", compute='_compute_payment_total', store=True)
    count = fields.Integer(string="Count", compute='_compute_payment_total', store=True)
    user_id = fields.Many2one('res.users', string="Issued By", default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.user.company_id)
    line_ids = fields.One2many('month.payment.line', 'month_id', string="Lines")
    due_invoice_ids = fields.Many2many('grant.benefit.invoice', string="Due Payments")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('create', 'Create Lines'),
        ('approve', 'Approved'),
        ('submit', 'Submit To Pay'),
        ('paid', 'Paid'),
        ('refused', 'Refused'),
        ('cancel', 'Cancel'),
    ], string='state', default="draft", tracking=True)
 
    month_code = fields.Char(string="Month Code", store=True, compute='_compute_payment_month_code')
    entry_id = fields.Many2one('account.move', string="Entry")

    @api.depends('line_ids')
    def _compute_payment_total(self):
        for rec in self:
            if rec.line_ids:
                rec.amount = sum(rec.line_ids.mapped('amount'))
                rec.count = len(rec.line_ids)
            else:
                rec.amount = 0
                rec.count = 0

    @api.onchange('name', 'date')
    def _compute_payment_name(self):
        if self.date and not self.name:
            date = parse(str(self.date)).date()
            self.name = _('Sponsorship Due Payments') + ' {}'.format(date.strftime("%m-%Y"))

    def _compute_payment_month_code(self):
        """ Extract month code from date """   
        for rec in self: 
            if rec.date:
                date = parse(str(rec.date)).date()
                rec.month_code = date.strftime("%Y_%m")

    @api.model
    def create(self, vals):
        res = super(MonthPayment, self).create(vals)
        if not res.code or res.code == _('New'):
            res.code = self.env['ir.sequence'].sudo().next_by_code('month.payment.sequence') or _('New')
        return res

    def open_payments(self):
        return {
            'name': _('Payments'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(self.env.ref(
                'odex_takaful.benefit_month_payment_line_tree').id, 'tree'),
                      (self.env.ref('odex_takaful.benefit_month_payment_line_form').id, 'form')],
            'res_model': 'month.payment.line',
            'type': 'ir.actions.act_window',
            'domain': "[('month_id','=',%s)]" % (self.id),
            'target': 'current',
        }

    def action_create_lines(self):
        if not self.line_ids:
            due_invoices = self.env['grant.benefit.invoice'].sudo().search([
                ('operation_type',  '=', 'sponsorship'),
                ('due_code',  '=', self.month_code),
                ('is_recorded',  '=', False),
            ])

            for rec in due_invoices:
                if rec.benefit_target == "person" and len(rec.benefit_ids) ==1:
                    line = self.env['month.payment.line'].sudo().create({
                        'month_id': self.id,
                        'sponsorship_id': rec.operation_id,
                        'benefit_id': rec.benefit_ids[0].id,
                        'responsible_id': rec.benefit_ids[0].responsible_id.id if rec.benefit_ids[0].responsible_id else False,
                        'partner_id': rec.benefit_ids[0].responsible_id.partner_id.id if rec.benefit_ids[0].responsible_id else False,
                        'amount': rec.paid_amount,
                        'date': datetime.now(),
                    })          
                else:
                    amount = (rec.paid_amount / len(rec.benefit_ids))
                    now = datetime.now()
                    for ben in rec.benefit_ids:
                        line = self.env['month.payment.line'].sudo().create({
                            'month_id': self.id,
                            'sponsorship_id': rec.operation_id,
                            'benefit_id': ben.id,
                            'responsible_id': ben.responsible_id.id if ben.responsible_id else False,
                            'partner_id': ben.responsible_id.partner_id.id if ben.responsible_id else False,
                            'amount': amount,
                            'date': now,
                        })

                self.write({'due_invoice_ids': [(4, rec.id)]})

                # Now true for rec.is_recorded
                # rec.is_recorded = True
                       
            self.state = 'create'


    def create_entry(self):
        move_name = self.name + ' - %s' % self.code
        move_id = self.env['account.move'].sudo().create({
            'name': move_name,
            'journal_id': self.company_id.kafala_benefit_journal_id.id,
            'ref': self.code})
        move_line = []
        move_line.append({
            'debit': self.amount,
            'credit': 0.0,
            'account_id': self.company_id.kafala_benefit_account_id.id,
        })
        move_line.append({
            'debit': 0.0,
            'credit': self.amount,
            'account_id': self.company_id.kafala_benefit_bank_account_id.id,
        })

        move_id.write({'line_ids': [(0, 0, line) for line in move_line]})
        move_id.post()
        self.entry_id = move_id.id

        for inv in self.due_invoice_ids:
            inv.is_recorded = True

    def action_notify(self):
        if self.state == 'submit':
            payment = self.env['month.payment.line'].search([('month_id', '=', self.id)])
            for i in payment:
                if i.responsible_id.email:
                    email_from = self.env.user.company_id.email
                    company_name = self.env.user.company_id.name

                    template_id = self.env.ref('odex_takaful.push_notification_email_template').id
                    context = {
                       'email_from': email_from,
                       'email_to': i.responsible_id.email,
                       'partner_name': i.responsible_id.name,
                       'body': _("You have recieved money in tolal of %s in your account.") % str(i.amount),
                       'title': _("Recieving Money"),
                       'company_name': company_name
                    }

                    # Start to SEND Email
                    self.env['mail.template'].browse(template_id).with_context(context).send_mail(self.id, force_send=True, raise_exception=False)
                                            
            self.state = 'paid'
        else:
            raise ValidationError(
                _(u' No benefits for pay'))

    def action_approve(self):
        if self.line_ids:
            self.sudo().create_entry()
            self.state = 'approve'

    def action_refuse(self):
        self.state = 'refused'

    def action_submit(self):
        self.state = 'submit'

    def action_cancel(self):
        for i in self.line_ids:
            i.sudo().unlink()
        self.state = 'cancel'


class MonthPaymentLine(models.Model):
    _name = 'month.payment.line'
    _rec_name = 'month_id'

    month_id = fields.Many2one('month.payment')
    sponsorship_id = fields.Many2one("takaful.sponsorship", string="Sponsorship")
    s_code = fields.Char(string="Sponsorship Number", related="sponsorship_id.code",store=True)
    sponsor_id = fields.Many2one(string="The Sponsor", related="sponsorship_id.sponsor_id",store=True)
    benefit_id = fields.Many2one('grant.benefit', string="Benefit")
    benefit_type = fields.Selection(string="Benefit Type", related="benefit_id.benefit_type",store=True)
    responsible_id = fields.Many2one('grant.benefit', string="Responsible Benefit")
    partner_id = fields.Many2one('res.partner', string="Responsible Partner")
    date = fields.Date(string="Date")
    state = fields.Selection(related="month_id.state", store=True)
    code = fields.Char(related="month_id.code", store=True)
    amount = fields.Float(string="Amount")

"""
@api.model
    def payment_cron(self):
        payment = self.env['month.payment'].search([('state', '=', 'approve'), ('date', '=', str(datetime.now().date())),
                                                   ('line_ids', '=', False)], limit=1)
        if payment:
            payment.action_create_lines()

def create_records(self, benefits, support=False):
        if benefits:
            self.sudo().is_benefits = True
            for p in benefits:
                p.get_amount_month()
                amount = float("{:.2f}".format(p.amount * self.amount))
                if self.is_appendix:
                    payment = self.env['month.payment.line'].search([('month_id', '=', self.parent_id.id)])
                    for i in payment:
                        amount += i.amount
                line = self.env['month.payment.line'].sudo().create({
                    'month_id': self.id,
                    'benefit_id': p.id,
                    'responsible_id': p.id if not support else p.parent_id.id,
                    'amount': amount,
                    'date': datetime.now(),
                })
                if self.is_appendix:

                    payment = self.env['month.payment.line'].search([('month_id', '=', self.id)])
                    self.amount = 0.0
                    for pay in payment:
                        self.amount += pay.amount

def action_create_lines(self):
        if not self.line_ids:
            if not self.parent_id:
                benefit = self.env['grant.benefit'].search([('state', '=', 'approve')])
                benefits = benefit.filtered(lambda r: r.benefit_type in ['benefit', 'support'])
                self.create_records(benefits)
                parent = benefit.filtered(lambda r: r.benefit_type == 'parent')
                self.get_child(parent)
                self.get_child(benefits)
            else:
                ben = self.parent_id.line_ids.mapped('benefit_id')
                benefit = self.env['grant.benefit'].search([('state', '=', 'approve')])
                benefits = benefit.filtered(lambda r: r.benefit_type in ['benefit', 'support'] and r.id not in ben.ids)
                self.create_records(benefits)
                parent = benefit.filtered(lambda r: r.benefit_type == 'parent')
                self.get_child(parent, sub=ben.ids)
                self.get_child(benefits, sub=ben.ids)
            self.state = 'create'
"""
# -*- coding: utf-8 -*-
##############################################################################
#
#   Expert (LCT, Life Connection Technology)
#    Copyright (C) 2021-2022 LCT
#
##############################################################################

from datetime import datetime, date
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProjectPaymentRequest(models.Model):
    _name = 'project.payment.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    def create(self, vals):
        if vals.get('sequence') == '/':
            if vals.get('type') == 'subcontractor':
                vals['sequence'] = self.env['ir.sequence'].next_by_code('project.payment.request.subcontract') or ('/')
            else :
                vals['sequence'] = self.env['ir.sequence'].next_by_code('project.payment.request.eng') or ('/')
        result = super(ProjectPaymentRequest, self).create(vals)
        return result

    @api.returns('self', lambda value: value.id)
    def copy(self, default=None):
        raise UserError(_('You cannot duplicate project payment.'))

    def unlink(self):
        raise UserError(_('You cannot Delete project payment.'))


    @api.model
    def name_get(self):
        """
        :return:
        """
        res = []
        for rec in self:
            order_name = rec.sequence
            if order_name:
                order_name = order_name + ' |' + str(rec.name)
            res.append((rec.id, order_name))
        return res

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=80):
        args = args or []
        records = self.search(
            ['|', ('sequence', operator, name), ('name', operator, name)] + args,
            limit=limit)
        return records.name_get()

    sequence = fields.Char(string='Sequence', default='/')
    name = fields.Char(string='Description')
    project_id = fields.Many2one('project.project', string='Project')
    date = fields.Date(string='Date')
    delivery_date = fields.Date(string='Delivery Data')
    type = fields.Selection([('subcontractor', 'Subcontractor'),
                             ('eng_office', 'Engineering Office')], string='Payment Type', default='eng_office')
    state = fields.Selection([('draft', 'Draft'),
                              ('submit', 'Submit'),
                              ('approve', 'To Pay'),
                              ('done', 'Paid'),
                              ('cancel', 'Cancel')], string='State', default='draft')
    partner_id = fields.Many2one('res.partner', string='Partner')
    amount = fields.Float(string='Amount',digits=(16, 2))
    eng_office_installment_id = fields.Many2one('engineering.office.line',string='Engineering Office Installment')
    subcontractor_line_id = fields.Many2one('subcontractor.work.line',string='Contractor Installment')
    account_move_id = fields.Many2one('account.move',string='Account Move')
    penalty_amount =  fields.Float(string="Penalty Amount")
    flag = fields.Boolean(string="Flag")
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)

    def _get_delay_details(self):
        amount = 0.0
        for record in self:
            if record.subcontractor_line_id:
                for line in record.subcontractor_line_id:
                    amount += line.penalty_amount
            record.penalty_amount = amount

    def expect_penalty(self):
        self.penalty_amount = 0
        self.flag = True

    def submit(self):
        self._get_delay_details()
        self.state = 'submit'

    def cancel(self):
        if self.eng_office_installment_id :
            self.eng_office_installment_id.payment_id = False
        self.state = 'cancel'

    def compute_days(self, date,date_to):
        if date and date_to:
            d1 = datetime.strptime(str(date), '%Y-%m-%d')
            d2 = datetime.strptime(str(date_to), '%Y-%m-%d')
            daysDiff = (d1 - d2).days
            days = int(daysDiff) + 1
            return days

    def _prepare_invoice_values(self, payment, installment_type, project_payment_id,name_spec,account_id, amount):
        invoice_vals = {
            'ref': payment.name,
            'move_type': 'in_invoice',
            'invoice_origin': payment.sequence,
            'invoice_user_id': self.env.user.id,
            'installment_type': installment_type,
            'project_payment_id': project_payment_id,
            'invoice_date': payment.date,
            'invoice_date_due': payment.date,
            'eng_office_installment_id': payment.eng_office_installment_id.id,
            'narration': payment.name,
            'partner_id': payment.partner_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': name_spec,
                'price_unit': amount,
                'quantity': 1.0,
                'account_id': account_id,
                # 'tax_ids': [(6, 0, [payment.tax_id.id])],
            })],
        }
        return invoice_vals

                
    def approve(self):
        if not self.project_id.project_expenses_account_id or not self.project_id.discount_account_id or not self.project_id.project_investment_account_id:
            raise UserError(_('Please Contact Administrator to configure your project accounts.'))
        if self.project_id.project_owner_type == 'company':
            account_id = self.project_id.project_expenses_account_id
        else :
            account_id = self.project_id.project_investment_account_id
        name_spec = ''
        name_spec = 'Installment Reference:' + str(self.sequence) + '-' + str(self.name)
        if self.type == 'eng_office':
            invoice = self._prepare_invoice_values(self, 'engineer_office', self.id, name_spec, account_id, self.amount)
        elif self.type == 'subcontractor':
            amount = 0.0
            days = self.compute_days(self.subcontractor_line_id.subcontractor_installment_id.delivery_date, date.today().strftime('%Y-%m-%d'))
            if not self.flag:
                amount = abs(self.amount - self.penalty_amount)
            else:
                amount = self.amount
            invoice = self._prepare_invoice_values(self, 'subcontractor', self.id, name_spec, account_id, self.amount)
        invoice_id = self.env['account.move'].sudo().create(invoice).with_user(self.env.uid)
        self.state = 'approve'
        self.account_move_id = invoice_id.id


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    installment_type = fields.Selection([('subcontractor','Subcontractor'),
                                         ('engineer_office','Engineering Office')], string='Installment Type')
    project_payment_id = fields.Many2one('project.payment.request', string='Project Payment')
    eng_office_installment_id = fields.Many2one('engineering.office.line', string='Engineering Office Installment')
    subcontractor_installment_id = fields.Many2one('subcontractor.work.line', string='Subcontractor Office Installment')

    def action_post(self):
        res = super(AccountInvoice, self).action_post()
        if self.project_payment_id:
            self.project_payment_id.state = 'done'
        if self.subcontractor_installment_id:
            self.subcontractor_installment_id.paid = True
            self.subcontractor_installment_id.paid_date = date.today()
        if self.eng_office_installment_id:
            self.eng_office_installment_id.paid = True
            self.eng_office_installment_id.paid_date = date.today()
        return res
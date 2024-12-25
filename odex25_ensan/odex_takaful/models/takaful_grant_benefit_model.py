# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime, date, timedelta
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse
from odoo.exceptions import UserError, ValidationError, Warning
import logging

_logger = logging.getLogger(__name__)


class TakafulGrantBenefit(models.Model):
    _inherit = "grant.benefit"

    is_active_sponsorship = fields.Boolean(
        string="Currently Has Sponsorship?", compute='_get_sponsorship_ids')

    sponsorship_ids = fields.Many2many(
        'takaful.sponsorship', string='Sponsorships', compute='_get_sponsorship_ids')
    has_kafala_delay = fields.Boolean(
        string='Has Kafala Delay?', compute='_get_sponsorship_ids')
    overdue_kafalat_amount = fields.Float(
        string="Current Overdue Kafalat Amount", compute='_get_sponsorship_ids')

    # These fields work to calculate the value of the need and its percentage
    total_kafala_value = fields.Integer(
        string='Total Kafala Value', compute='_needs_value')
    benefit_needs_value = fields.Float(compute='_needs_value')
    benefit_needs_percent = fields.Float(compute='_needs_value')

    # Monthly sponsorship Payments
    # sponsorship_payment_ids = fields.One2many(
    #     'benefit.sponsorship.payment.line',
    #     'benefit_id', 'Sponsorship Monthly Payments')

    # @api.onchange('arrears_ids')
    # def _compute_sponsorships_arrears(self):
    #     for rec in self:
    #         rec.benefit_arrears_value = sum(rec.arrears_ids.mapped('arrears_total'))

    @api.onchange('total_expenses', 'total_income')
    def _needs_value(self):
        for rec in self:
            rec.total_kafala_value = rec.total_expenses
            kafala_income = 0.0
            for kafala in rec.sponsorship_ids:
                # if kafala.state not in ['draft', 'canceled', 'closed']: #todo
                kafala_income += kafala.contribution_value
            rec.benefit_needs_value = abs(
                rec.total_expenses - rec.total_income - kafala_income)  # todo
            try:
                rec.benefit_needs_percent = 100 - \
                    (((rec.total_income + kafala_income) / rec.total_kafala_value) * 100)
            except:
                rec.benefit_needs_percent = 0.0
                pass

    def _get_sponsorship_ids(self):
        """ Get Sponsorships of Benefit"""
        for rec in self:
            sponsorships = self.env['takaful.sponsorship'].sudo().search(
                [('benefit_id', '=', rec.id), ('state', 'in', ['wait_pay', 'progress', 'to_cancel'])])
            overdue_kafala = 0
            ls_ids = []

            today = datetime.today().date().replace(day=1)
            for spon in sponsorships:
                spon._compute_next_due_date()
                ls_ids.append(spon.id)
                if spon.has_delay:
                    start_date = parse(str(spon.start_date)).date().replace(day=1)
                    if spon.paid_month_count > 0:
                        last_pay_date = start_date + \
                            relativedelta(months=spon.paid_month_count)
                    else:
                        spon._compute_next_due_date()
                        last_pay_date = (spon.next_due_date or start_date +
                                         relativedelta(months=spon.paid_month_count))

                    if spon.paid_month_count == 0:
                        num_months = 1
                    else:
                        num_months = (today.year - last_pay_date.year) * \
                            12 + (today.month - last_pay_date.month)

                    overdue_kafala += (num_months * spon.contribution_value)

            if ls_ids:
                rec.sponsorship_ids = [(6, 0, ls_ids)]
                rec.is_active_sponsorship = True
            else:
                rec.sponsorship_ids = [(6, 0, [])]
                rec.is_active_sponsorship = False

            if overdue_kafala > 0:
                rec.has_kafala_delay = True
                rec.overdue_kafalat_amount = overdue_kafala
            else:
                rec.has_kafala_delay = False
                rec.overdue_kafalat_amount = 0


class GrantBenefitInvoice(models.Model):
    _name = "grant.benefit.invoice"
    _description = 'Invoice for Beneficiaries'
    # _rec_name = 'code'

    benefit_ids = fields.Many2many('grant.benefit', string='Beneficiaries')
    operation_invoice_id = fields.Many2one('account.move',
                                           string="Invoice", ondelete='set null', readonly=True)
    operation_code = fields.Char(string='Operation Code', readonly=True)
    operation_type = fields.Selection([
        ('sponsorship', 'Sponsorship'),
        ('financial_gift', 'Financial Gift'),
        ('need_contribution', 'Needs Contribution')],
        string='Operation Type',
    )
    operation_id = fields.Integer(readonly=True)
    benefit_type = fields.Selection([
        ('orphan', 'Orphans'),
        ('widow', 'Widows')],
        string='Beneficiaries Type',
    )
    benefit_target = fields.Selection([
        ('person', 'Individual'),
        ('group', 'Group')],
        string='Target of Beneficiaries',
    )
    paid_amount = fields.Float(string='Paid Amount', readonly=True)
    partner_id = fields.Many2one('res.partner', string='From',
                                 store=True,
                                 related='operation_invoice_id.partner_id')
    journal_id = fields.Many2one('account.journal', string='Journal',
                                 store=True,
                                 related='operation_invoice_id.journal_id')
    due_date = fields.Date(string='Due Date', store=True,
                           related='operation_invoice_id.invoice_date')
    due_code = fields.Char(string='Due Code', store=True,
                           compute='_get_due_code', )
    payment_date = fields.Date(string='Payment Date', readonly=True)
    note = fields.Text(string='Note/Message')
    is_recorded = fields.Boolean(
        string='Is Recorded In Beneficiaries', default=False)

    def _get_due_code(self):
        """ Extract due code from due date """
        for rec in self:
            if rec.due_date:
                date = parse(str(rec.due_date)).date()
                rec.due_code = date.strftime("%Y_%m")


class AccountInvoice(models.Model):
    _inherit = "account.move"

    benefit_invoice_ids = fields.One2many('grant.benefit.invoice', 'operation_invoice_id',
                                          string='The Beneficiaries', ondelete='restrict')


class AccountPayment(models.Model):
    _inherit = "account.payment"

    is_benefit_registered = fields.Boolean(
        string='Is Registered To Beneficiary', default=False)

    def sponsorship_validate_invoice_payment(self, invoice):

        sponsorship_obj = self.env['takaful.sponsorship'].sudo().browse(
            invoice.operation_id)
        # Create an invoice for benefits.
        benefit_invoice = self.env['grant.benefit.invoice'].sudo().create({
            'operation_invoice_id': invoice.id,
            'operation_type': 'sponsorship',
            'operation_id': sponsorship_obj.id,
            'operation_code': sponsorship_obj.code,
            'benefit_type': sponsorship_obj.benefit_type,
            'benefit_target': sponsorship_obj.sponsorship_type,
            'paid_amount': self.amount,
            'payment_date': self.payment_date,
        })

        if sponsorship_obj.sponsorship_type == 'person':
            benefit_invoice.write(
                {'benefit_ids': [(4, sponsorship_obj.benefit_id.id)]})
        else:
            for benefit in sponsorship_obj.benefit_ids:
                benefit_invoice.write({'benefit_ids': [(4, benefit.id)]})

        if invoice.state == 'paid':
            self.is_benefit_registered = True

        # Change State
        if not sponsorship_obj.has_delay:
            sponsorship_obj.state = "progress"

        # Send SMS and Email Notifications
        paid_template = self.env['takaful.message.template'].search(
            [('template_name', '=', 'sponsorship_paid')], limit=1)

        subject = paid_template.title
        message = paid_template.body + '\n' + _('Sponsorship: ') + '{}'.format(sponsorship_obj.code) + '\n' + _(
            'Paid Value: ') + '{}'.format(self.amount) + '\n' + _('Invoice Ref: ') + '{}'.format(invoice.number)
        user_id = sponsorship_obj.sponsor_id.user_id

        push = self.env['takaful.push.notification'].sudo().create({
            'user_id': user_id.id,
            'title': subject,
            'body': message,
        })

        push.sudo().send_sms_notification()
        push.sudo().send_email_notification()

    def action_validate_invoice_payment(self):
        res = super(AccountPayment, self).action_validate_invoice_payment()
        # Handle payment for every invoice
        for invoice in self.invoice_ids:
            # move = invoice.invoice_id
            if invoice.operation_type == 'sponsorship':
                self.sudo().sponsorship_validate_invoice_payment(invoice)

        return res


class TakafulGrantBenefit(models.Model):
    _inherit = "grant.benefit"

    @api.model
    def create(self, values):
        name = values.get('name', False)
        if name is False:
            first_name = values.get('first_name')
            second_name = values.get('second_name')
            middle_name = values.get('middle_name')
            family_name = values.get('family_name')
            name = ''
            if all([second_name,first_name,middle_name,family_name]):
                name = first_name + " " + second_name + " " + middle_name + " " + family_name
            values.update({'name': name})
        values.update({'lang': 'ar_001'})
        values.update({'tz': 'Asia/Riyadh'})
        return super(TakafulGrantBenefit, self).create(values)

    arrears_ids = fields.One2many(
        'sponsorship.benefit.arrears', 'sponsor_id', string="Sponsorships Arrears")
    benefit_arrears_value = fields.Float(
        string='Total Sponsorships Arrears', compute='_compute_sponsorships_arrears', store=True)
    has_arrears = fields.Boolean(
        string='Has Arrears', compute='_compute_sponsorships_arrears', store=True)
    # analytic_account_id = fields.Many2one(
    #     'account.analytic.account', 'Cost Center')

    def finish_complete_data(self):
        for rec in self:
            res = super(TakafulGrantBenefit, self).finish_complete_data()
            # main_analytic_account_id = ""
            # self.ensure_one()
            # sudoConf = self.env['ir.config_parameter'].sudo()
            # main_widows_analytic_account_id = sudoConf.get_param(
            #     'odex_benefit.main_widows_analytic_account_id', default=False)
            # main_orphan_analytic_account_id = sudoConf.get_param(
            #     'odex_benefit.main_orphan_analytic_account_id', default=False)
            # if rec.benefit_type == "orphan":
            #     if not main_orphan_analytic_account_id:
            #         raise ValidationError(
            #             _(''' Please set orphan restricted income account in settings '''))
            #     main_analytic_account_id = main_orphan_analytic_account_id
            # elif rec.benefit_type == "widow":
            #     if not main_widows_analytic_account_id:
            #         raise ValidationError(
            #             _(''' Please set widow restricted income account in settings '''))
            #     main_analytic_account_id = main_widows_analytic_account_id
            # if main_analytic_account_id and not rec.analytic_account_id:
            #     ID = self.env['account.analytic.account'].create({'parent_id': main_analytic_account_id,'name': rec.name})
            #     rec.write({'analytic_account_id': ID.id})
    def action_accepted(self):
        for rec in self:
            res = super(TakafulGrantBenefit, self).action_accepted()
            # main_analytic_account_id = ""
            # self.ensure_one()
            # sudoConf = self.env['ir.config_parameter'].sudo()
            # main_widows_analytic_account_id = sudoConf.get_param(
            #     'odex_benefit.main_widows_analytic_account_id', default=False)
            # main_orphan_analytic_account_id = sudoConf.get_param(
            #     'odex_benefit.main_orphan_analytic_account_id', default=False)
            # if rec.benefit_type == "orphan":
            #     if not main_orphan_analytic_account_id:
            #         raise ValidationError(
            #             _(''' Please set orphan restricted income account in settings '''))
            #     main_analytic_account_id = main_orphan_analytic_account_id
            # elif rec.benefit_type == "widow":
            #     if not main_widows_analytic_account_id:
            #         raise ValidationError(
            #             _(''' Please set widow restricted income account in settings '''))
            #     main_analytic_account_id = main_widows_analytic_account_id
            # if main_analytic_account_id and not rec.analytic_account_id:
            #     ID = self.env['account.analytic.account'].create({'parent_id': main_analytic_account_id,'name': rec.name})
            #     rec.write({'analytic_account_id': ID.id})
        
    @api.onchange('arrears_ids')
    def _compute_sponsorships_arrears(self):
        for rec in self:
            rec.benefit_arrears_value = sum(
                rec.arrears_ids.mapped('arrears_total'))
            if rec.benefit_arrears_value > 0:
                rec.has_arrears = True
            else:
                rec.has_arrears = False


class SponsorshipBenefitArrears(models.Model):
    _name = "sponsorship.benefit.arrears"
    _description = 'Sponsorship Arrears for a Beneficiary'
    _rec_name = 'code'

    benefit_id = fields.Many2one('grant.benefit', string='Beneficiary')
    benefit_type = fields.Selection(
        string="Beneficiary Type", related="benefit_id.benefit_type", store=True)
    sponsorship_id = fields.Many2one(
        'takaful.sponsorship',
        string='Sponsorship'
    )
    sponsor_id = fields.Many2one(
        'takaful.sponsor',
        string='The Sponsor',
        ondelete='set null'
    )
    code = fields.Char(string="Sponsorship Number",
                       related="sponsorship_id.code", store=True)
    month_amount = fields.Float(string="Month Sponsorship Amount",
                                related="sponsorship_id.load_amount", store=True, readonly=True)
    arrears_month_number = fields.Integer(string="Arrears Months Number")
    arrears_total = fields.Float(string="Arrears Total")
    date = fields.Date('Date', readonly=True, default=fields.Date.today())
    is_paid = fields.Float(string="Is Paid", compute='_get_arrears_amount')
    paid_amount = fields.Float(
        string="Paid Amount", compute='_get_arrears_amount', store=True)
    arrears_amount = fields.Float(
        string="Remine Arrears Amount", compute='_get_arrears_amount', store=True)
    invoice_ids = fields.Many2many(
        'account.move', string='Payment Invoices')

    def _get_arrears_amount(self):
        """ Compute Arrears Amount, Paid and Remine"""
        for rec in self:
            if rec.invoice_ids:
                paid_amount = 0
                for inv in rec.invoice_ids:
                    if inv.state == 'paid':
                        paid_amount += inv.amount

                if paid_amount > 0:
                    rec.paid_amount = paid_amount
                    rec.arrears_amount = abs(rec.arrears_total - paid_amount)
                else:
                    rec.paid_amount = 0
                    rec.arrears_amount = rec.arrears_total

                if paid_amount >= rec.arrears_total:
                    rec.is_paid = True
                else:
                    rec.is_paid = False
            else:
                rec.is_paid = False
                rec.arrears_amount = rec.arrears_total

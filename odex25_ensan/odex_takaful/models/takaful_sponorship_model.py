# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo import SUPERUSER_ID
from odoo.exceptions import UserError, ValidationError, Warning

from ast import literal_eval
import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse

def trunc_datetime(someDate):
    # Compare two dates based on Month and Year only
    return someDate.replace(day=1, hour=0, minute=0, second=0, microsecond=0)


def get_first_day_of_next_month():
    """ Get the first day of the next month. Preserves the timezone. """
    dt = datetime.datetime.today()  # Starting from current month
    if dt.day == 1:
        # Ya.. first day of the month!
        return dt

    if dt.month == 12:
        return datetime.datetime(year=dt.year + 1,
                                 month=1,
                                 day=1,
                                 tzinfo=dt.tzinfo)
    else:
        return datetime.datetime(year=dt.year,
                                 month=dt.month + 1,
                                 day=1,
                                 tzinfo=dt.tzinfo)


class TakafulSponsorship(models.Model):
    _name = 'takaful.sponsorship'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Sponsorship"
    _rec_name = 'code'

    sponsor_id = fields.Many2one('takaful.sponsor',string='Sponsor Name',domain="[('branch_custom_id', '=', branch_custom_id),('branch_custom_id','!=',False)]")
    member_id = fields.Many2one('res.partner',string='Member Name',domain="[('is_member', '=', True)]")
    is_gift = fields.Selection([('no', 'No'),('yes', 'Yes')],string='Is Gift To Person')
    gifter_id = fields.Many2one(
        'takaful.sponsor',
        string='The Gifter To'
    )
    gifter_name = fields.Char(string="The Gifter Name")
    gifter_mobile = fields.Char(string="The Gifter Mobile")
    gifter_message = fields.Text(string='Message To Gifter')

    sponsorship_type = fields.Selection([('person', 'Individual'),('group', 'Group')],string='Sponsorship Type',tracking=True)
    code = fields.Char(string="Code",copy=False,readonly=True)
    benefit_type = fields.Selection([('orphan', 'Orphans'),('widow', 'Widows')],string='Sponsorship Beneficiary Type',tracking=True)
    branch_custom_id = fields.Many2one('branch.settings', string="Branch")
    sponsorship_creation_date = fields.Datetime(string="Sponsorship Creation Date", default=fields.Datetime.now)
    sponsor_note = fields.Text(string='Sponsor Note')
    sponsor_or_donor_type = fields.Selection(string='Sponsor / Donor Type',selection=[('registered', 'Registered'), ('new_sponsor', 'New Sponsor'),('not_registered', 'Not Registered'),('unknown', 'Unknown')])
    sponsor_name = fields.Char(string="Sponsor Name")
    sponsor_phone = fields.Char(string="Sponsor Phone")
    sponsor_title = fields.Many2one('res.partner.title',string='Sponsor Title')
    donate_for_another_person = fields.Boolean(string='Donate For Another Person')
    another_sponsors = fields.One2many('donate.for.another.person','sponsorship_id')
    registered_type = fields.Selection(string='Registered Type',selection=[('sponsor', 'Sponsor'),('member', 'Member')])
    members_domain_ids = fields.Many2many(comodel_name='family.member', compute='_compute_domain_ids')
    # This is if for one person, and not a group.
    benefit_id = fields.Many2one('family.member',string='Beneficiary Name',ondelete='set null',domain = "[('id', 'in',members_domain_ids)]")
    family_id = fields.Many2one('grant.benefit',string='Family',ondelete='set null',related="benefit_id.benefit_id")
    education_status = fields.Selection(string='Education Status',selection=[('educated', 'educated'), ('illiterate', 'illiterate'),('under_study_age','Under Study Age')])
    education_level = fields.Many2one("education.level", string='Education Levels')
    sponsorship_duration = fields.Selection([('temporary', 'Temporary'),('permanent', 'Permanent')],string='Sponsorship Duration',default='permanent',tracking=True)
    total_sponsorship_amount = fields.Float(string='Total Sponsorship Amount',compute='_get_total_sponsorship_amount')
    supporter_status = fields.Selection([
        ('no', 'Not Exist'),
        ('yes', 'Exist')],
        string='Supporter',
        tracking=True,
        compute='_compute_supporter_status',
    )

    has_needs = fields.Boolean(store=True)
    donations_details_lines = fields.One2many('donations.details.lines','sponsorship_id')
    payment_details_lines = fields.One2many('payment.details.lines','sponsorship_id')

    @api.constrains('payment_details_lines')
    def check_payment_amount(self):
        total_amount = 0
        for rec in self.payment_details_lines:
            total_amount += rec.donation_amount
        if total_amount != self.total_sponsorship_amount:
            raise ValidationError(
                _('Total Payment Amount Should be Total Sponsorship Amount'))

    @api.constrains('donations_details_lines')
    def check_donation_types(self):
        # Search for an existing record
        record_exist = self.env["donations.details.lines"].search(
            [('donation_type', '=', 'sponsorship'),
             ('sponsorship_id', '=', self.id)],
        )

        # Raise error if record already exists
        if record_exist and len(record_exist) > 1:
            raise ValidationError(_("You cannot Add more than one sponsorship"))

    @api.constrains('end_date')
    def check_end_date(self):
        if self.sponsorship_duration == "temporary" and not self.end_date:
            raise ValidationError(
                _(u'Please Select End Date'))

        elif self.sponsorship_duration == "temporary" and self.end_date:
            start_date = trunc_datetime(parse(str(self.start_date))).date()
            end_date = trunc_datetime(parse(str(self.end_date))).date()
            if start_date >= end_date:
                raise ValidationError(
                    _(u'End Date Must Be More Than Start Date in Months'))

    @api.depends('benefit_id.benefit_id')
    @api.onchange('benefit_id')
    def _compute_supporter_status(self):
        for rec in self:
            if rec.benefit_id:
                if rec.benefit_id.benefit_id:
                    rec.supporter_status = 'yes'
                else:
                    rec.supporter_status = 'no'
            else:
                rec.supporter_status = ''
    @api.depends('donations_details_lines')
    def _get_total_sponsorship_amount(self):
        for rec in self:
            rec.total_sponsorship_amount = sum(line.total_donation_amount for line in rec.donations_details_lines)

    @api.onchange('donations_details_lines')
    def onchange_donations_details_lines(self):
        for rec in self:
            rec.benefit_ids = rec.donations_details_lines.benefit_ids.ids

    @api.depends('gender','education_status','education_level','sponsorship_type','benefit_type','age_category_id')
    def _compute_domain_ids(self):
        # Create a domain
        self.members_domain_ids = [(6, 0, [])]
        if self.benefit_type == 'orphan' and self.sponsorship_type:
            base_domain = \
                [
                    ('state', 'in', ['second_approve', 'temporarily_suspended', 'suspended_first_approve']),
                    ('member_status', '=', 'benefit'),
                    '|',
                    ('relationn.relation_type', '=', 'daughter'),
                    ('relationn.relation_type', '=', 'son')
                ]
            if self.gender:
                if self.gender == 'female':
                    base_domain = [
                        ('state', 'in', ('second_approve', 'temporarily_suspended', 'suspended_first_approve')),
                        ('member_status', '=', 'benefit'), ('relationn.relation_type', '=', 'daughter')]
                if self.gender == 'male':
                    base_domain = [
                        ('state', 'in', ('second_approve', 'temporarily_suspended', 'suspended_first_approve')),
                        ('member_status', '=', 'benefit'),('relationn.relation_type', '=', 'son')]
            if self.education_status:
                base_domain.append(('education_status', '=', self.education_status))
            if self.education_level:
                base_domain.append(('education_levels', '=', self.education_level.id))
            if self.age_category_id:
                base_domain.append(('age', '<=', self.age_category_id.max_age))
                base_domain.append(('age', '>=', self.age_category_id.min_age))
            self.members_domain_ids = self.env['family.member'].sudo().search(base_domain)
            domain = {'benefit_id': [('id', 'in', self.members_domain_ids.ids)]}
            return {'domain': domain}
        if self.benefit_type == 'widow' and self.sponsorship_type:
            self.benefit_count = 0
            self.min_needs_percent = 0
            self.max_needs_percent = 0
            base_domain = [('state', 'in', ['second_approve', 'temporarily_suspended', 'suspended_first_approve']),('member_status','=','benefit'),'|',('relationn.relation_type', '=', 'mother'),('relationn.relation_type', '=', 'replacement_mother')]
            if self.education_status:
                base_domain.append(('education_status', '=', self.education_status))
            if self.education_level:
                base_domain.append(('education_levels', '=', self.education_level.id))
            if self.age_category_id:
                base_domain.append(('age', '<=', self.age_category_id.max_age))
                base_domain.append(('age', '>=', self.age_category_id.min_age))
            self.members_domain_ids = self.env['family.member'].sudo().search(base_domain)
            domain = {'benefit_id': [('id', 'in', self.members_domain_ids.ids)]}
            return {'domain': domain}

    # @api.depends('sponsorship_type')
    # def onchange_benefit_type(self):
    #     # Create a domain
    #     if self.benefit_type and self.benefit_id and not self.benefit_id.benefit_type == self.benefit_type:
    #         self.benefit_id = False
    #     elif self.benefit_type and self.benefit_ids and not self.benefit_ids[0].benefit_type == self.benefit_type:
    #         self.benefit_ids = [(6, 0, [])]
    #         self.benefit_count = 0
    #         self.min_needs_percent = 0
    #         self.max_needs_percent = 0
    #
    #     if self.benefit_type and self.sponsorship_type == 'person':
    #         self.benefit_ids = [(6, 0, [])]
    #         self.benefit_count = 0
    #         self.min_needs_percent = 0
    #         self.max_needs_percent = 0
    #         base_domain = [('state', 'in', ('second_approve', 'temporarily_suspended', 'suspended_first_approve'))]
    #         if self.gender:
    #             if self.gender == 'female':
    #                 base_domain.append(('relationn.relation_type', '=','daughter'))
    #             if self.gender == 'male':
    #                 base_domain.append(('relationn.relation_type', '=', 'son'))
    #         if self.education_status:
    #             base_domain.append(('education_status', '=', self.education_status))
    #         if self.education_level:
    #             base_domain.append(('education_levels', '=', self.education_level.id))
    #         benefit_ids = self.env['family.member'].sudo().search(base_domain)
    #         domain = {'benefit_id': [('id', 'in', benefit_ids.mapped('id'))]}
    #         return {'domain': domain}
    #     elif self.benefit_type and self.sponsorship_type == 'group':
    #         self.benefit_id = False
    #         benefit_ids = self.env['grant.benefit'].sudo().search(
    #             [('benefit_type', '=', self.benefit_type), ('state', '=', 'approve')], limit=self.benefit_count)
    #         # domain = {'benefit_ids': [('id', 'in', benefit_ids.filtered(lambda ben: ben.benefit_needs_percent > 0 and ben.benefit_needs_percent >= self.min_needs_percent and ben.benefit_needs_percent <= self.max_needs_percent).mapped('id'))]}
    #         domain = {'benefit_ids': [('id', 'in', benefit_ids.mapped('id'))]}
    #         return {'domain': domain}

    gender = fields.Selection(selection=[('male', 'Male'), ('female', 'Female')], string="Gender")
    age_category_id = fields.Many2one('age.category',string='Age Category')
    city_id = fields.Many2one(
        'res.country.city',string='District')

    benefit_count = fields.Integer(string='Sponsorship Beneficiaries Number',compute="_get_benefits_count")

    start_date = fields.Date(string="Sponsorship Start Date", copy=False)
    end_date = fields.Date(string="Sponsorship End Date")

    min_needs_percent = fields.Float(string='Min Needs Percentage')
    max_needs_percent = fields.Float(string='Max Needs Percentage')

    sponsorship_class = fields.Selection([
        ('partial', 'Partial Sponsorship'),
        ('fully', 'Fully Sponsorship')],
        string='Sponsorship Beneficiaries Classification',
        tracking=True
    )
    benefit_ids = fields.Many2many('family.member',string='Beneficiaries Names')

    with_orphan_ids = fields.Many2many(
        'grant.benefit',relation='takaful_sponsor_grant_benefit_rel',
        string='Orphans Names Of Widow'
    )

    is_widow_orphan = fields.Boolean(
        string='Widow with Her Orphans?', default=False)

    payment_option = fields.Selection([('month', 'Monthly'),('once', 'For Once')], string='Payment Option')

    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('deduct', 'Deduction'),
    ], string='Method Of Payment')
    payment_journal_id = fields.Many2one('account.journal', string='Payment Method', domain="[('type', 'in', ['cash', 'bank'])]",)

    cancel_reason_id = fields.Many2one('sponsorship.cancellation', string='Cancellation Entry',
                                       tracking=True)
    reason = fields.Text(string="Cancellation Reason",
                         related="cancel_reason_id.note", store=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('wait_pay', 'Waiting Payment'),
        ('progress', 'In Progress'),
        ('to_cancel', 'About To Cancel'),
        ('canceled', 'Canceled'),
        ('closed', 'Closed'),
    ], string='state', default='draft', tracking=True)

    has_delay = fields.Boolean(string='Has Payment Delay?', compute='_check_if_has_delay', related=False, readonly=True,
                               store=True)
    due_days = fields.Integer(string='Overdue in Days',
                              compute='_check_if_has_delay', store=True)
    contribution_value = fields.Float(string="Contribution Value")
    load_amount = fields.Float(string="Load Amount Per Person")
    total_contribution = fields.Float(string="Contributions Total",
                                      compute='calculate_total_paid')
    
    total_voucher = fields.Float(string="Voucher Total",
                                      compute='voucher_total_paid')
    # New Added
    to_renew = fields.Boolean(string='Need To Renew?', default=False)
    overdue_amount = fields.Float(
        string='Overdue Amount', compute='_compute_overdue_total_amount')
    expected_cancel_date = fields.Date(
        string='Expected Cancel Date', compute='_check_if_has_delay')
    month_count = fields.Integer(
        string='Sponsorship Months Count', compute='_compute_month_count')
    paid_month_count = fields.Integer(
        string='Paid Months Count', compute='_compute_paid_month_count')
    next_due_date = fields.Date(
        string='Next Payment Date', compute='_compute_next_due_date', store=True)
    close_to_be_canceled_date = fields.Date(string='Close To Cancel Date')

    # NN
    invoice_count = fields.Integer(string='Invoices',
                                   compute='_compute_invoice_count')
    last_invoice_date = fields.Date(string='Last Invoice')
    voucher_ids = fields.One2many('account.move','sponsorship_id',string='Vouchers', copy=False)
    # payment_ids = fields.One2many('account.payment','sponsorship_id',string='Payments', copy=False)

    # @api.depends('contribution_value', 'benefit_ids', 'sponsorship_type')
    # def _compute_load_amount(self):
    #     """ Calculate load amount of sponsorship for a person """
    #     for rec in self:
    #         if rec.benefit_ids and rec.contribution_value > 0 and rec.sponsorship_type == 'group':
    #             rec.load_amount = float(
    #                 rec.contribution_value / len(rec.benefit_ids))
    #         else:
    #             rec.load_amount = rec.contribution_value
    @api.depends('benefit_ids')
    def _get_benefits_count(self):
        for rec in self:
            rec.benefit_count = len(rec.benefit_ids)

    def voucher_total_paid(self):
        self.total_voucher = len(self.voucher_ids)

    def calculate_total_paid(self):
        """ Calculate Total Paid Invoices based on sponsorship """
        for rec in self:
            paid_invoices = self.env['account.move'].sudo().search_count([
                ('sponsorship_id', '=', rec.id),
                ('state', 'not in', ['draft','proforma']),
            ])
            rec.total_contribution = paid_invoices

    def _compute_invoice_count(self):
        """ Calculate Invoice count based on sponsorship """
        invoice_count = self.env['account.move'].search_count(
            [('operation_id', '=', self.id), ('operation_type', '=', 'sponsorship')])
        if invoice_count > 0:
            self.invoice_count = invoice_count
        else:
            self.invoice_count = 0

    def create_next_invoice(self, next_date=None):
        if not next_date:
            next_date = get_first_day_of_next_month(datetime.datetime.today())

        # Get journal from config
        sudoConf = self.env['ir.config_parameter'].sudo()
        journal_id = sudoConf.get_param(
            'odex_takaful_base.kafala_journal_id', default=False)

        if not journal_id:
            # Raise an error
            raise ValidationError(
                _(u'No Journal for Sponsorships, Please configure it'))

        journal = self.env['account.journal'].search([('id', '=', journal_id)])
        # Create the Invoice staff
        customer = self.sponsor_id.partner_id
        # account_receivable = self.env['account.account'].search([('user_type_id', '=', self.env.ref('account.data_account_type_receivable').id)], limit=1)

        company_id = self.env.user.company_id

        if self.benefit_type == 'orphan':
            account_revenue = company_id.orphan_account_id
        elif self.benefit_type == 'widow':
            account_revenue = company_id.widow_account_id

        if not account_revenue:
            # Raise an error
            raise ValidationError(
                _(u'Invalid Orphans or Widows account, Please configure it'))

        account_receivable = company_id.kafala_benefit_account_id
        if not account_receivable:
            # Raise an error
            raise ValidationError(
                _(u'Invalid From Account of Benefit Payments (Recievable Account), Please configure it'))

        Invoice = self.env["account.move"].sudo()

        currency_id = self.env.ref('base.main_company').currency_id

        invoice_id = Invoice.create({
            'operation_id': self.id,
            'operation_type': 'sponsorship',
            'partner_id': customer.id,
            'reference_type': 'none',
            'journal_id': journal.id,
            'currency_id': journal.currency_id.id or company_id.currency_id.id or currency_id.id,
            # journal.currency_id.id
            'name': u'إستحقاق كفالة' + ' - ' + self.code,
            'account_id': account_receivable.id,  # account_id or
            'type': 'out_invoice',
            'comment': u'بغرض إستحقاق كفالة',
            'date_invoice': next_date,
        })

        product_id = self.env['product.product'].sudo().search(
            [('default_code', '=', "sponsorship")], limit=1)
        partner_id = self.sponsor_id.partner_id

        # Update product:
        product_id.sudo().write({
            "list_price": self.contribution_value,
            "name": u'كفالة' + ' ' + self.code,
            'description_sale': u'كفالة رقم ' + self.code,
        })

        # Create line
        InvoiceLine = self.env["account.move.line"]
        InvoiceLine.create({
            'product_id': product_id.id,
            'quantity': 1,
            'price_unit': self.contribution_value,
            'invoice_id': invoice_id.id,
            'name': u'كفالة رقم ' + self.code,
            'account_id': account_revenue.id,
            # "invoice_line_tax_ids": [],
        })

        invoice_id.action_invoice_open()

        if invoice_id:
            self.state = "wait_pay"

        return invoice_id

    def button_invoice_count(self):
        """ It displays invoice based on sponsorship """
        return {
            'name': _('Invoices'),
            'domain': [('operation_id', '=', self.id), ('operation_type', '=', 'sponsorship')],
            'view_type': 'form',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
            'context': {
                "create": False
            }
        }

    def button_payment(self):
        """ Button to create invoice for sponsorship """
        out_invoice = self.create_next_invoice()

        return {
            'name': _('The Sponsorship Invoices'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'form',
            'res_id': out_invoice.id if out_invoice else False
        }

    # EE
    def _compute_overdue_total_amount(self):
        """ Calculate Total Overdue Amount"""
        for rec in self:
            overdue_kafala = 0
            if rec.has_delay and rec.state in ['wait_pay', 'progress', 'to_cancel']:
                # Get open invoices
                open_invoices = self.env['account.move'].sudo().search(
                    [('state', '=', 'open'), ('operation_id', '=', rec.id), ('operation_type', '=', 'sponsorship')])
                for invoice in open_invoices:
                    if invoice.state == 'open':
                        overdue_kafala += invoice.residual_company_signed
            rec.overdue_amount = overdue_kafala

    @api.depends("paid_month_count", "month_count", "last_invoice_date")
    def _compute_next_due_date(self):
        """ Find the Next Due Date for Sponsorship Payment"""
        for rec in self:
            next_due = None
            if rec.end_date:
                end_date = parse(str(rec.end_date)).date()
            else:
                end_date = None

            if rec.state in ['draft', 'wait_pay', 'progress', 'to_cancel']:
                if rec.end_date and rec.paid_month_count < rec.month_count:
                    start_date = parse(str(rec.start_date)).date()
                    next_due = start_date + \
                        relativedelta(months=(rec.paid_month_count + 1))
                else:
                    if rec.last_invoice_date:
                        last_invoice = parse(str(rec.last_invoice_date)).date()
                        next_due = last_invoice + relativedelta(months=1)

            if (next_due and end_date and next_due <= end_date) or (next_due and not rec.end_date):
                rec.next_due_date = next_due
            else:
                rec.next_due_date = None

            if rec.state == "confirmed":
                rec.next_due_date = parse(str(rec.start_date)).date()

    def _compute_paid_month_count(self):
        """ Calculate Total Paid Months for the sponsorship """
        for rec in self:
            invoice_count = self.env['account.move'].sudo().search_count([
                ('operation_type', '=', 'sponsorship'),
                ('operation_id', '=', rec.id),
                ('state', '=', 'paid'),
            ])

            if invoice_count > 0:
                rec.paid_month_count = invoice_count
            else:
                rec.paid_month_count = 0

    def _compute_month_count(self):
        """ Calculate months count """
        for rec in self:
            if rec.start_date and rec.end_date:
                start = parse(str(rec.start_date)).date()
                end = parse(str(rec.end_date)).date()
                months = relativedelta(start, end)
                rec.month_count = abs(months.months) + abs(months.years*12)

    def is_sponsorship_has_delay(self):
        """ Find that if sponsorship package has overdue invoices"""
        sudoConf = self.env['ir.config_parameter'].sudo()
        allowed_days = int(sudoConf.get_param(
            'odex_takaful_base.allowed_pay_days'))
        date_today = datetime.datetime.today().date()

        # Get open invoices
        open_invoices = self.env['account.move'].sudo().search(
            [('state', '=', 'open'), ('operation_id', '=', self.id), ('operation_type', '=', 'sponsorship')])
        for invoice in open_invoices:
            payment_limt_date = parse(
                str(invoice.date_due)) + timedelta(days=allowed_days)
            if payment_limt_date.date() < date_today:
                return payment_limt_date

        return False

    @api.depends('expected_cancel_date')
    def _check_if_has_delay(self):
        sudoConf = self.env['ir.config_parameter'].sudo()
        cancel_kafala = int(sudoConf.get_param(
            'odex_takaful_base.cancel_kafala'))
        date_today = datetime.datetime.today().date()
        for rec in self:
            delay_date = rec.is_sponsorship_has_delay()
            if delay_date:
                rec.has_delay = True
                rec.due_days = (date_today - delay_date.date()).days
                rec.expected_cancel_date = delay_date + \
                    timedelta(days=(cancel_kafala))
            else:
                rec.has_delay = False
                rec.expected_cancel_date = None
                rec.due_days = 0

    # On Change
    # @api.onchange('sponsorship_class', 'sponsorship_type', 'benefit_id', 'benefit_ids')
    # def sponsorship_fully_value(self):
    #     if self.sponsorship_class == 'fully' and self.benefit_ids and self.sponsorship_type == 'group':
    #         self.update({'contribution_value': sum(
    #             self.benefit_ids.mapped('benefit_needs_value'))})
    #     elif self.sponsorship_class == 'fully' and self.benefit_id and self.sponsorship_type == 'person':
    #         self.update(
    #             {'contribution_value': self.benefit_id.benefit_needs_value})
    #     else:
    #         self.update({'contribution_value': 0})

    # @api.constrains('contribution_value')
    # def check_contribution_value(self):
    #     if not self.sponsor_id:
    #         raise ValidationError(
    #             _(u'Please Select The Sponsor'))

        # if not self.sponsorship_type:
        #     raise ValidationError(
        #         _(u'Please Select Sponsorship Type'))
        #
        # if not self.benefit_type:
        #     raise ValidationError(
        #         _(u'Please Select Sponsorship Beneficiary Type'))
        #
        # if not self.sponsorship_class:
        #     raise ValidationError(
        #         _(u'Please Select Sponsorship Class'))
        #
        # if not self.sponsorship_duration:
        #     raise ValidationError(
        #         _(u'Please Select Sponsorship Duration'))
        #
        # if not self.benefit_id and self.sponsorship_type == 'person':
        #     raise ValidationError(
        #         _(u'Please Select a Beneficiary For Sponsorship Person'))
        #
        # if len(self.benefit_ids) < 2 and self.sponsorship_type == 'group':
        #     raise ValidationError(
        #         _(u'Please Select At least Two Beneficiaries For Sponsorship Group'))
        #
        # if self.sponsorship_class == 'partial':
        #     default_sponsorship = int(
        #         self.env['ir.config_parameter'].sudo().get_param('odex_takaful_base.min_kafala', 0))
        #
        #     if self.benefit_ids and self.sponsorship_type == 'group':
        #         benefit_count = len(self.benefit_ids)
        #     else:
        #         benefit_count = 1
        #
        #     if default_sponsorship <= 0:
        #         raise ValidationError(
        #             _(u'Min kafala value should be defined by administration'))
        #
        #     total_sponsorship = default_sponsorship * benefit_count
        #     if self.contribution_value < total_sponsorship:
        #         raise ValidationError(
        #             _(u'Kafala value should be equal or greater than') + ' ' + str(total_sponsorship))

    # Model Operations
    @api.model
    def create(self, vals):
        if vals.get('code', 'New') == 'New':
            if vals.get('benefit_type') == 'orphan':
                main_code = self.env['ir.sequence'].sudo(
                ).next_by_code('sponsorship.sequence')
                sub_code = self.env['ir.sequence'].sudo().next_by_code(
                    'sponsorship.orphan.sequence')
                if main_code and sub_code:
                    defualt_code = 'OR/' + str(main_code) + '/' + sub_code
                    vals.update({"code": defualt_code})

            elif vals.get('benefit_type') == 'widow':
                main_code = self.env['ir.sequence'].sudo(
                ).next_by_code('sponsorship.sequence')
                sub_code = self.env['ir.sequence'].sudo().next_by_code(
                    'sponsorship.widow.sequence')
                if main_code and sub_code:
                    defualt_code = 'WI/' + str(main_code) + '/' + sub_code
                    vals.update({"code": defualt_code})

        # Create the record
        res = super(TakafulSponsorship, self).create(vals)

        return res

    # @api.multi
    def action_open_sponsorship_payement(self):
        """Open Payments for a Sponsorship"""
        pay = []
        pay_ids = self.voucher_ids.mapped('payment_id').ids
        for line in self.voucher_ids:
            pay.append(line.line_ids.filtered(lambda x : x.payment_id != False).mapped('payment_id').id)
        domain = [('id','in',pay_ids)]
        context = dict(self.env.context or {})
        context['default_sponsor_id'] = self.sponsor_id.id
        context['default_sponsorship_id'] = self.id
        return {
            'name': _('Sponsorship Payment'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'target': 'current',
            'domain': domain,
        }

    # @api.multi
    def action_set_cancel(self):
        """Make Cancellation For Sponsorship"""
        domain = []
        context = dict(self.env.context or {})
        context['default_sponsor_id'] = self.sponsor_id.id
        context['default_cancel_user_id'] = self.env.uid or SUPERUSER_ID
        context['default_sponsorship_id'] = self.id
        view = self.env.ref('odex_takaful.sponsorship_cancellation_form')
        return {
            'name': _('Sponsorship Cancellation'),
            'view_mode': 'form',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'res_model': 'sponsorship.cancellation',
            'view_id': view.id,
            'target': 'current',
            'domain': domain,
            'context': context,
        }

    # @api.multi
    def action_make_payement(self):
        """Create Payment for Sponsorship Beneficiary"""
        # Create necessary objects
        if self.state == 'draft':
            # Raise an error
            raise ValidationError(
                _(u'This Sponsorship is not confirmed'))

        self.sponsor_id.partner_id.write({
            'lang': 'ar_001',
        })

        domain = []
        context = dict(self.env.context or {})
        context['default_sponsor_id'] = self.sponsor_id.id
        context['default_sponsorship_id'] = self.id
        view = self.env.ref('odex_takaful.takaful_sponsorship_payment_form')
        return {
            'name': _('Sponsorship Payment'),
            'view_mode': 'form',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'res_model': 'sponsorship.payment',
            'view_id': view.id,
            'target': 'current',
            'domain': domain,
            'context': context,
        }

    def action_confirm_data(self):
        if self.state == 'draft':
            # Send SMS Notification
            msg_template = self.env['takaful.message.template'].search(
                [('template_name', '=', 'sponsorship_creation')], limit=1)

            start_date = parse(str(self.start_date)).date()
            start_by = _('Start Date')
            start_text = start_by + ' ' + start_date.strftime('%d, %b %Y')

            subject = msg_template.title
            message = msg_template.body + '\n' + _('Sponsorship Number') + ' %s' % self.code + '\n' + _(
                'Contribution Value') + ' %s' % str(self.contribution_value) + '\n' + start_text
            user_id = self.sponsor_id.user_id
            push = self.env['takaful.push.notification'].sudo().create({
                'user_id': user_id.id,
                'title': subject,
                'body': message,
            })

            push.sudo().send_sms_notification()
            self.state = "confirmed"

    # @api.multi
    def print_makfuleen_report(self):
        """ Method to print Makfuleen report """
        datas = dict(self.env.context)
        return self.env.ref('odex_takaful.makfuleen_report_pdf_act').report_action(self, data=datas)

    # @api.multi
    def process_sponsor_payments_scheduler(self):
        domain = []
        context = dict(self.env.context or {})
        context["create"] = False
        context["edit"] = False
        flags = {'initial_mode': 'readonly'}  # default is 'edit'
        return {
            'name': _('Move Entries'),
            'domain': domain,
            'view_type': 'form',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
            'flags': flags,
            'context': context,
        }

        # """
        # contribute = self.env['takaful.contribution'].sudo().create({
        #     'name': u'مساهمة مالية لكمبيوتر مكتبي',
        #     'sponsor_id': self.sponsor_id.id,
        #     'benefit_id': self.benefit_id.id or False,
        #     'amount': self.contribution_value,
        # })
        #
        # contribute.sudo().create_entry()
        # """

    # @api.multi
    def monthly_create_sponsorship_invoice_scheduler(self):
        _logger.info("Ya, Create Sponsorships Invoices Scheduler")
        sponsorships = self.env['takaful.sponsorship'].sudo().search(
            [('state', 'in', ['wait_pay', 'progress', 'to_cancel'])])
        for rec in sponsorships:
            if rec.last_invoice_date:
                today = trunc_datetime(datetime.datetime.today()).date()
                invoice_date = parse(str(rec.last_invoice_date))
                last_invoice = trunc_datetime(invoice_date).date()
                if today != last_invoice:
                    rec.sudo().create_next_invoice()

        _logger.info("Bye, Create Sponsorships Invoices Scheduler")

    # @api.multi
    def process_sponsorship_workflow_scheduler(self):
        # _logger.info("Hi, Manage Sponsorship Workflow Scheduler")s
        # Part: Processing state
        sudoConf = self.env['ir.config_parameter'].sudo()
        notifications = sudoConf.get_param(
            'odex_takaful_base.notification_ids')

        cancel_number = 1
        finish_number = 1
        cancel_message_type_ids = []
        finish_message_type_ids = []
        if notifications:
            notification_ids = self.env['takaful.notification'].sudo().search(
                [('id', 'in', literal_eval(notifications))])
            for rec in notification_ids:
                if rec.notification_type == "before_cancel":
                    cancel_number = rec.duration
                    cancel_message_type_ids = rec.message_type_ids

                if rec.notification_type == "before_finish":
                    finish_number = rec.duration
                    finish_message_type_ids = rec.message_type_ids

        sponsorships = self.env['takaful.sponsorship'].sudo().search(
            [('state', 'in', ['wait_pay', 'progress', 'to_cancel'])])

        date_today = datetime.datetime.today().date()
        for rec in sponsorships:
            # For colse (Finishing the sponsorships)
            partner_id = rec.sponsor_id.partner_id[0]
            if rec.end_date:
                end_date = datetime.datetime.strptime(
                    rec.end_date, '%Y-%m-%d').date()
                if end_date == date_today:
                    rec.sudo().write({"state": "closed", })
                    # Send Close Notification
                    sponsorship_close_template = self.env['takaful.message.template'].sudo().search(
                        [('template_name', '=', 'sponsorship_close')], limit=1)

                    subject = sponsorship_close_template.title
                    message = sponsorship_close_template.body
                    user_id = self.env['res.users'].sudo().search(
                        [('partner_id', '=', partner_id.id)], limit=1)

                    push = self.env['takaful.push.notification'].sudo().create({
                        'user_id': user_id.id,
                        'title': subject,
                        'body': message,
                    })

                    push.sudo().send_sms_notification()
                    push.sudo().send_email_notification()
                else:
                    before_close_date = end_date - \
                        timedelta(days=finish_number)
                    if before_close_date == date_today and not rec.to_renew:
                        rec.to_renew = True
                        # Send About to Close Notification
                        sponsorship_to_close_template = self.env['takaful.message.template'].sudo().search(
                            [('template_name', '=', 'sponsorship_to_close')], limit=1)

                        subject = sponsorship_to_close_template.title
                        message = sponsorship_to_close_template.body

                        user_id = self.env['res.users'].sudo().search(
                            [('partner_id', '=', partner_id.id)], limit=1)
                        push = self.env['takaful.push.notification'].sudo().create({
                            'user_id': user_id.id,
                            'title': subject,
                            'body': message,
                        })
                        for msg in finish_message_type_ids:
                            if msg.tool_type == "sms":
                                push.sudo().send_sms_notification()

                            elif msg.tool_type == "email":
                                push.sudo().send_email_notification()

            # For Cancel or about to cancel sponsorships
            if rec.expected_cancel_date:
                cancel_date = datetime.datetime.strptime(
                    rec.expected_cancel_date, '%Y-%m-%d').date()
                if cancel_date == date_today:
                    # Create Automatic cancellation record
                    sp_cancel = self.env['sponsorship.cancellation'].sudo().create({
                        'sponsorship_id': self.id,
                        'cancel_type': "sys",
                        'cancel_user_id': self.env.uid or SUPERUSER_ID,
                        'note': _('Overdue in Sponsorships Payment of Total %s') % str(rec.overdue_amount)
                    })
                    # Confirm cancellation and Send Notifications
                    sp_cancel.sudo().do_cancel_action()
                else:
                    before_cancel_date = cancel_date - \
                        timedelta(days=cancel_number)
                    if rec.state != "to_cancel" and before_cancel_date == date_today:
                        rec.sudo().write({"state": "to_cancel", })
                        rec.close_to_be_canceled_date = before_cancel_date
                        # Send About to Cancel Notification
                        sponsorship_to_cancel_template = self.env['takaful.message.template'].sudo().search(
                            [('template_name', '=', 'sponsorship_to_cancel')], limit=1)

                        subject = sponsorship_to_cancel_template.title
                        message = sponsorship_to_cancel_template.body + '\n' + _('Overdue Amount:') + ' %s' % str(
                            rec.overdue_amount)

                        user_id = self.env['res.users'].sudo().search(
                            [('partner_id', '=', partner_id.id)], limit=1)
                        push = self.env['takaful.push.notification'].sudo().create({
                            'user_id': user_id.id,
                            'title': subject,
                            'body': message,
                        })
                        for msg in cancel_message_type_ids:
                            if msg.tool_type == "sms":
                                push.sudo().send_sms_notification()

                            elif msg.tool_type == "email":
                                push.sudo().send_email_notification()
            else:
                rec.close_to_be_canceled_date = None

    # _logger.info("Bye, Manage Sponsorship Workflow Scheduler")

    # @api.multi
    def get_voucher_lines(self):
        """
        prepare voucher lines from details lines
        for voucher creation
        """
        self.ensure_one()
        if self.benefit_type == "orphan":
            if not self.env.user.company_id.widow_account_id:
                raise ValidationError(
                    _(''' Please set orphan restricted income account in settings '''))
            account_id = self.env.user.company_id.orphan_account_id.id
        elif self.benefit_type == "widow":
            if not self.env.user.company_id.widow_account_id:
                raise ValidationError(
                    _(''' Please set widow restricted income account in settings '''))
            account_id = self.env.user.company_id.widow_account_id.id

        lines = [
            {
                'name': self.code,
                'account_id': account_id,
                'price_unit': self.contribution_value,
                'quantity': 1,  # only one service
                'analytic_account_id': self.branch_custom_id.branch.analytic_account_id.id,
            }
        ]
        lines = [(0, 0, x) for x in lines]
        return lines

    # @api.multi
    def open_account_voucher(self):
        self.ensure_one()
        lines = self.get_voucher_lines()
        journal_id = False
        sudoConf = self.env['ir.config_parameter'].sudo()
        journal_id = sudoConf.get_param('odex_takaful_base.kafala_journal_id', default=False)  
        if not journal_id:
            raise ValidationError(
                _(''' Please set income journal in settings (kafala_journal_id Payment Journal)'''))

        company_id = self.env.user.company_id.id
        p = self.sponsor_id.partner_id if not company_id else self.sponsor_id.partner_id.with_company(company_id)

        rec_account = p.property_account_receivable_id
        pay_account = p.property_account_payable_id
        if not rec_account and not pay_account:
            raise ValidationError(
                _(''' Please set donor's payable and receivable accounts first '''))

        periods = self.env['fiscalyears.periods'].search(
            [('state', '=', 'open'),
             ('date_from', '<=', fields.Datetime.now()),
             ('date_to', '>=', fields.Datetime.now())])

        if not periods:
            raise ValidationError(
                _('No fiscal year periods in this date.'))

        data = {
            # 'name': self.code,
            # 'ref': self.code,
            # 'move_type': 'out_receipt',
            # 'date': fields.Datetime.now(),
            'invoice_date': fields.Datetime.now(),
            'invoice_date_due': fields.Datetime.now(),
            'narration': self.code,
            'company_id': self.env.user.company_id.id,
            'partner_id': self.sponsor_id.partner_id.id,
            'journal_id': int(journal_id),
            # 'account_id': self.sponsor_id.partner_id.property_account_receivable_id.id,
            'line_ids': lines,
            # 'pay_now': 'pay_now',
            # 'payment_journal_id':self.payment_journal_id.id,
            'sponsorship_id':self.id,
        }
        voucher_id = self.env['account.move'].create(data)
        self.voucher_ids = [(4,voucher_id.id)]

    def action_open_voucher_payement(self):
        """Open Payments for a voucher"""
        domain = [('sponsorship_id', '=', self.id or False)]
        context = dict(self.env.context or {})
        
        return {
            'name': _('voucher Payment'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(self.env.ref(
                'account.view_move_tree').id, 'tree'),
                (self.env.ref('account.view_move_form').id, 'form')],
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'target': 'current',
            'domain': domain,
            'context': context,
        }
    def create_new_sponsor(self):
        return {
            'name': 'Add New Sponsor',
            'type': 'ir.actions.act_window',
            'res_model': 'takaful.sponsor',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_company_type': 'person',
                'parent_model': self._name,  # Pass current model's name
                'parent_id': self.id,  # Pass current record's ID  # Pass the current record ID
            },
           # 'flags': {'form': {'action_buttons': True, 'options': {'mode': 'edit', 'close_on_save': True}}},
        }

class AccountVoucher(models.Model):
    _inherit = "account.move"

    sponsorship_id = fields.Many2one('takaful.sponsorship',string='Sponsorship', readonly=True,)
    payment_id = fields.Many2one('account.payment',string='Payment', copy=False)
    
    
    # @api.multi
    def action_move_line_create(self):
        '''
        Confirm the vouchers given in ids and create the journal entries for each of them
        '''        
        res = super(AccountVoucher, self).action_move_line_create()
        if res :
            self.write({'payment_id':self.move_id.line_ids.mapped('payment_id').id})
            
    @api.onchange('payment_journal_id')      
    def on_change_payment_journal_id(self):
        print("***********payment_journal_id******************")
        for rec in self:
            rec.account_id = rec.payment_journal_id.default_debit_account_id

class AnotherSponsors(models.Model):
    _name = "donate.for.another.person"

    sponsor_name = fields.Char(string="Sponsor Name")
    sponsor_phone = fields.Char(string="Sponsor Phone")
    sponsor_id_number = fields.Char(string="Sponsor ID Number")
    sponsorship_id = fields.Many2one('takaful.sponsorship')
    receive_messages = fields.Boolean(string='Receive messages?')

class DonationsDetailsLines(models.Model):
    _name = "donations.details.lines"

    donation_type = fields.Selection([('donation', 'Donation'), ('waqf', 'Waqf'), ('sponsorship', 'Sponsorship'), ],string='Donation Type')
    donation_name = fields.Many2one('donations.items', string="Donation Name" , domain="[('donation_type','=',donation_type),('show_donation_item','=',True)]")
    sponsorship_id = fields.Many2one('takaful.sponsorship', string="Sponsorship")
    donation_amount = fields.Float(string='Donation Amount')
    donation_mechanism = fields.Selection([('with_conditions', 'With Conditions'),('without_conditions', 'Without Conditions')],string='Donation Mechanism')
    benefit_type = fields.Selection([('orphan', 'Orphans'),('widow', 'Widows'),('both', 'Both')],string='Sponsorship Beneficiary Type',tracking=True)
    sponsorship_type = fields.Selection([('person', 'Individual'),('group', 'Group')],string='Sponsorship Type',tracking=True)
    gender = fields.Selection(selection=[('male', 'Male'), ('female', 'Female')], string="Gender")
    age_category_id = fields.Many2one('age.category', string='Age Category')
    education_status = fields.Selection(string='Education Status',selection=[('educated', 'educated'), ('illiterate', 'illiterate'),('under_study_age', 'Under Study Age')])
    education_level = fields.Many2one("education.level", string='Education Levels')
    benefit_id = fields.Many2one('family.member',string='Beneficiary Name',ondelete='set null',domain = "[('id', 'in',members_domain_ids)]")
    family_id = fields.Many2one('grant.benefit',string='Family',ondelete='set null',related="benefit_id.benefit_id")
    members_domain_ids = fields.Many2many(comodel_name='family.member', compute='_compute_domain_ids')
    benefit_ids = fields.Many2many('family.member',string='Beneficiaries Names')
    sponsorship_duration = fields.Selection([('temporary', 'Temporary'),('permanent', 'Permanent')],string='Sponsorship Type',default='permanent',tracking=True)
    start_date = fields.Date(string="Sponsorship Start Date", copy=False)
    end_date = fields.Date(string="Sponsorship End Date",compute='_compute_end_date')
    payment_option = fields.Selection([('month', 'Monthly'),('once', 'For Once')], string='Payment Option')
    payment_month_count = fields.Integer(string='Payment Month Count')
    fixed_value = fields.Boolean(string='Is Fixed Value?',related='donation_name.fixed_value')
    benefits_count = fields.Integer(string='Benefits Count',compute='_get_benefits_count')
    total_donation_amount = fields.Float(string='Total Donation Amount',compute='_get_total_donation_amount')

    @api.depends('start_date', 'payment_month_count')
    def _compute_end_date(self):
        for record in self:
            if record.start_date and record.payment_month_count:
                record.end_date = record.start_date + relativedelta(months=record.payment_month_count)
            else:
                record.end_date = False

    @api.depends('benefit_ids')
    def _get_benefits_count(self):
        for rec in self:
            rec.benefits_count = len(rec.benefit_ids)

    @api.depends('benefits_count','donation_amount')
    def _get_total_donation_amount(self):
        for rec in self:
           if rec.sponsorship_type == 'group':
              rec.total_donation_amount = rec.benefits_count * rec.donation_amount
           else :
               rec.total_donation_amount = rec.donation_amount

    @api.depends('gender', 'education_status', 'education_level', 'sponsorship_type', 'benefit_type', 'age_category_id')
    def _compute_domain_ids(self):
        for rec in self:
            # Create a domain
            rec.members_domain_ids = [(6, 0, [])]
            if rec.benefit_type == 'orphan' and rec.sponsorship_type:
                base_domain = \
                    [
                        ('state', 'in', ['second_approve', 'temporarily_suspended', 'suspended_first_approve']),
                        ('member_status', '=', 'benefit'),
                        '|',
                        ('relationn.relation_type', '=', 'daughter'),
                        ('relationn.relation_type', '=', 'son')
                    ]
                if rec.gender:
                    if rec.gender == 'female':
                        base_domain = [
                            ('state', 'in', ('second_approve', 'temporarily_suspended', 'suspended_first_approve')),
                            ('member_status', '=', 'benefit'), ('relationn.relation_type', '=', 'daughter')]
                    if rec.gender == 'male':
                        base_domain = [
                            ('state', 'in', ('second_approve', 'temporarily_suspended', 'suspended_first_approve')),
                            ('member_status', '=', 'benefit'), ('relationn.relation_type', '=', 'son')]
                if rec.education_status:
                    base_domain.append(('education_status', '=', rec.education_status))
                if rec.education_level:
                    base_domain.append(('education_levels', '=', rec.education_level.id))
                if rec.age_category_id:
                    base_domain.append(('age', '<=', rec.age_category_id.max_age))
                    base_domain.append(('age', '>=', rec.age_category_id.min_age))
                rec.members_domain_ids = self.env['family.member'].sudo().search(base_domain)
                domain = {'benefit_id': [('id', 'in', rec.members_domain_ids.ids)]}
                return {'domain': domain}
            if rec.benefit_type == 'widow' and rec.sponsorship_type:
                base_domain = [('state', 'in', ['second_approve', 'temporarily_suspended', 'suspended_first_approve']),
                               ('member_status', '=', 'benefit'), '|', ('relationn.relation_type', '=', 'mother'),
                               ('relationn.relation_type', '=', 'replacement_mother')]
                if rec.education_status:
                    base_domain.append(('education_status', '=', rec.education_status))
                if rec.education_level:
                    base_domain.append(('education_levels', '=', rec.education_level.id))
                if rec.age_category_id:
                    base_domain.append(('age', '<=', rec.age_category_id.max_age))
                    base_domain.append(('age', '>=', rec.age_category_id.min_age))
                rec.members_domain_ids = self.env['family.member'].sudo().search(base_domain)
                domain = {'benefit_id': [('id', 'in', rec.members_domain_ids.ids)]}
                return {'domain': domain}
            if rec.benefit_type == 'both' and rec.sponsorship_type:
                base_domain = [('state', 'in', ['second_approve', 'temporarily_suspended', 'suspended_first_approve']),
                               ('member_status', '=', 'benefit')]
                if rec.education_status:
                    base_domain.append(('education_status', '=', rec.education_status))
                if rec.education_level:
                    base_domain.append(('education_levels', '=', rec.education_level.id))
                if rec.age_category_id:
                    base_domain.append(('age', '<=', rec.age_category_id.max_age))
                    base_domain.append(('age', '>=', rec.age_category_id.min_age))
                rec.members_domain_ids = self.env['family.member'].sudo().search(base_domain)
                domain = {'benefit_id': [('id', 'in', rec.members_domain_ids.ids)]}
                return {'domain': domain}

    @api.onchange('donation_name')
    def onchange_donation_name(self):
        for rec in self:
            if rec.donation_name.fixed_value:
                rec.donation_amount = rec.donation_name.fixed_donation_amount

    @api.onchange('donation_type')
    def onchange_donation_type(self):
        for rec in self:
            if rec.donation_type == 'sponsorship':
                rec.donation_mechanism = 'with_conditions'

class PaymentDetailsLines(models.Model):
    _name = "payment.details.lines"

    payment_method = fields.Selection(selection=[("cash", "Cash"),("card", "Card"),("check", "Check"),("credit_card", "Credit Card"),("bank_transfer", "Bank Transfer"),("direct_debit", "Direct Debit")])
    donation_amount = fields.Float(string='Donation Amount')
    donation_date = fields.Date(string='Donation Date',default=lambda self: fields.Date.today())
    note = fields.Char(string='Note')
    journal_id = fields.Many2one('account.journal', string="Journal")
    points_of_sale = fields.Many2one('points.of.sale.custom', string="Point OF sale")
    sponsorship_id = fields.Many2one('takaful.sponsorship')
    bank_id = fields.Many2one('res.partner.bank',string="Sponsorship Bank")
    charity_journal_id = fields.Many2one('account.journal', string="charity Bank",related = 'points_of_sale.journal_id')
    name = fields.Char(string="Ref.",readonly=True)
    check_number = fields.Char(string='Check Number')
    account_payment_method = fields.Many2one('account.payment.method.line',domain="[('payment_type','=','inbound')]",string='Account Payment Method')
    branch_custom_id = fields.Many2one('branch.settings', string="Branch",related='sponsorship_id.branch_custom_id')
    sponsor_account_number = fields.Char(string='Sponsor Account Number')
    sa_iban = fields.Char('SA',default='SA',readonly=True)
    charity_bank_id = fields.Many2one('account.journal', string="charity Bank")
    bank_transfer_amount = fields.Float(string='Bank Transfer Amount')
    direct_debit_amount = fields.Float(string='Direct Debit Amount')
    payment_attachment = fields.Many2many('ir.attachment', 'rel_attachment_payment_details', 'payment_id','attachment_id', string='Payment Attachment')
    direct_debit_start_date = fields.Date(string='Direct Debit Start Date')
    direct_debit_end_date = fields.Date(string='Direct Debit End Date')

    @api.onchange('sponsor_account_number')
    def onchange_sponsor_account_number(self):
        if self.sponsor_account_number:
            # Check if the value is numeric before anything else
            if not self.sponsor_account_number.isdigit():
                raise ValidationError(_("The account number should contain only digits."))

            # Check if the account number contains exactly 22 digits
            if len(self.sponsor_account_number) != 22:
                raise ValidationError(_("The IBAN number must contain exactly 22 digits."))

    @api.onchange('branch_custom_id')
    def _onchange_branch_custom_id(self):
        domain = []
        for rec in self:
            domain = [
                ('branch_custom_ids', 'in', [rec.branch_custom_id.id]) ]
        return {'domain': {'points_of_sale': domain}}




    @api.model
    def create(self, vals):
        res = super(PaymentDetailsLines, self).create(vals)
        if not res.name or res.name == _('New'):
            res.name = self.env['ir.sequence'].sudo().next_by_code('payment.details.sequence') or _('New')
        return res
    @api.onchange('payment_method')
    def onchange_journal_id(self):
        for rec in self:
            # Build the dynamic domain
            domain = []
            if rec.payment_method == 'cash':
                domain = [
                    ('type','=','cash')
                ]
            if rec.payment_method == 'check':
                domain = [
                    '|',('type', '=', 'cash'),('type', '=', 'bank')
                ]
            return {'domain': {'journal_id': domain}}



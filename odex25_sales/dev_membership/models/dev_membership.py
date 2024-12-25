# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

from odoo import fields, models, api, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError, ValidationError


class DevMembership(models.Model):
    _name = 'dev.membership'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Dev Membership'
    _order = 'name desc'

    name = fields.Char(string='Name')
    date = fields.Date(string="Request Date", tracking=3, required=1, default=lambda self: datetime.now().date())
    from_date = fields.Date(string="Membership From Date", tracking=3, required=1,
                            default=lambda *a: (datetime.now().date()))
    to_date = fields.Date(string="Membership To Date", tracking=3)
    request_date = fields.Date(string="Cancell Date", tracking=3, readonly=1)
    partner_id = fields.Many2one('res.partner', string="Partner", domain="[('is_member', '=', True)]", tracking=2,
                                 required=1)
    id_no = fields.Char(string='Identification Number', related='partner_id.identification_number', store=True)
    phone = fields.Char(string='Phone', related='partner_id.phone', store=True)
    email = fields.Char(string='Email', related='partner_id.email', store=True)
    product_id = fields.Many2one('product.product', string="Membership Product",
                                 domain="[('is_membership', '=', True)]", tracking=2, required=1)
    membership_fees = fields.Float(string="Membership Fees")
    is_free = fields.Boolean(string="Is Free", related="product_id.is_free", )
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.company, required=1,
                                 tracking=3)
    duration = fields.Integer(string="Duration", )
    description = fields.Text(string="Description", related="product_id.description", readonly=False)
    interval = fields.Selection(string="Interval", selection=([
        ('days', 'Days'),
        ('month', 'Month'),
        ('year', 'Year')]), default='year', required=1)
    payment_state = fields.Selection(string='Payment State', related='invoice_id.payment_state')
    state = fields.Selection(string="State", selection=([
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('active', 'Active'),
        ('expire', 'Expire'),
        ('cancel', 'Cancel')]), default='draft', tracking=1)
    membership_id = fields.Many2one('dev.membership', string='Renew Membership')
    invoice_id = fields.Many2one('account.move', string='Invoice')
    user_id = fields.Many2one('res.users', string='Resposible', default=lambda self: self.env.user)
    cancel_reasone = fields.Many2one('cancellation.reason', string='Cancel Membership Reason')
    membrship_level = fields.Many2one('membership.level', string='Membrship level', store=True, required=False,
                                      compute='_compute_membership_level')

    def action_set_to_draft(self):
        self.ensure_one()
        if self.invoice_id and self.invoice_id.state != 'draft':
            raise UserError(_("Kindly The invoice is not in draft state, so it cannot be unlinked."))

        if self.invoice_id:
            self.invoice_id.sudo().write({'posted_before': False})
            self.invoice_id.sudo().unlink()
        self.state = 'draft'

    @api.onchange('product_id')
    def _onchange_membership_type(self):
        if self.product_id:
            if self.product_id.is_free:
                self.membership_fees = 0
            else:
                self.membership_fees = self.product_id.list_price
            self.duration = self.product_id.duration
            self.interval = self.product_id.interval

    @api.onchange('duration')
    def _onchange_duration(self):
        if self.duration and self.interval and self.membership_fees:
            self.membership_fees = self.duration * self.product_id.list_price

    @api.constrains('from_date')
    def _check_from_date(self):
        for rec in self:
            if not rec.from_date >= datetime.now().date():
                pass
                # raise ValidationError("Membership date should be greater than or equal to today's date!!")

    def make_activity_group(self):
        # templet_id = self.env.ref('dev_membership.template_membership_cancell')
        # templet2_id = self.env.ref('dev_membership.template_membership_cancell2')
        date_deadline = fields.Date.today()
        note = _('Membership  %s  is Cancelled') % self.name

        summary = _("Membership Cancellation")
        self.sudo().activity_schedule(
            'mail.mail_activity_data_todo', date_deadline,
            note=note,
            user_id=self.partner_id.user_id.id,
            res_id=self.id,
            summary=summary
        )
        self.sudo().activity_schedule(
            'mail.mail_activity_data_todo', date_deadline,
            note=note,
            user_id=self.user_id.id,
            res_id=self.id,
            summary=summary
        )

    @api.constrains('partner_id', 'from_date')
    def _check_if_membership_exists(self):
        membership_obj = self.env['dev.membership'].search(
            [('partner_id.id', '=', self.partner_id.id), ('state', 'in', ['draft', 'active', 'confirm']),
             ('id', '!=', self.id)])
        if membership_obj:
            for rec in self:
                for membership in membership_obj:
                    if rec.from_date < membership.to_date:
                        raise ValidationError(
                            _("You already have a membership from '%s' to '%s' !!!!") % (
                                membership.from_date, membership.to_date))

    @api.onchange('from_date', 'product_id', 'duration', 'interval')
    def onchange_from_date(self):
        if self.from_date and self.product_id:
            if self.interval == 'year':
                self.to_date = self.from_date + relativedelta(years=+self.duration) - relativedelta(days=1)
            elif self.interval == 'month':
                self.to_date = self.from_date + relativedelta(months=+self.duration) - relativedelta(days=1)
            elif self.interval == 'days':
                self.to_date = self.from_date + relativedelta(days=+self.duration)

    def action_confirm_membership(self):
        if self.product_id.nationality_ids:
            if self.partner_id.nationality_id not in self.product_id.nationality_ids:
                raise ValidationError(_("The member's nationality does not meet the membership requirements"))
        if self.product_id.age > 0 and self.partner_id.age < self.product_id.age:
            raise ValidationError(_('The member must be at least %s years old.') % self.product_id.age)
        if self.product_id.max_age > 0 and self.partner_id.age > self.product_id.max_age:
            raise ValidationError(_('The member must not be more than %s years old.') % self.product_id.max_age)
        if self.product_id.gender and self.partner_id.gender != self.product_id.gender:
            raise ValidationError(_('Membership is only  %s allowed') % self.product_id.gender)

        if self.membership_fees < (self.product_id.list_price * self.duration):
            raise ValidationError(
                _("Membership fees cannot be less than %s .") % (self.product_id.list_price * self.duration,))
        if self.duration < self.product_id.duration:
            raise ValidationError(
                _("Duration cannot be less than the default value in Setting of membrship type.%s'") % self.product_id.duration)
        self.state = 'confirm'

    def action_active_membership(self):
        # Search for the last membership of the partner
        last_membership = self.env['dev.membership'].search([
            ('partner_id', '=', self.partner_id.id),
            ('state', '=', 'cancel')
        ], limit=1, order="to_date desc")
        # Handle sequence generation for new or renewed memberships
        sequence_code = 'membership.no.sequence'

        if not self.invoice_id and not self.is_free:
            raise ValidationError(_('Please Create Membership Invoice'))
        if self.invoice_id.payment_state not in ['paid', 'in_payment'] and not self.is_free:
            raise ValidationError(
                _('Membership Invoice is not paid.\nPlease pay the membership invoice and activate the membership.'))
        else:
            # Assuming you have a field to track payment state
            self.payment_state = self.invoice_id.payment_state
        if not self.partner_id.membrship_no or last_membership:
            # Generate new sequence number if it's the first membership or it's a renewal after cancellation
            self.partner_id.membrship_no = self.env['ir.sequence'].next_by_code(sequence_code) or _('New')
        # else:
        #     if self.state=='confirm':
        #         self.partner_id.membrship_no = self.env['ir.sequence'].next_by_code(sequence_code) or _('New')
        self.state = 'active'
        self.partner_id.check_active_membership()
        
    def action_cancel_membership(self):
        self.state = 'cancel'
        self.partner_id.check_active_membership()

    
    @api.model
    def create(self, vals):
        res = super(DevMembership, self).create(vals)
        sequence = self.env['ir.sequence'].next_by_code('seq.dev.membership') or 'New'
        res.name = sequence
        return res

    def unlink(self):
        for rec in self:
            if rec.state not in ('draft', 'cancel'):
                raise UserError("You are not allowed to delete this record!!")
        return super(DevMembership, self).unlink()

    def membership_send_by_mail(self):
        self.ensure_one()
        template_id = self.env['ir.model.data'].xmlid_to_res_id('dev_membership.template_membership',
                                                                raise_if_not_found=False)
        ctx = {
            'default_model': 'dev.membership',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'force_email': True,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    def membership_auto_expire(self):
        current_date = datetime.now().date()
        membership_ids = self.env['dev.membership'].search([('state', '=', 'active'),
                                                            ('to_date', '<=', current_date)])
        template_id = self.env.ref('dev_membership.dev_membership_expired_mail_template')
        for membership in membership_ids:
            membership.state = 'expire'
            membership.partner_id.check_active_membership()

            # template_id.send_mail(membership.id, force_send=True)
            if membership.user_id:
                membership.message_post(
                    body=_("The Membership %s was expired on  %s") % (membership.name, membership.to_date),
                    subject=_("Auto Expire Membership"),
                    partner_ids=[membership.user_id.partner_id.id],
                    message_type='notification',  #
                    author_id=self.env.user.partner_id.id,
                )


    def membership_reminder_email_cron(self):
        membership_pool = self.env['dev.membership']
        tmpl_id = self.env.ref('dev_membership.dev_membership_expire_reminder_mail_template')
        days_before = self.env['ir.config_parameter'].get_param('dev_membership.days_before')
        if tmpl_id:
            date = datetime.now().date() + relativedelta(days=int(days_before))
            membership_ids = membership_pool.search([('state', '=', 'active'),
                                                     ('to_date', '=', date)])

            for membership in membership_ids:

                # tmpl_id.send_mail(membership.id, force_send=True)

                if membership.user_id:
                    membership.message_post(
                        body=_("The Membership %s is about to expire on  %s") % (membership.name, membership.to_date),
                        subject=_("Membership Expire Reminder"),
                        partner_ids=[membership.user_id.partner_id.id],
                        message_type='notification',
                        author_id=self.env.user.partner_id.id,
                    )

    def cancell2_membership_reminder_email_cron(self):
        membership_pool = self.env['dev.membership']
        post_expiry_period = self.env['ir.config_parameter'].get_param('dev_membership.post_expiry_period')
        cancel_reason = self.env['ir.config_parameter'].get_param('dev_membership.cancellation_reason')
        if post_expiry_period:
            try:
                post_expiry_period = int(post_expiry_period)
            except ValueError:
                post_expiry_period = 0

            date = fields.Date.today() - relativedelta(days=int(post_expiry_period))
            membership_ids = membership_pool.search([
                ('state', '=', 'expire'),
                ('to_date', '=', date), ('membership_id', '=', False)
            ])
            for membership in membership_ids:
                existing_cancel_request = self.env['membership.cancellation.request'].search([
                    ('membership_id', '=', membership.id),
                    ('state', '=', 'draft')
                ], limit=1)
                if not existing_cancel_request:
                    self.env['membership.cancellation.request'].create({
                        'membership_id': membership.id,
                        'member_id': membership.partner_id.id,
                        'request_date': fields.Datetime.now(),
                        'state': 'draft',
                        'cancel_reason': cancel_reason
                    })

        return True

    def membership_secand_reminder_email_cron(self):
        membership_pool = self.env['dev.membership']
        tmpl_id = self.env.ref('dev_membership.dev_membership_expire_second_reminder_mail_template')
        days_before_second = self.env['ir.config_parameter'].get_param('dev_membership.days_before_second')
        if tmpl_id and days_before_second:
            try:
                days_before_second = int(days_before_second)
            except ValueError:
                days_before_second = 0

            date = datetime.now().date() + relativedelta(days=days_before_second)
            membership_ids = membership_pool.search([
                ('state', '=', 'active'),
                ('to_date', '=', date)
            ])
            for membership in membership_ids:
                # tmpl_id.send_mail(membership.id, force_send=True)
                if membership.user_id:
                    membership.message_post(
                        body=_("The Membership %s is about to expire on  %s") % (membership.name, membership.to_date),
                        subject=_("Membership Expire Reminder"),
                        partner_ids=[membership.user_id.partner_id.id],
                        message_type='notification',
                        author_id=self.env.user.partner_id.id,
                    )
        return True

    def datetime_convert(self):
        convert_date = self.to_date.strftime("%d-%m-%Y")
        return convert_date

    def create_membership_invoice(self):
        vals = {'move_type': 'out_invoice',
                'partner_id': self.partner_id.id,
                'ref': self.name,
                'invoice_line_ids': [
                    (0, None, {'product_id': self.product_id.id, 'quantity': 1, 'price_unit': self.membership_fees,
                               'tax_ids': [(6, 0, self.product_id.taxes_id.ids)]})
                ]
                }
        invoice_id = self.env['account.move'].create(vals)
        self.invoice_id = invoice_id and invoice_id.id or False

    def view_invoice(self):
        if self.invoice_id:
            ctx = dict(create=False)
            return {
                'type': 'ir.actions.act_window',
                'name': 'Invoice',
                'res_model': 'account.move',
                'domain': [('id', '=', self.invoice_id.id)],
                'view_mode': 'tree,form',
                'target': 'current',
                'context': ctx,
            }

    def view_membership(self):
        if self.membership_id:
            ctx = dict(create=False)
            return {
                'type': 'ir.actions.act_window',
                'name': 'Membership',
                'res_model': 'dev.membership',
                'domain': [('id', '=', self.membership_id.id)],
                'view_mode': 'tree,form',
                'target': 'current',
                'context': ctx,
            }

    @api.depends('membership_fees', 'duration')
    def _compute_membership_level(self):
        for record in self:
            total_fees = record.membership_fees
            total_duration = record.duration

            # Search for memberships to sum fees and duration
            memberships = self.env['dev.membership'].search([
                ('partner_id', '=', record.partner_id.id),
                ('to_date', '<', record.from_date),
                ('state', 'in', ['expire', 'active', 'cancel'])
            ])

            for membership in memberships:
                total_fees += membership.membership_fees
                total_duration += membership.duration

            # Search for membership level based on the total fees and duration
            level_by_fees = self.env['membership.level'].search([
                ('min', '<=', total_fees),
                ('years', '<=', total_duration)
            ], limit=1, order='sequence desc')

            # Update the membership level
            record.membrship_level = level_by_fees




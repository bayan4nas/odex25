# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, Warning
from dateutil.parser import parse
import re


class IrActionsServer(models.Model):
    _inherit = 'ir.actions.server'

    groups_id = fields.Many2many('res.groups', 'res_groups_server_rel', 'uid', 'gid', string='Groups')


class TakafulSponsor(models.Model):
    # _inherit = 'res.partner'
    _name = 'takaful.sponsor'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _inherits = {'res.partner': 'partner_id'}

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if not args:
            args = []

            # Extend the domain filter with custom search conditions
        domain = ['|', ('name', operator, name),('id_number', operator, name)]

        # Combine domain filter with any existing args (domain filter in Many2one)
        partners = self.search(domain + args, limit=limit)

        return partners.name_get()

    partner_id = fields.Many2one('res.partner', string='Partner', required=True,ondelete='cascade', copy=False)
    user_id = fields.Many2one('res.users', string="Related User")
    sponsor_title = fields.Many2one('res.partner.title',string='Title')

    account_number = fields.Char(string="Account Number")
    bank_entity_name = fields.Char(string="Bank Entity Name")

    #Location
    branch_custom_id = fields.Many2one('branch.settings', string="Branch")
    district_id = fields.Many2one('res.districts', string="District", domain="[('branch_custom_id','=',branch_custom_id)]")

    # New Added
    notify_by_app = fields.Boolean(string='Notify By App', default=True)
    notify_by_sms = fields.Boolean(string='Notify By SMS', default=True)
    notify_for_pay = fields.Boolean(string='Paying Notify By App', default=True)
    notify_pay_by_app = fields.Boolean(string='Paying Notify By App', default=True)
    notify_pay_by_sms = fields.Boolean(string='Paying Notify By SMS', default=True)
    
    name_in_certificate = fields.Boolean(string='Beneficiaries Names In Certificate', default=True)
    type_in_certificate = fields.Boolean(string='Beneficiaries Type In Certificate', default=True)
    duration_in_certificate = fields.Boolean(string='Sponsorship Duration In Certificate', default=True)

    notify_month_day = fields.Integer(string="Notify Month Day", default=1)
    wait_cancel_day = fields.Integer(string="Waiting For Cancellation", default=2)
    # operation_ids = fields.One2many('takaful.sponsor.operation', 'sponsor_id', string="Operations Records")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('verified', 'Verified')
    ], string='State',default='draft', tracking=True)

    _sql_constraints = [
        ('id_number_uniq', 'unique (id_number)', 'The ID Number Already Exist!'),
        ('mobile_uniq', 'unique (mobile)', 'The Mobile Already Exist!'),
        ('phone_uniq', 'unique (phone)', 'The Phone Already Exist!'),
        ('user_id_uniq', 'unique (user_id)', 'The User Already Exist!'),
        ('email_uniq', 'unique (email)', 'The Email Already Exist!'),
    ]

    @api.onchange('company_type', 'first_name', 'second_name', 'middle_name', 'family_name')
    def get_partner_name(self):
        if self.company_type == 'person':
            self.name = ''
            if all([self.second_name, self.first_name, self.middle_name, self.family_name]):
                self.name = self.first_name + " " + self.second_name + " " + self.middle_name + " " + self.family_name
            elif all([self.second_name, self.first_name, self.middle_name, self.family_name, self.sponsor_title]):
                self.name = self.sponsor_title.name + " " + self.first_name + " " + self.second_name + " " + self.middle_name + " " + self.family_name
        else:
            self.second_name = ''
            self.first_name = ''
            self.middle_name = ''
            self.family_name = ''

    @api.onchange('id_number','email')
    def onchange_id_number(self):
        for rec in self:
            res_partner_duplicated = self.env['res.partner'].search([('id_number','=',rec.id_number),('id_number','!=',False)],limit=1)
            duplicated_record = self.search([('id_number','=',rec.id_number)],limit=1)
            if rec.id_number and not re.match(r'^\d{10}$', rec.id_number):
                raise ValidationError(_("ID number must contain exactly 10 digits."))
            if duplicated_record or res_partner_duplicated:
                raise ValidationError(_("The ID number already exists in sponsor with name"))
            duplicated_record_same_email = self.search([('email','=',rec.id_number)],limit=1)
            if duplicated_record_same_email and duplicated_record_same_email.email != False:
                raise ValidationError(_("email already exists in sponsor with name %s")%duplicated_record_same_email.name)

    def _compute_operation_count(self):
        # Get operation_count
        operation_count = self.env['takaful.sponsor.operation'].sudo().search_count([('sponsor_id', '=', self.id)])

        if operation_count >0:
            self.operation_count = operation_count
        else:
            self.operation_count = 0

    operation_count = fields.Integer(
        compute='_compute_operation_count',
        string="# Of Operations",
        readonly=True
    )

    def _compute_kafalat_count(self):
        # Get kafalat
        kafalat_count = self.env['takaful.sponsorship'].sudo().search_count([('sponsor_id', '=', self.id)])

        if kafalat_count >0:
            self.kafalat_count = kafalat_count
        else:
            self.kafalat_count = 0

    kafalat_count = fields.Integer(
        compute='_compute_kafalat_count',
        string="# of Kafalat",
        readonly=True
    )

    def _compute_contribution_count(self):
        # The current user may not have access rights for contributions.
        for partner in self:
            try:
                partner.contribution_count = len(partner.id) * 2
            except Exception:
                partner.contribution_count = 50

    contribution_count = fields.Integer(
        compute='_compute_contribution_count',
        string="# of Contributions",
        readonly=True
    )

    active_counts = fields.Integer(
        string="Active Sponsors Count",
    )
    active = fields.Boolean(default=True)

    def _compute_gift_count(self):
        # The current user may not have access rights for gifts.
        for partner in self:
            try:
                partner.gift_count = len(partner.id) * 3
            except Exception:
                partner.gift_count = 75

    gift_count = fields.Integer(
        compute='_compute_gift_count',
        string="# of Gifts",
        readonly=True
    )

    #Validition here
    def check_bank_info_value(self):
        # all values true
        bank_info = [self.account_number,
                 self.iban,
                 self.bank_id,
                 self.bank_entity_name,
                ]

        res = all(bank_info)
        return res

    # New Added Here
    # New staff ..
    
    # @api.multi
    def unlink(self):
        for record in self:
            if record.active:
                if record.user_id:
                    record.user_id.sudo().write({
                        "active": False
                    })
                record.active = False
            else:
                raise UserError(_('Sponsor is already inactive'))

    # @api.multi
    def on_activate_sponsor_multi(self):
        for record in self:
            if not record.active:
                if record.user_id:
                    record.user_id.sudo().write({
                        "active": True
                    })
                record.active = True
            else:
                raise UserError(_('Sponsor is already active'))

    @api.model
    def create(self, values):
        name = values.get('name', False)
        company_type = values.get('company_type')

        if name is False and company_type == 'person':
            sponsor_title = values.get('sponsor_title')
            first_name = values.get('first_name')
            second_name = values.get('second_name')
            middle_name = values.get('middle_name')
            family_name = values.get('family_name')
            name = self.sponsor_title.browse(sponsor_title).name + " " + first_name + " " + second_name + " " + middle_name + " " + family_name
            values.update({'name': name})

        values.update({'lang': 'ar_001'})
        values.update({'tz': 'Asia/Riyadh'})
        values.update({'account_type':'sponsor'})

        res = super(TakafulSponsor, self).create(values)
        # Automatically update the sponsor_id field of the parent record
        context = self.env.context
        if context.get('parent_model') == 'takaful.sponsorship' and context.get('parent_id'):
            parent_record = self.env[context['parent_model']].browse(context['parent_id'])
            parent_record.sponsor_id = res.id
        if not res.user_id:
            res = res.sudo().create_user(res)

        res.partner_id = res.user_id.partner_id.id

        return res

    def create_user(self, res):
        for follower in res['message_follower_ids']:
            follower.sudo().unlink()
        if not res.partner_id:
            partner = res.create_partner()
        # If you add  'no_reset_password' to the context to True, it won't send an email. 
        # You can then set the password manually (and find a way to let the user know it).
        if res.company_type == 'company':
            user = self.env['res.users'].sudo().with_context(no_reset_password=False).create({
                'name': res.name,
                # 'user_type': 'company',
                'login': res.id_number if not res.email else res.email,
                'phone': res.mobile,
                'mobile': res.mobile,
                'partner_id': res.partner_id.id,
                'active': True,
                'city': res.city_id.name if res.city_id else False,
                'lang':'ar_001',
                'tz': 'Asia/Riyadh',
            })
        else:
            user = self.env['res.users'].sudo().with_context(no_reset_password=False).create({
                'name': res.name,
                'first_name': res.first_name,
                'second_name': res.second_name,
                'middle_name': res.middle_name,
                'family_name': res.family_name,
                # 'user_type': 'person',
                'login': res.id_number if not res.email else res.email,
                'phone': res.mobile,
                'mobile': res.mobile,
                'partner_id': res.partner_id.id,
                'active': True,
                'city': res.city_id.name if res.city_id else False,
                'lang':'ar_001',
                'tz': 'Asia/Riyadh',
            })

        # Add groups to the user as sponsor
        user.sudo().write({'groups_id': [
            # in odoo relation field accept a list of commands
            # command 4 means add the id in the second position must be an integer
            # ref return an object so we return the id
            ( 4, self.env.ref('odex_takaful.takaful_group_user_sponsor').id),
            ]
        })

        res.user_id = user.id
        return res

    # @api.multi
    def action_open_sponsor_operation(self):
        """Open Operations History for a Sponsor"""
        domain = [('sponsor_id', '=', self.id or False)]
        context = dict(self.env.context or {})
        context['default_sponsor_id'] = self.id or False

        return {
            'name': _('Sponsor Operations'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'view_id': False,
            'res_model': 'takaful.sponsor.operation',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': domain,
            'context': context,
        }

    # @api.multi
    def view_sponsorship_action(self):
        """List Sponsorships For The Sponsor"""
        domain = [('sponsor_id', '=', self.id or False)]
        context = dict(self.env.context or {})
        context['default_sponsor_id'] = self.id or False

        # view = self.env.ref('odex_takaful.takaful_sponsorship_tree')
        return {
            'name': _('Sponsorships'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'view_id': False,
            'res_model': 'takaful.sponsorship',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': domain,
            'context': context,
        }

    @api.model
    def get_active_sponsors_users(self):
        sponsors_users = self.env['res.users'].sudo().search([
            ("active", "=", True), 
            ("groups_id", "=", self.env.ref("odex_takaful.takaful_group_user_sponsor").id)])#self.env['res.users'].sudo().search([])
        
        count = len(sponsors_users) or 0
        sponsors = self.env['takaful.sponsor'].sudo().search([])
        for rec in sponsors:
            rec.update({
                "active_counts": count,
                })

    def show_active_sponsor_report_report(self):
        self.sudo().get_active_sponsors_users()
        ctx = self.env.context.copy()
        return {
            'name': _('Active Sponsors Count Report'),
            'type': 'ir.actions.act_window',
            'res_model': 'takaful.sponsor',
            'view_type': 'form',
            'view_mode': 'pivot',
            'view_id': self.env.ref('odex_takaful.active_sponsor_report_pivot_view').id,
            'target': 'main',
            'context': ctx,
        }


class TakafulSponsorOperation(models.Model):
    _name = 'takaful.sponsor.operation'
    # _rec_name = 'sponsor_id'

    name = fields.Char(string="Operation Name")
    title = fields.Char(string="Operation Title")
    sponsor_id = fields.Many2one(
        'takaful.sponsor',
        string='The Sponsor',
        ondelete='set null'
    )
    benefit_ids = fields.Many2many(
        'grant.benefit',
        string='Beneficiaries'
    )
    benefit_id = fields.Many2one(
        'grant.benefit',
        string='Beneficiary',
        ondelete='set null'
    )
    benefit_type = fields.Selection([
        ('orphan', 'Orphans'),
        ('widow', 'Widows'),
        ('general', 'General')],
        string='Beneficiaries Type',
        compute='_compute_benefit_type_value',
        related=False,
        readonly=True,
    )
    operation_type = fields.Selection([
        ('sponsorship', 'Sponsorship'),
        ('contribution', 'Needs Contribution'),
        ('gift', 'Financial Gift')],
        string='Operation Type',
    )
    date = fields.Date(string="Date", default=fields.Date.today)
    operation_on = fields.Datetime(string="Operation Time", default=fields.Datetime.now)
    month = fields.Integer(string="The Month", compute='_compute_period_filter')
    origin_id = fields.Integer(readonly=True)
    period_code = fields.Char(string="Period Code", compute='_compute_period_filter')
    amount = fields.Float(string="Amount")

    def _compute_period_filter(self):
        """ Extract period code from date """   
        for rec in self: 
            if rec.date:
                date = parse(str(rec.date)).date()
                rec.period_code = date.strftime("%Y_%m")
                rec.month = int(date.strftime("%m"))

    def _compute_benefit_type_value(self):
        for rec in self:
            b_type = []
            if rec.benefit_ids:
                for i in rec.benefit_ids:
                    b_type.append(i.benefit_type)
            if rec.benefit_id:
                b_type.append(rec.benefit_id.benefit_type)
            if 'orphan' in b_type and 'widow' not in b_type:
                rec.benefit_type = 'orphan'
            if 'widow' in b_type and 'orphan' not in b_type:
                rec.benefit_type = 'widow'
            if 'widow' in b_type and 'orphan' in b_type:
                rec.benefit_type = 'general'
            if b_type == []:
                rec.benefit_type = ''

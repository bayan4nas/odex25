# -*- coding: utf-8 -*-
from odoo import models, fields, _, api
from odoo.exceptions import ValidationError
from lxml import etree
import json
from odoo.exceptions import UserError
from datetime import date
from odoo.tools import config
from dateutil.relativedelta import relativedelta


class GrantBenefit(models.Model):
    _inherit = 'grant.benefit'

    STATE_SELECTION = [
        ('draft', 'الباحث الاجتماعي'),
        ('confirm', 'Primary Care Director Accreditation'),
        ('validate', 'Beneficiary Services Center Director Approval'),
        ('review', 'Review'),
        ('approve', 'Approve'),
        ('approved', 'Approved'),
        ('closed', 'Done'),
        ('cancelled', 'Rejected'),

    ]

    previous_state = fields.Selection(STATE_SELECTION, string="Previous State")
    need_calculator = fields.Selection([('high', 'High Need'), ('medium', 'Medium Need'), ('low', 'Low Need'), ],
                                       readonly=1, string="Need Calculator", )
    beneficiary_category = fields.Selection(related='detainee_file_id.beneficiary_category',
                                            string='Beneficiary Category')
    # name = fields.Char(string="Folder State", readonly=True)

    total_income = fields.Float(string="Total Income", store=True, readonly=True)
    expected_income = fields.Float(string="Expected  Income", readonly=True)
    name_member = fields.Char(string="Expected  Income", compute='_compute_member_name', readonly=True)
    researcher_insights = fields.Text('Researcher Insights')
    researcher_id = fields.Many2one("committees.line", string='Researcher Name')
    folder_state = fields.Selection([('Active', 'active'), ('not_active', 'Not Active')], string='Folder State')

    # related = 'benefit_breadwinner_ids[0].member_name.building_number'
    building_number = fields.Integer(string='Building Number', compute='_compute_breadwinner_address', readonly=False,
                                     store=False)
    sub_number = fields.Integer(string='Sub Number', compute='_compute_breadwinner_address')
    additional_number = fields.Integer(string='Additional Number', compute='_compute_breadwinner_address')
    street_name = fields.Char(string='Street Name', compute='_compute_breadwinner_address')
    city = fields.Many2one("res.country.city", string='City', compute='_compute_breadwinner_address')

    district_name = fields.Many2one(
        'res.district',
        string='District', compute='_compute_breadwinner_address')

    postal_code = fields.Char(string='Postal Code', compute='_compute_breadwinner_address')
    national_address_code = fields.Char(string='National address code', compute='_compute_breadwinner_address')

    @api.depends(
        'benefit_breadwinner_ids.member_name.building_number',
        'benefit_breadwinner_ids.member_name.sub_number',
        'benefit_breadwinner_ids.member_name.additional_number',
        'benefit_breadwinner_ids.member_name.street_name',
        'benefit_breadwinner_ids.member_name.district_id',
        'benefit_breadwinner_ids.member_name.city',
        'benefit_breadwinner_ids.member_name.postal_code',
        'benefit_breadwinner_ids.member_name.national_address_code',
    )
    def _compute_breadwinner_address(self):
        for rec in self:
            if rec.benefit_breadwinner_ids:
                member = rec.benefit_breadwinner_ids[0].member_name
                rec.building_number = member.building_number
                rec.sub_number = member.sub_number
                rec.additional_number = member.additional_number
                rec.street_name = member.street_name
                rec.district_name = member.district_id
                rec.city = member.city
                rec.postal_code = member.postal_code
                rec.national_address_code = member.national_address_code
            else:
                rec.building_number = rec.sub_number = rec.additional_number = False
                rec.street_name = rec.district_name = rec.city = False
                rec.postal_code = rec.national_address_code = False

    @api.depends('rent_start_date', 'rent_end_date')
    def compute_rent_period(self):
        for record in self:
            if record.rent_start_date and record.rent_end_date:
                delta = relativedelta(record.rent_end_date, record.rent_start_date)
                years = delta.years
                months = delta.months
                days = delta.days

                def arabic_plural(value, singular, dual, plural):
                    if value == 1:
                        return f"1 {singular}"
                    elif value == 2:
                        return dual
                    elif 3 <= value <= 10:
                        return f"{value} {plural}"
                    else:
                        return f"{value} {singular}"

                year_txt = arabic_plural(years, "سنة", "سنتان", "سنوات")
                month_txt = arabic_plural(months, "شهر", "شهران", "أشهر")
                day_txt = arabic_plural(days, "يومًا", "يومان", "أيام")

                parts = []
                if years:
                    parts.append(year_txt)
                if months:
                    parts.append(month_txt)
                if days:
                    parts.append(day_txt)

                rtl_marker = '\u200F'
                record.period_text = rtl_marker + " و ".join(parts) if parts else rtl_marker + "0 يوم"
            else:
                record.period_text = "\u200Fالمدة غير متوفرة"

    @api.depends('benefit_member_ids')
    def _compute_member_name(self):
        self.name_member = ''
        for lin in self:
            for rec in lin.benefit_member_ids:
                if rec.is_breadwinner:
                    lin.name_member = rec.member_id.name
                    break

    def action_done(self):
        self.state = 'approved'

    # start
    def _convert_to_monthly(self, amount, periodicity):
        mapping = {
            'monthly': 1,
            'every_three_months': 3,
            'every_six_months': 6,
            'every_nine_months': 9,
            'annually': 12,
            'two_years': 24,
        }
        return amount / mapping.get(periodicity or 'monthly', 1)

    def _get_total_net_income(self):
        income = sum(self._convert_to_monthly(line.salary_amount, line.revenue_periodicity)
                     for line in self.salary_ids)
        expenses = sum(self._convert_to_monthly(line.amount, line.revenue_periodicity)
                       for line in self.expenses_ids)
        return income - expenses

    def _get_expected_family_income(self):
        config_param = self.env['ir.config_parameter'].sudo()
        base_line_value = float(config_param.get_param('trahum_benefits.base_line_value', ))
        expected = 0.0
        for member in self.benefit_member_ids:
            if member.is_breadwinner:
                expected += base_line_value
            elif member.member_id and member.member_id.birth_date:
                age = self._calculate_age(member.member_id.birth_date)
                if age >= 18:
                    expected += base_line_value * 0.5
                else:
                    expected += base_line_value * 0.3
        self.expected_income = expected
        return expected

    def _calculate_age(self, birth_date):
        today = date.today()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

    def _compute_need_calculator(self):
        for record in self:
            net_income = record._get_total_net_income()
            record.total_income = net_income
            expected_income = record._get_expected_family_income()

            if expected_income == 0:
                record.need_calculator = False
                continue

            percent = (net_income / expected_income) * 100

            if percent <= 30:
                record.need_calculator = 'high'
            elif percent <= 60:
                record.need_calculator = 'medium'
            else:
                record.need_calculator = 'low'

    # end
    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        res = super(GrantBenefit, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                        submenu=submenu)
        if view_type == 'form':
            doc = etree.XML(res['arch'])

            for node in doc.xpath("//field"):
                modifiers = json.loads(node.get("modifiers", '{}'))

                if 'readonly' not in modifiers:
                    modifiers['readonly'] = [('state', 'not in', ['draft'])]
                else:
                    if not isinstance(modifiers['readonly'], bool):
                        if ('state', 'not in', ['draft']) not in modifiers['readonly']:
                            modifiers['readonly'].insert(0, '|')
                            modifiers['readonly'].append(('state', 'not in', ['draft']))

                node.set("modifiers", json.dumps(modifiers))

            res['arch'] = etree.tostring(doc, encoding='unicode')
        return res

    def write(self, vals):
        for rec in self:
            if 'state' in vals and rec.state != vals['state']:
                rec.previous_state = rec.state
                print('state = ', rec.state)
        return super().write(vals)

    def action_open_salary_income(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'salary.line',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('odex_benefit.view_salary_line_tree').id, 'tree'),
                (self.env.ref('odex_benefit.view_salary_line_form').id, 'form'),
            ],
            # 'domain': [('member_id', '=', self.id)],
            'target': 'current',
        }

    def action_open_expenses(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'expenses.line',
            'view_mode': 'tree,form',
            'views': [
                (self.env.ref('odex_benefit.view_expense_line_tree').id, 'tree'),
                (self.env.ref('odex_benefit.view_expense_line_form').id, 'form'),
            ],
            # 'domain': [('member_id', '=', self.id)],
            'target': 'current',
        }

    def action_open_family_member(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'family.member',
            'view_mode': 'tree,form',
            'domain': [
                ('id', 'in', (
                        self.benefit_member_ids.mapped('member_id').ids +
                        self.benefit_breadwinner_ids.mapped('member_name').ids
                ))
            ],
            'target': 'current',
        }

    # add new customuzation
    state = fields.Selection(STATE_SELECTION, default='draft', tracking=True)
    detainee_file_id = fields.Many2one('detainee.file', string="Detainee File", tracking=True, required=1)

    benefit_member_ids = fields.One2many('grant.benefit.member', 'grant_benefit_id', string="Benefit Member")
    benefit_breadwinner_ids = fields.One2many('grant.benefit.breadwinner', 'grant_benefit_ids',
                                              string="Benefit breadwinner", required=1)

    member_count = fields.Integer(string="Members Count", compute="_compute_member_count", readonly=1)

    benefit_member_count = fields.Integer(
        string=" Count member",
        compute="_compute_benefit_counts",
        store=True,
        readonly=True
    )

    benefit_breadwinner_count = fields.Integer(
        string="Benefit Breadwinner Count",
        compute="_compute_benefit_counts",
        store=True,
        readonly=True
    )

    natural_income = fields.Float(
        string="Natural Income",
        compute="_compute_natural_income",
        store=True,
        readonly=True
    )

    need_ratio = fields.Float(
        string="Need Value Ratio",
        compute="_compute_need_ratio",
        store=True,
        readonly=True
    )
    family_need_class_id = fields.Many2one(
        'family.need.category',
        string="Family Need Category",
        compute="_compute_family_need_class",
        store=True
    )

    @api.depends('need_ratio')
    def _compute_family_need_class(self):
        for rec in self:
            rec.family_need_class_id = False

            ratio = round(rec.need_ratio / 100, 2)
            category = self.env['family.need.category'].sudo().search([
                ('min_need', '<=', ratio),
                ('max_need', '>=', ratio)
            ], order='min_need asc', limit=1)

            if category:
                rec.family_need_class_id = category.id

    @api.depends('total_salary', 'natural_income')
    def _compute_need_ratio(self):
        for rec in self:
            if rec.natural_income:
                ratio = (rec.total_salary / rec.natural_income) * 100
                rec.need_ratio = min(ratio, 100)
            else:
                rec.need_ratio = 0.0

    @api.depends('benefit_breadwinner_ids',
                 'members_under_18',
                 'members_18_and_above')
    def _compute_natural_income(self):
        ratio_parent = float(
            self.env['ir.config_parameter'].sudo().get_param('trahum_benefits.ratio_parent', 0)
        )
        ratio_under_18 = float(
            self.env['ir.config_parameter'].sudo().get_param('trahum_benefits.ratio_under_18', 0)
        )
        ratio_above_18 = float(
            self.env['ir.config_parameter'].sudo().get_param('trahum_benefits.ratio_above_18', 0)
        )
        base_line = float(
            self.env['ir.config_parameter'].sudo().get_param('trahum_benefits.base_line_value', 0)
        )
        for rec in self:
            filtered = rec.benefit_breadwinner_ids.filtered(
                lambda bw: bw.relation_id and not bw.relation_id.exclude_need
            )
            breadwinner_count = len(filtered)
            under_18_count = rec.members_under_18
            above_18_count = rec.members_18_and_above

            rec.natural_income = (
                    (breadwinner_count * ratio_parent * base_line) +
                    (under_18_count * ratio_under_18 * base_line) +
                    (above_18_count * ratio_above_18 * base_line)
            )

    @api.depends('benefit_member_ids', 'benefit_breadwinner_ids', 'benefit_breadwinner_ids.relation_id',
                 'benefit_breadwinner_ids.relation_id.exclude_need', )
    def _compute_benefit_counts(self):
        for rec in self:
            rec.benefit_member_count = len(rec.benefit_member_ids) + len(rec.benefit_breadwinner_ids)
            filtered = rec.benefit_breadwinner_ids.filtered(
                lambda bw: bw.relation_id and not bw.relation_id.exclude_need
            )
            rec.benefit_breadwinner_count = len(filtered)
            rec.benefit_member_count = len(rec.benefit_member_ids) + len(filtered)
            rec.benefit_breadwinner_count = len(filtered)

    @api.depends('benefit_member_ids')
    def _compute_member_count(self):
        self.member_count = 0
        for rec in self:
            filtered = rec.benefit_breadwinner_ids.filtered(lambda bw: bw.relation_id.name != 'زوجة مطلقة')
            rec.member_count = len(rec.benefit_member_ids) + len(filtered)

    members_under_18 = fields.Integer(
        string="Members Under 18",
        compute="_compute_age_counts",
        store=True,
        readonly=True
    )

    members_18_and_above = fields.Integer(
        string="Members 18 and Above",
        compute="_compute_age_counts",
        store=True,
        readonly=True
    )

    @api.depends('benefit_member_ids.member_id.age')
    def _compute_age_counts(self):
        for rec in self:
            under_18 = rec.benefit_member_ids.filtered(lambda m: m.member_id.age < 18)
            above_18 = rec.benefit_member_ids.filtered(lambda m: m.member_id.age >= 18)
            rec.members_under_18 = len(under_18)
            rec.members_18_and_above = len(above_18)

    @api.onchange('benefit_breadwinner_ids')
    def _onchange_benefit_breadwinner_ids(self):
        for rec in self:
            if rec.benefit_breadwinner_ids:
                rec.breadwinner_member_id = rec.benefit_breadwinner_ids[0].member_name.id
            else:
                rec.breadwinner_member_id = False

    def action_revert_state(self):
        return {
            'name': _('Revert State'),
            'type': 'ir.actions.act_window',
            'res_model': 'revert.state.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_benefit_id': self.id},
        }

    def reset_to_draft(self):
        self.state = 'draft'

    def action_reject(self):
        return {
            'name': _('Cancel Benefit'),
            'type': 'ir.actions.act_window',
            'res_model': 'benefit.rejection.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_benefit_id': self.id},
        }

    @api.onchange('detainee_file_id')
    def _onchange_detainee_file_id(self):
        if self.detainee_file_id:
            self.inmate_member_id = self.detainee_file_id.detainee_id

    def action_set_basic_manager(self):
        self.ensure_one()
        if not self.researcher_id or not self.folder_state:
            raise UserError(_("Please fill in both Researcher Name and Folder State before submitting."))
        self._compute_need_calculator()
        self.state = 'confirm'

    def action_set_service_manager(self):
        self.state = 'validate'

    def action_approve(self):
        self.state = 'approved'

    def action_close(self):
        self.state = 'closed'

    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise UserError(_("You can only delete the record when it's in draft state."))
        return super().unlink()

    @api.model
    def create(self, vals):
        vals['name'] = _('New')
        record = super(GrantBenefit, self).create(vals)
        branch = record.branch_details_id
        detainee_name_seq = record.detainee_file_id.name or ''

        if not branch or not branch.code:
            return record

        branch_code = branch.code

        previous_records = self.search([
            ('branch_details_id', '=', branch.id),
            ('name', 'like', f'{branch_code}%/%'),
            ('id', '!=', record.id)
        ])

        max_seq = 0
        for rec in previous_records:
            name = rec.name or ''
            if name.startswith(branch_code) and '/' in name:
                try:
                    seq_part = name[len(branch_code):].split('/')[0]
                    if not seq_part.isdigit():
                        continue
                    seq_num = int(seq_part)
                    max_seq = max(max_seq, seq_num)
                except Exception:
                    continue

        new_seq = max_seq + 1
        formatted_seq = str(new_seq).zfill(4)

        record.name = f"{branch_code}{formatted_seq}/{detainee_name_seq}"

        return record

    @api.constrains('benefit_member_ids')
    def _check_duplicate_members(self):
        for record in self:
            members = []
            has_breadwinner = False
            for line in record.benefit_member_ids:
                if line.member_id in members:
                    raise ValidationError(_(
                        "The individual %s has already been added.") % line.member_id.name)
                members.append(line.member_id)
                if line.is_breadwinner:
                    if has_breadwinner:
                        raise ValidationError(_("Only one breadwinner can be selected."))
                    has_breadwinner = True

                # Ensure the member is not in another file that is not closed
                other_files = self.env['grant.benefit'].search([
                    ('id', '!=', record.id),
                    ('state', '!=', 'closed'),
                    ('benefit_member_ids.member_id', '=', line.member_id.id)
                ])
                if other_files:
                    raise ValidationError(_(
                        "The individual %s is already listed in another file that is not closed.") % line.member_id.name)

    # end

    attachment_id = fields.One2many('attachment', 'benefit_id', string='')
    partner_id = fields.Many2one('res.partner', required=True, ondelete='cascade')
    inmate_member_id = fields.Many2one('family.member', string='Inmate', domain="[('benefit_type', '=', 'inmate')]")
    breadwinner_member_id = fields.Many2one('family.member', string='Breadwinner',
                                            domain="[('benefit_type', '=', 'breadwinner')]",
                                            )
    education_ids = fields.One2many('family.profile.learn', 'grant_benefit_id', string='Education History')
    member_ids = fields.One2many('family.member', 'benefit_id')
    rehabilitation_ids = fields.One2many('comprehensive.rehabilitation', 'grant_benefit_id',
                                         string='Comprehensive Rehabilitation')
    salary_ids = fields.One2many('salary.line', 'benefit_id', string='')
    health_data_ids = fields.One2many('family.member', 'benefit_id', string='Health Data')

    breadwinner_name = fields.Many2one('family.member', 'Breadwinner')
    relation_id = fields.Many2one('family.member.relation', string='Relation')

    external_guid = fields.Char(string='External GUID')
    account_status = fields.Selection(
        [('active', 'Active'), ('inactive', 'Inactive')],
        string="Account status",
        default='active', tracking=True,
        help="Account status to determine whether the account is active or suspended.")
    entitlement_status = fields.Selection([
        ('beneficiary', 'Beneficiary'),
        ('non_beneficiary', 'Non Beneficiary')
    ], string='Entitlement Status',
    )
    Add_appendix = fields.Binary(string="IBAN", attachment=True)
    relation_to_family = fields.Text(string="Relation to Family")
    stop_reason = fields.Many2one('bank.stop.reason', string="Reason", help="Reason for account suspension.")
    reason = fields.Text(string="Reason")
    reason_revert = fields.Text(string="Revert Reason")
    stop_proof = fields.Binary(string="Proof of suspension document", attachment=True)
    exchange_period = fields.Selection(
        [
            ('monthly', 'Monthly'),
            ('every_three_months', 'Every Three Months'),
            ('every_six_months', 'Every Six Months'),
            ('every_nine_months', 'Every Nine Months'),
            ('annually', 'Annually'),
            ('two_years', 'Two Years'),
        ],
        string="Exchange Period", tracking=True,
        attrs="{'readonly': [('housing_status', 'not in', ['usufruct', 'rent'])]}"
    )

    housing_status = fields.Selection(
        [
            ('owned', 'Owned'),
            ('shared', 'Shared'),
            ('usufruct', 'Usufruct'),
            ('rent', 'Rent'),
        ],
        string="Housing Status", tracking=True,
    )

    housing_value = fields.Integer(
        string="Housing Value",
        attrs="{'readonly': [('housing_status', 'not in', ['usufruct', 'rent'])]}"
    )

    accommodation_attachments = fields.Binary(string="Accommodation Attachments ", attachment=True)

    delegate_id_number = fields.Char(string="Proof of suspension document")
    delegate_mobile = fields.Char(string="Authorized mobile number")
    delegate_name = fields.Char(string="Name of the delegate")
    delegate_iban = fields.Char(string="Authorized IBAN")
    delegate_document = fields.Binary(string="Authorization form", attachment=True)
    delegate_family_rel = fields.Char('Delegat Family Relation')
    house_ids = fields.One2many('family.member.house', 'benefit_id', string="House Profile")

    total_salary = fields.Float(
        string="Total Salary",
        compute="_compute_total_salary",
        store=True
    )

    @api.depends('salary_ids.salary_amount')
    def _compute_total_salary(self):
        for benefit in self:
            benefit.total_salary = sum(benefit.salary_ids.mapped('salary_amount'))

    @api.constrains('delegate_mobile')
    def _check_delegate_mobile(self):
        for record in self:
            if record.delegate_mobile:
                if len(record.delegate_mobile) != 10 or not record.delegate_mobile.isdigit():
                    raise ValidationError("The authorized mobile number must contain exactly 10 digits.")

    @api.constrains('benefit_breadwinner_ids')
    def check_benefit_breadwinner_ids(self):
        for rec in self:
            if not rec.benefit_breadwinner_ids:
                raise ValidationError(_("You must add at least one Breadwinner"))


class BankStopReason(models.Model):
    _name = 'bank.stop.reason'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    stop_reason = fields.Char(string='Reason')


class attachment(models.Model):
    _name = 'attachment'

    benefit_id = fields.Many2one('grant.benefit')
    note = fields.Char()
    attachment_name = fields.Many2one('attachment.type', string='Attachment name')
    classification = fields.Selection(
        [('active', 'Active'), ('inactive', 'Inactive')],
        string="Classification")
    attachment_attachment = fields.Binary(string='Attachment')


class AttachmentType(models.Model):
    _name = 'attachment.type'

    name = fields.Char('Name')


class ExpensesInheritLine(models.Model):
    _inherit = 'expenses.line'

    revenue_periodicity = fields.Selection(
        [
            ('monthly', 'Monthly'),
            ('every_three_months', 'Every Three Months'),
            ('every_six_months', 'Every Six Months'),
            ('every_nine_months', 'Every Nine Months'),
            ('annually', 'Annually'),
            ('two_years', 'Two Years'),
        ],
        string="Revenue periodicity")
    side = fields.Char(string='The side')
    attachment = fields.Binary(string="Attachments", attachment=True)
    benefit_id = fields.Many2one('grant.benefit', ondelete='cascade', string="Benefit")


class SalaryInheritLine(models.Model):
    _inherit = 'salary.line'

    side = fields.Char(string='side')
    benefit_id = fields.Many2one('grant.benefit', ondelete='cascade', string="Benefit")

    revenue_periodicity = fields.Selection(
        [
            ('monthly', 'Monthly'),
            ('every_three_months', 'Every Three Months'),
            ('every_six_months', 'Every Six Months'),
            ('every_nine_months', 'Every Nine Months'),
            ('annually', 'Annually'),
            ('two_years', 'Two Years'),
        ],
        string="Revenue periodicity")


class GrantBenefitMember(models.Model):
    _name = 'grant.benefit.member'
    _description = 'Grant Benefit Member'

    grant_benefit_id = fields.Many2one('grant.benefit', string="Grant Benefit", ondelete="cascade")
    member_id = fields.Many2one('family.member', string="Member")
    # relationship = fields.Many2one(related='member_id.relation_id', string="Relationship", readonly=True)
    is_breadwinner = fields.Boolean(string=" Is Breadwinner?")
    relation_id = fields.Many2one('family.member.relation', string='Relation with res')
    rel_with_resd = fields.Char(string='Relation', default=lambda self: _('Follower'))

    @api.onchange('member_id')
    def _onchange_member_name(self):
        linked_member_ids = self.env['detainee.file'].search([]).mapped('detainee_id').ids

        return {
            'domain': {
                'member_id': [
                    ('state', '=', 'confirmed'),
                    ('id', 'not in', linked_member_ids)
                ]
            }
        }


class GrantBenefitBreadwinner(models.Model):
    _inherit = 'grant.benefit.breadwinner'
    _description = 'Grant Benefit Breadwinner'

    grant_benefit_ids = fields.Many2one('grant.benefit', string="Grant Benefit", ondelete="cascade", required=1)

    relation_id = fields.Many2one('family.member.relation', string='Relation with res')
    breadwinner = fields.Char(string=' Breadwinner', default=lambda self: _('Breadwinner  '))
    member_name = fields.Many2one('family.member', string="Member name")

    @api.onchange('member_name')
    def _onchange_member_name(self):
        linked_member_ids = self.env['detainee.file'].search([]).mapped('detainee_id').ids

        return {
            'domain': {
                'member_name': [
                    ('state', '=', 'confirmed'),
                    ('id', 'not in', linked_member_ids)
                ]
            }
        }

# -*- coding: utf-8 -*-
from odoo import models, fields, _, api
from odoo.exceptions import ValidationError
from lxml import etree
import json
from odoo.exceptions import UserError
from datetime import date
from odoo.tools import config


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    base_line_value = fields.Float(string="Base Line", config_parameter='trahum_benefits.base_line_value')


class GrantBenefit(models.Model):
    _inherit = 'grant.benefit'

    STATE_SELECTION = [
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('validate', 'Validate'),
        ('review', 'Review'),
        ('approve', 'Approve'),
        ('approved', 'Approved'),
        ('closed', 'Done'),
        ('cancelled', 'Cancelled'),

    ]

    previous_state = fields.Selection(STATE_SELECTION, string="Previous State")
    need_calculator = fields.Selection([('high', 'High Need'), ('medium', 'Medium Need'), ('low', 'Low Need'), ],
                                       readonly=1, string="Need Calculator", )
    beneficiary_category = fields.Selection(related='detainee_file_id.beneficiary_category',
                                            string='Beneficiary Category')

    total_income = fields.Float(string="Total Income", store=True, readonly=True)
    expected_income = fields.Float(string="Expected  Income", readonly=True)
    name_member = fields.Char(string="Expected  Income", compute='_compute_member_name', readonly=True)
    researcher_insights = fields.Char('Researcher Insights')
    researcher_id = fields.Many2one("committees.line", string='Researcher Name')
    folder_state = fields.Selection([('Active', 'active'), ('not_active', 'Not Active')], string='Folder State')

    building_number = fields.Integer(string='Building Number')
    sub_number = fields.Integer(string='Sub Number')
    additional_number = fields.Integer(string='Additional Number')
    street_name = fields.Char(string='Street Name')
    city = fields.Many2one("res.country.city", string='City')

    district_name = fields.Many2one(
        'res.district',
        string='District', )

    postal_code = fields.Char(string='Postal Code')
    national_address_code = fields.Char(string='National address code')

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
                field_name = node.get('name')
                modifiers = json.loads(node.get("modifiers", '{}'))

                if field_name == 'researcher_insights':  # Make this field editable in 'confirm'
                    modifiers['readonly'] = [('state', 'not in', ['validate'])]
                else:
                    # Make all other fields readonly unless in 'draft'
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
            'domain': [('id', 'in', self.benefit_member_ids.mapped('member_id').ids)],
            'target': 'current',
        }

    # add new customuzation
    state = fields.Selection(STATE_SELECTION, default='draft', tracking=True)
    detainee_file_id = fields.Many2one('detainee.file', string="Detainee File", tracking=True, related='')

    benefit_member_ids = fields.One2many('grant.benefit.member', 'grant_benefit_id', string="Benefit Member")
    benefit_breadwinner_ids = fields.One2many('grant.benefit.breadwinner', 'grant_benefit_ids',
                                              string="Benefit breadwinner", required=1)

    member_count = fields.Integer(string="Members Count", compute="_compute_member_count", readonly=1)

    @api.depends('benefit_member_ids')
    def _compute_member_count(self):
        self.member_count = 0
        for rec in self:
            filtered = rec.benefit_breadwinner_ids.filtered(lambda bw: bw.relation_id.name != 'زوجة مطلقة')
            rec.member_count = len(rec.benefit_member_ids) + len(filtered)

    @api.onchange('benefit_breadwinner_ids')
    def _onchange_benefit_breadwinner_ids(self):
        if len(self.benefit_breadwinner_ids) > 1:
            raise UserError(_('You can only add one breadwinner line.'))

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

    def action_cancel(self):
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

    def action_submit_call_center(self):
        self._compute_need_calculator()
        self.state = 'confirm'

    def action_approve_call_center(self):
        self.state = 'validate'

    def action_approve_social(self):
        self.state = 'review'

    def action_approve_branch(self):
        self.state = 'approve'

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
                                            domain="[('benefit_type', '=', 'breadwinner')]")
    education_ids = fields.One2many('family.profile.learn', 'grant_benefit_id', string='Education History')
    member_ids = fields.One2many('family.member', 'benefit_id')
    rehabilitation_ids = fields.One2many('comprehensive.rehabilitation', 'grant_benefit_id',
                                         string='Comprehensive Rehabilitation')
    salary_ids = fields.One2many('salary.line', 'benefit_id', string='')
    health_data_ids = fields.One2many('family.member', 'benefit_id', string='Health Data')
    branch_details_id = fields.Many2one(comodel_name='branch.details', string='Branch Name', tracking=True)
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

    @api.constrains('delegate_mobile')
    def _check_delegate_mobile(self):
        for record in self:
            if record.delegate_mobile:
                if len(record.delegate_mobile) != 10 or not record.delegate_mobile.isdigit():
                    raise ValidationError("The authorized mobile number must contain exactly 10 digits.")


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
    member_id = fields.Many2one('family.member', string="Member", domain=[('state', '=', 'confirmed')])
    # relationship = fields.Many2one(related='member_id.relation_id', string="Relationship", readonly=True)
    is_breadwinner = fields.Boolean(string=" Is Breadwinner?")
    relation_id = fields.Many2one('family.member.relation', string='Relation with res')
    rel_with_resd = fields.Char(string='Relation', default=lambda self: _('Follower'))


class GrantBenefitBreadwinner(models.Model):
    _inherit = 'grant.benefit.breadwinner'
    _description = 'Grant Benefit Breadwinner'

    grant_benefit_ids = fields.Many2one('grant.benefit', string="Grant Benefit", ondelete="cascade")
    member_name = fields.Many2one('family.member', string="Member name", domain=[('state', '=', 'confirmed')])

    relation_id = fields.Many2one('family.member.relation', string='Relation with res')
    breadwinner = fields.Char(string='Breadwinner', default=lambda self: _('Breadwinner'))

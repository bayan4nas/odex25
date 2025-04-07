# -*- coding: utf-8 -*-
from odoo import models, fields,_ , api
from odoo.exceptions import ValidationError

from odoo.exceptions import UserError




class GrantBenefit(models.Model):
    _inherit = 'grant.benefit'

    STATE_SELECTION = [
        ('draft', 'Draft'),
        ('call_center', 'Call Center Approved'),
        ('social_researcher', 'Social Researcher Approved'),
        ('branch_manager', 'Branch Manager Approved'),
        ('ceo', 'CEO Approved'),
        ('cancelled', 'Cancelled'),
        ('closed', 'Closed'),
    ]
    previous_state = fields.Selection(STATE_SELECTION, string="Previous State")

    def write(self, vals):
        for rec in self:
            if 'state' in vals and rec.state != vals['state']:
                rec.previous_state = rec.state
                print('state = ',rec.state)
        return super().write(vals)

    # add new customuzation
    state = fields.Selection(STATE_SELECTION,default='draft',tracking=True)
    detainee_file_id = fields.Many2one('detainee.file', string="Detainee File",tracking=True)

    benefit_member_ids = fields.One2many('grant.benefit.member', 'grant_benefit_id', string="Benefit Member")

    member_count = fields.Integer(string="Members Count", compute="_compute_member_count",readonly=1)

    @api.depends('benefit_member_ids')
    def _compute_member_count(self):
        self.member_count=0
        for rec in self:
            rec.member_count = len(rec.benefit_member_ids)

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
        self.state = 'call_center'

    def action_approve_call_center(self):
        self.state = 'social_researcher'

    def action_approve_social(self):
        self.state = 'branch_manager'

    def action_approve_branch(self):
        self.state = 'ceo'


    def action_close(self):
        self.state = 'closed'

    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise UserError(_("You can only delete the record when it's in draft state."))
        return super().unlink()



    @api.model
    def create(self, vals):
        if 'name' not in vals or not vals['name']:
            vals['name'] = 'Unnamed Contact'
        record = super(GrantBenefit, self).create(vals)
        if record.detainee_file_id:
            prefix = record.detainee_file_id.name
            existing = self.search_count([('detainee_file_id', '=', record.detainee_file_id.id)])
            record.name = f"{prefix}/{existing}"
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
    breadwinner_member_id = fields.Many2one('family.member', string='Breadwinner', domain="[('benefit_type', '=', 'breadwinner')]")
    education_ids = fields.One2many('family.profile.learn', 'grant_benefit_id', string='Education History')
    member_ids = fields.One2many('family.member', 'benefit_id')
    rehabilitation_ids = fields.One2many('comprehensive.rehabilitation', 'grant_benefit_id', string='Comprehensive Rehabilitation')
    salary_ids = fields.One2many('salary.line', 'benefit_id', string='')
    health_data_ids = fields.One2many('family.member', 'benefit_id', string='Health Data')
    branch_details_id = fields.Many2one(comodel_name='branch.details', string='Branch Name',tracking=True)
    external_guid = fields.Char(string='External GUID')
    account_status = fields.Selection(
        [('active', 'Active'), ('inactive', 'Inactive')],
        string="Account status",
        default='active',tracking=True,
        help="Account status to determine whether the account is active or suspended.")

    Add_appendix = fields.Binary(string="IBAN", attachment=True)
    stop_reason = fields.Text(string="Reason", help="Reason for account suspension.")
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
        string="Exchange Period",tracking=True,
        attrs="{'readonly': [('housing_status', 'not in', ['usufruct', 'rent'])]}"
    )

    housing_status = fields.Selection(
        [
            ('owned', 'Owned'),
            ('shared', 'Shared'),
            ('usufruct', 'Usufruct'),
            ('rent', 'Rent'),
        ],
        string="Housing Status",tracking=True,
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

    house_ids = fields.One2many('family.member.house','benefit_id' ,string="House Profile")


    @api.constrains('delegate_mobile')
    def _check_delegate_mobile(self):
        for record in self:
            if record.delegate_mobile:
                if len(record.delegate_mobile) != 10 or not record.delegate_mobile.isdigit():
                    raise ValidationError("The authorized mobile number must contain exactly 10 digits.")

class attachment(models.Model):
    _name = 'attachment'

    benefit_id = fields.Many2one('grant.benefit')
    note = fields.Char()
    attachment_name = fields.Char(string='Attachment name')
    classification = fields.Selection(
        [('active', 'Active'), ('inactive', 'Inactive')],
        string="Classification")
    attachment_attachment = fields.Binary(string='Attachment')


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

class SalaryInheritLine(models.Model):
    _inherit = 'salary.line'

    side = fields.Char(string='side')
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
    member_id = fields.Many2one('family.member', string="Member", domain=[('state', '=', 'confirm')])
    # relationship = fields.Many2one(related='member_id.relation_id', string="Relationship", readonly=True)
    relation_id = fields.Many2one('family.member.relation', string='Relation')
    is_breadwinner = fields.Boolean(string=" Is Breadwinner?")


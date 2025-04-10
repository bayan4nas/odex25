# -*- coding: utf-8 -*-
# from future.backports.email.policy import default

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.exceptions import UserError
from lxml import etree
import json

class FamilyMemberMaritalStatus(models.Model):
    _name = 'family.member.maritalstatus'
    _description = 'Family Member Marital Status'

    name = fields.Char(string='Marital Status', required=True)


class FamilyMemberRelation(models.Model):
    _name = 'family.member.relation'
    _description = 'Family Member Relation'

    name = fields.Char(string='Relation', required=True)


class FamilyMemberQualification(models.Model):
    _name = 'family.member.qualification'
    _description = 'Family Member Qualification'

    name = fields.Char(string='Qualification', required=True)


class FamilyEducationLevel(models.Model):
    _name = 'family.education.level'
    _description = 'Family Education Level'

    name = fields.Char(string='Education Level', required=True)


class FamilyEducationDepartment(models.Model):
    _name = 'family.education.department'
    _description = 'Family Education Department'

    name = fields.Char(string='Education Department', required=True)


class FamilyProfile(models.Model):
    _name = 'family.profile.learn'
    _description = 'Family Profile Learning'

    member_id = fields.Many2one('family.member', string='Family Member')
    level_id = fields.Many2one('family.education.level', string='Education Level')
    school_name = fields.Char(string='School Name')
    path = fields.Char(string='Path')
    education_department_id = fields.Many2one('family.education.department', string='Education Department')
    grade = fields.Char(string='Grade')
    graduate_date = fields.Date(string='Graduation Date')


class DisabilityType(models.Model):
    _name = 'disability.type'
    _description = 'Disability Type'

    name = fields.Char(string='Disability Type', required=True)


class ComprehensiveRehabilitation(models.Model):
    _name = 'comprehensive.rehabilitation'
    _description = 'Comprehensive Rehabilitation'

    income_value = fields.Float(string='Income Value')
    disability_type_id = fields.Many2one('disability.type', string='Disability Type')
    disability_date = fields.Date(string='Disability Date')
    member_id = fields.Many2one('family.member', string='Family Member', ondelete='cascade')
    grant_benefit_id = fields.Many2one('grant.benefit', string='Grant Benefit')  # حقل جديد
    name = fields.Char(string="Name", required=True, default="Rehabilitation Record")
    attachments = fields.Binary(string="Attachments")


class FamilyProfileLearn(models.Model):
    _name = 'family.profile.learn'
    _description = 'Family Profile Learning'

    member_id = fields.Many2one('family.member', string='Family Member')
    grant_benefit_id = fields.Many2one('grant.benefit', string='Grant Benefit')  # حقل جديد
    level_id = fields.Many2one('family.education.level', string='Education Level')
    school_name = fields.Char(string='School Name')
    path = fields.Char(string='Path')
    education_department_id = fields.Many2one('family.education.department', string='Education Department')
    grade = fields.Char(string='Grade')
    graduate_date = fields.Date(string='Graduation Date')
    name = fields.Char(string="Name", required=True, default="Rehabilitation Record")
    identity_number = fields.Integer(string="Identity Number")
    graduation_year = fields.Char(string="Graduation Year")
    attachments = fields.Binary(string="Attachments")

    @api.constrains('identity_number')
    def _check_identity_number_length(self):
        for record in self:
            if record.identity_number and (len(str(record.identity_number)) != 10):
                raise ValidationError("Identity Number must be exactly 10 digits.")


class Disease(models.Model):
    _name = 'disease'
    _description = 'Disease'

    name = fields.Char(string='Disease Name', required=True)
    disease_type = fields.Selection([
        ('genetic', 'Genetic'),
        ('chronic', 'Chronic'),
        ('psychological', 'Psychological')
    ], string='Disease Type', required=True)


class MemberDisease(models.Model):
    _name = 'member.disease'
    _description = 'Member Disease'

    member_id = fields.Many2one('family.member', string='Family Member', ondelete='cascade')
    disease_id = fields.Many2one('disease', string='Disease', required=True)
    disease_type = fields.Selection(related='disease_id.disease_type', string='Disease Type', store=True, readonly=True)


class PrisonBenefit(models.Model):
    _name = 'prison.benefit'

    prison_id = fields.Char(string="Prison")


class IssuesInformation(models.Model):
    _name = 'issues.information'

    member_id = fields.Many2one('family.member', string='Family Member')
    detainee_id = fields.Many2one('detainee.file', string='Family Member')
    case_name = fields.Text(string="Case")
    record_start_date = fields.Date(string="Record Start Date")
    record_end_date = fields.Date(string="Record End Date")
    release_date = fields.Date(string="Release Date")
    account_status = fields.Selection(
        [('active', 'Active'), ('inactive', 'Inactive')],
        string="status")
    prison_prison_id = fields.Many2one('prison.benefit', 'prison_id')


class FamilyMember(models.Model):
    _inherit = 'family.member'

    benefit_id = fields.Many2one('grant.benefit', string='Family Profile')
    name = fields.Char(
        string="Name",
        compute="_compute_full_name",
        store=True,  # Store it in the database so it appears on page load
        readonly=True
    )
    first_name = fields.Char("First Name")
    father_name = fields.Char("Father Name")
    grand_name = fields.Char("Grand Name")
    family_name = fields.Char("Family Name")
    benefit_type = fields.Selection([
        ('inmate', 'Inmate'),
        ('breadwinner', 'Breadwinner'),
        ('member', 'Member'),
        ('released', 'Released')
    ], string='Benefit Type')
    inmate_status = fields.Selection([
        ('convicted', 'Convicted'),
        ('not_convicted', 'Not Convicted')
    ], string='Inmate Status', )
    entitlement_status = fields.Selection([
        ('beneficiary', 'Beneficiary'),
        ('non_beneficiary', 'Non Beneficiary')
    ], string='Entitlement Status',
        attrs="{'invisible': [('benefit_type', 'not in', ['breadwinner', 'member'])]}"
    )
    released_status = fields.Selection([
        ('convicted', 'Convicted'),
        ('not_convicted', ' Not Convicted')
    ], string='Released Status',
        attrs="{'invisible': [('benefit_type', '!=', 'released')]}"
    )

    code = fields.Char("File No")
    marital_status_id = fields.Many2one('family.member.maritalstatus', string='Marital Status')
    birth_place = fields.Char(string='Birth Place')
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female')
    ], string='Gender')
    relation_id = fields.Many2one('family.member.relation', string='Relation')
    nationality_id = fields.Many2one('res.country', string='Nationality')
    qualification_id = fields.Many2one('family.member.qualification', string='Qualification')
    education_ids = fields.One2many('family.profile.learn', 'member_id', string='Education History')
    sub_number = fields.Char(string='Sub Number')
    additional_number = fields.Char(string='Additional Number')
    additional_mobile_number = fields.Char(string='Additional Mobile Number')
    street_name = fields.Char(string='Street Name')
    district = fields.Char(string='District')
    city = fields.Many2one("res.country.city", string='City')
    postal_code = fields.Char(string='Postal Code')
    building_number = fields.Char(string='Building Number')
    rehabilitation_ids = fields.One2many('comprehensive.rehabilitation', 'member_id',
                                         string='Comprehensive Rehabilitation')
    blood_type = fields.Selection([
        ('a+', 'A+'), ('a-', 'A-'),
        ('b+', 'B+'), ('b-', 'B-'),
        ('ab+', 'AB+'), ('ab-', 'AB-'),
        ('o+', 'O+'), ('o-', 'O-')
    ], string='Blood Type')
    member_diseases_ids = fields.One2many('member.disease', 'member_id', string='Member Diseases')
    issues_ids = fields.One2many('issues.information', 'member_id', string='issues information')
    social_insurance_income = fields.Float(string='Social Insurance Income')
    social_insurance_status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('active_inactive', 'Active Inactive')
    ], string='Social Insurance Status')
    social_security_income = fields.Float(string='Social Security Income')
    social_security_status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ], string='Social Security Status')

    prison_id = fields.Many2one('res.prison', string='Prison Name')
    prison_country_id = fields.Many2one('res.prison.country', string='Prison Country')
    work_type_id = fields.Many2one('work.type', string='Work Type')
    identity_proof_id = fields.Many2one('identity.proof', string='Identity Proof')

    has_hereditary_disease = fields.Boolean(string="Has a hereditary disease?")
    has_chronic_disease = fields.Boolean(string="He has a chronic disease?")
    has_mental_illness = fields.Boolean(string="He has a mental illness?")
    hereditary_details = fields.Many2one(
        'health.genetic.diseases',  # Reference to the main table
        string="Hereditary Disease",
    )
    chronic_details = fields.Many2one(
        'health.chronic.diseases',  # Reference to the main table
        string="Chronic Disease",
    )
    mental_details = fields.Many2one(
        'health.mental.illnesses',  # Reference to the main table
        string="Mental Illness",
    )
    external_guid = fields.Char(string='External GUID')

    house_ids = fields.One2many('family.member.house', 'member_id', string='House Profile')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Rejected')
    ], string="Status", default='draft', tracking=True)

    cancel_reason: fields.Text = fields.Text(string="Rejection Reason", tracking=True, copy=False)

    def action_confirm(self) -> None:
        """Change status to 'Confirmed'."""
        self.write({'state': 'confirmed'})

    def action_cancel(self):
        """Open a wizard to enter the rejection reason."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reject Approval',
            'res_model': 'request.cancel.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_record_id': self.id}
        }

    def unlink(self) -> bool:
        """Prevent deletion unless the record is in 'Draft' state."""
        for record in self:
            if record.state != 'draft':
                raise UserError(_("You can only delete a record in the 'Draft' state."))
        return super().unlink()

    def action_completed(self):
        self.write({'state': 'completed'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def reset_to_draft(self):
        self.write({'state': 'draft'})

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        res = super(FamilyMember, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                        submenu=submenu)
        doc = etree.XML(res['arch'])
        if view_type == 'form':
            for node in doc.xpath("//field"):
                modifiers = json.loads(node.get("modifiers"))
                if 'readonly' not in modifiers:
                    modifiers['readonly'] = [('state', 'not in', ['draft'])]
                else:
                    if type(modifiers['readonly']) != bool:
                        modifiers['readonly'].insert(0, '|')
                        modifiers['readonly'].append(('state', 'not in', ['draft']))
                node.set("modifiers", json.dumps(modifiers))
                res['arch'] = etree.tostring(doc)
        return res

    @api.depends('first_name', 'father_name', 'grand_name', 'family_name')
    def _compute_full_name(self):
        """Computes 'name' field on page load and when related fields change."""
        for record in self:
            record.name = " ".join(filter(None, [
                record.first_name,
                record.father_name,
                record.grand_name,
                record.family_name
            ]))

    @api.onchange('first_name', 'father_name', 'grand_name', 'family_name')
    def _onchange_full_name(self):
        """Ensures 'name' updates dynamically in the form view when fields change."""
        self._compute_full_name()


class MemberHouse(models.Model):
    _name = 'family.member.house'

    member_id = fields.Many2one('family.member', string='Member', ondelete='cascade', )

    housing_type = fields.Selection([
        ('apartment', 'apartment'),
        ('villa', 'villa'),
        ('popular_house', 'popular house'),
        ('tent', 'tent'),
        ('Appendix', 'Appendix'), ], default='apartment')

    property_type = fields.Selection([
        ('ownership', 'ownership'),
        ('rent', 'rent'),
        ('charitable', 'charitable'),
        ('ownership_shared', 'Ownership Shared'),
        ('rent_shared', 'Rent Shared')])

    exchange_period = fields.Selection(
        [
            ('monthly', 'Monthly'),
            ('every_three_months', 'Every Three Months'),
            ('every_six_months', 'Every Six Months'),
            ('every_nine_months', 'Every Nine Months'),
            ('annually', 'Annually'),
            ('two_years', 'Two Years'),
        ],
        string="Exchange Period",
        attrs="{'readonly': [('housing_status', 'not in', ['usufruct', 'rent'])]}"
    )

    housing_status = fields.Selection(
        [
            ('owned', 'Owned'),
            ('shared', 'Shared'),
            ('usufruct', 'Usufruct'),
            ('rent', 'Rent'),
        ],
        string="Housing Status"
    )

    housing_value = fields.Integer(
        string="Housing Value",
        attrs="{'readonly': [('housing_status', 'not in', ['usufruct', 'rent'])]}"
    )

    accommodation_attachments = fields.Binary(string="Accommodation Attachments", attachment=True)

    benefit_id = fields.Many2one('grant.benefit', string="Profile", related='member_id.benefit_id', store=True)


class DetaineeFile(models.Model):
    _name = 'detainee.file'
    _description = 'Detainee File'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="code", readonly=True, copy=False, default=lambda self: _('New'))
    detainee_id = fields.Many2one('family.member', string="Detainee", required=True)
    detainee_status = fields.Selection([
        ('convicted', 'Convicted'),
        ('non_convicted', 'Non-Convicted'),
        ('released', 'Released')
    ], string="Detainee Status", required=True, tracking=True, default='non_convicted')

    arrest_date = fields.Date(string="Arrest Date", required=True, )
    record_start_date = fields.Date(string="Start Date",default=fields.Date.today)
    record_end_date = fields.Date(string="End Date",)
    expected_release_date = fields.Date(string="Expected Release Date")
    issues_ids = fields.One2many('issues.information', 'detainee_id')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('rejected', 'Rejected'),
    ], string="Status", default='draft', tracking=True)

    branch_id = fields.Many2one('branch.details', string="Branch")

    prison_country_id = fields.Many2one('res.prison.country', string="Prison Country")

    prison_id = fields.Many2one('res.prison', string="Prison")

    cancel_reason: fields.Text = fields.Text(string="Rejection Reason", tracking=True, copy=False)

    def action_open_family_files(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'ملفات الأسرة',
            'res_model': 'grant.benefit',
            'view_mode': 'kanban,tree,form',
            'domain': [('detainee_file_id', '=', self.id)],
            'target': 'current',
        }

    # Restrict deletion & modification based on status
    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise UserError(_("You can only delete records in Preliminary state."))
        return super(DetaineeFile, self).unlink()

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False, submenu=False):
        res = super(DetaineeFile, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,submenu=submenu)
        doc = etree.XML(res['arch'])
        if view_type == 'form':
            for node in doc.xpath("//field"):
                modifiers = json.loads(node.get("modifiers"))
                if 'readonly' not in modifiers:
                    modifiers['readonly'] = [('state', 'not in', ['draft'])]
                else:
                    if type(modifiers['readonly']) != bool:
                        modifiers['readonly'].insert(0, '|')
                        modifiers['readonly'].append(('state', 'not in', ['draft']))
                node.set("modifiers", json.dumps(modifiers))
                res['arch'] = etree.tostring(doc)
        return res


    def action_confirm(self):
        self.state = 'confirmed'


    def action_cancel(self):
        """Open a wizard to enter the rejection reason."""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Reject Approval',
            'res_model': 'request.canceld.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_record_id': self.id}
        }


    def reset_to_draft(self):
        self.state = 'draft'


    def name_get(self):
        result = []
        for rec in self:
            name = f"{rec.name} - {rec.detainee_id.name}"
            result.append((rec.id, name))
        return result

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('detainee.sequence') or _('New')
        res = super(DetaineeFile, self).create(vals)
        return res

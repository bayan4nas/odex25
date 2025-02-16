# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import ValidationError



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

    prison_id =fields.Char(string="Prison")


class IssuesInformation(models.Model):
    _name = 'issues.information'

    member_id = fields.Many2one('family.member', string='Family Member')
    case_name = fields.Text(string="Case")
    record_start_date = fields.Date(string="Record Start Date")
    record_end_date = fields.Date(string="Record End Date")
    release_date = fields.Date(string="Release Date")
    account_status = fields.Selection(
        [('active', 'Active'), ('inactive', 'Inactive')],
        string="status")
    prison_prison_id = fields.Many2one('prison.benefit','prison_id')




class FamilyMember(models.Model):
    _inherit = 'family.member'


    benefit_id = fields.Many2one('grant.benefit', string='Family Profile')
    name = fields.Char(string="Name", compute='get_partner_name', store=True, readonly=False)
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
    ], string='Inmate Status',
       attrs="{'invisible': [('benefit_type', '!=', 'inmate')]}"
    )
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
    street_name = fields.Char(string='Street Name')
    district = fields.Char(string='District')
    city = fields.Many2one("res.country.city",string='City')
    postal_code = fields.Char(string='Postal Code')
    building_number = fields.Char(string='Building Number')
    rehabilitation_ids = fields.One2many('comprehensive.rehabilitation', 'member_id', string='Comprehensive Rehabilitation')
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
    hereditary_details = fields.Char(string="Hereditary")
    chronic_details = fields.Char(string="chronic")
    mental_details = fields.Char(string="mental")

    @api.onchange('first_name', 'father_name', 'grand_name', 'family_name')
    def _onchange_full_name(self):
        """Automatically updates the 'name' field when any of the name parts change."""
        self.name = " ".join(filter(None, [
            self.first_name,
            self.father_name,
            self.grand_name,
            self.family_name
        ]))
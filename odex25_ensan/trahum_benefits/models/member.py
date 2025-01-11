# -*- coding: utf-8 -*-
from odoo import models, fields, api

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


class FamilyMember(models.Model):
    _inherit = 'family.member'


    benefit_id = fields.Many2one('grant.benefit', string='Family Profile')
    name = fields.Char(string="Name", compute='get_partner_name', store=True, readonly=False)
    benefit_type = fields.Selection([
        ('inmate', 'Inmate'),
        ('breadwinner', 'Breadwinner'),
        ('member', 'Member')
    ], string='Benefit Type')
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
    street_name = fields.Char(string='Street Name')
    district = fields.Char(string='District')
    city = fields.Many2one("res.city",string='City')
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
    social_insurance_income = fields.Float(string='Social Insurance Income')
    social_insurance_status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ], string='Social Insurance Status')
    social_security_income = fields.Float(string='Social Security Income')
    social_security_status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive')
    ], string='Social Security Status')

    
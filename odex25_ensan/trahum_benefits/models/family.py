# -*- coding: utf-8 -*-
from odoo import models, fields,_ , api
from odoo.exceptions import ValidationError


class GrantBenefit(models.Model):
    _inherit = 'grant.benefit'

    attachment_id = fields.One2many('attachment', 'benefit_id', string='')
    partner_id = fields.Many2one('res.partner', required=True, ondelete='cascade')
    inmate_member_id = fields.Many2one('family.member', string='Inmate', domain="[('benefit_type', '=', 'inmate')]")
    breadwinner_member_id = fields.Many2one('family.member', string='Breadwinner', domain="[('benefit_type', '=', 'breadwinner')]")
    education_ids = fields.One2many('family.profile.learn', 'grant_benefit_id', string='Education History')
    member_ids = fields.One2many('family.member', 'benefit_id')
    rehabilitation_ids = fields.One2many('comprehensive.rehabilitation', 'grant_benefit_id', string='Comprehensive Rehabilitation')
    salary_ids = fields.One2many('salary.line', 'benefit_id', string='')
    health_data_ids = fields.One2many('family.member', 'benefit_id', string='Health Data')
    branch_details_id = fields.Many2one(comodel_name='branch.details', string='Branch Name')
    external_guid = fields.Char(string='External GUID')


    account_status = fields.Selection(
        [('active', 'Active'), ('inactive', 'Inactive')],
        string="Account status",
        default='active',
        help="Account status to determine whether the account is active or suspended.")

    Add_appendix = fields.Binary(string="IBAN", attachment=True)
    stop_reason = fields.Text(string="Reason", help="Reason for account suspension.")
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

    accommodation_attachments = fields.Binary(string="Accommodation Attachments ", attachment=True)

    delegate_id_number = fields.Char(string="Proof of suspension document")
    delegate_mobile = fields.Char(string="Authorized mobile number")
    delegate_name = fields.Char(string="Name of the delegate")
    delegate_iban = fields.Char(string="Authorized IBAN")
    delegate_document = fields.Binary(string="Authorization form", attachment=True)

    house_ids = fields.One2many('family.member.house','benefit_id' ,string="House Profile")


    @api.model
    def create(self, vals):
        if 'name' not in vals or not vals['name']:
            vals['name'] = 'Unnamed Contact'
        return super(GrantBenefit, self).create(vals)

    @api.constrains('delegate_mobile')
    def _check_delegate_mobile(self):
        for record in self:
            if record.delegate_mobile:
                if len(record.delegate_mobile) != 10 or not record.delegate_mobile.isdigit():
                    raise ValidationError("The authorized mobile number must contain exactly 10 digits.")

    # @api.model
    # def create(self, vals):
    #     if not vals.get('name'):
    #         vals['name'] = 'Grant Benefit'
    #
    #     # استدعاء create الأصلية
    #     record = super(GrantBenefit, self).create(vals)
    #
    #     # تنظيف السجلات القديمة في rehabilitation_ids
    #     record.rehabilitation_ids = [(5, 0, 0)]
    #
    #     # جلب البيانات المتعلقة بـ rehabilitation_ids إذا كانت موجودة
    #     members = [record.inmate_member_id, record.breadwinner_member_id]
    #     rehabilitation_records = []
    #
    #     # إذا تم تحديد العضو
    #     for member in members:
    #         if member:
    #             for rehab in member.rehabilitation_ids:
    #                 # التحقق من عدم تكرار السجلات
    #                 existing_rehab = any(
    #                     r['income_value'] == rehab.income_value and
    #                     r['disability_type_id'] == rehab.disability_type_id.id and
    #                     r['disability_date'] == rehab.disability_date
    #                     for r in rehabilitation_records
    #                 )
    #                 if not existing_rehab:
    #                     rehabilitation_records.append({
    #                         'income_value': rehab.income_value,
    #                         'disability_type_id': rehab.disability_type_id.id,
    #                         'disability_date': rehab.disability_date,
    #                     })
    #
    #     # إذا لم يتم تحديد أي من الأعضاء، جلب كل السجلات من ComprehensiveRehabilitation
    #     if not any(members):
    #         all_rehabilitations = self.env['comprehensive.rehabilitation'].search([])
    #         for rehab in all_rehabilitations:
    #             # التحقق من عدم تكرار السجلات
    #             existing_rehab = any(
    #                 r['income_value'] == rehab.income_value and
    #                 r['disability_type_id'] == rehab.disability_type_id.id and
    #                 r['disability_date'] == rehab.disability_date
    #                 for r in rehabilitation_records
    #             )
    #             if not existing_rehab:
    #                 rehabilitation_records.append({
    #                     'income_value': rehab.income_value,
    #                     'disability_type_id': rehab.disability_type_id.id,
    #                     'disability_date': rehab.disability_date,
    #                 })
    #
    #     # إضافة السجلات إلى rehabilitation_ids
    #     if rehabilitation_records:
    #         record.rehabilitation_ids = [(0, 0, rec) for rec in rehabilitation_records]
    #
    #     return record
    # @api.onchange('inmate_member_id', 'breadwinner_member_id')
    # def _onchange_member_id(self):
    #     for record in self:
    #         record.education_ids = [(5, 0, 0)]
    #
    #         member = record.inmate_member_id or record.breadwinner_member_id
    #         if member:
    #             education_records = []
    #             for education in member.education_ids:
    #                 education_records.append((0, 0, {
    #                     'level_id': education.level_id.id,
    #                     'school_name': education.school_name,
    #                     'path': education.path,
    #                     'education_department_id': education.education_department_id.id,
    #                     'grade': education.grade,
    #                     'graduate_date': education.graduate_date,
    #                 }))
    #             record.education_ids = education_records
    #

    # @api.model
    # def create(self, vals):
    #     if not vals.get('name'):
    #         vals['name'] = 'Grant Benefit'
    #
    #     record = super(GrantBenefit, self).create(vals)
    #
    #     record.rehabilitation_ids = [(5, 0, 0)]
    #     record.education_ids = [(5, 0, 0)]
    #
    #     members = [record.inmate_member_id, record.breadwinner_member_id]
    #
    #     rehabilitation_records = []
    #     education_records = []
    #     for member in members:
    #         if member:
    #             for rehab in member.rehabilitation_ids:
    #                 existing_rehab = any(
    #                     r['income_value'] == rehab.income_value and
    #                     r['disability_type_id'] == rehab.disability_type_id.id and
    #                     r['disability_date'] == rehab.disability_date
    #                     for r in rehabilitation_records
    #                 )
    #                 if not existing_rehab:
    #                     rehabilitation_records.append({
    #                         'income_value': rehab.income_value,
    #                         'disability_type_id': rehab.disability_type_id.id,
    #                         'disability_date': rehab.disability_date,
    #                     })
    #             for education in member.education_ids:
    #                 if not any(edu['level_id'] == education.level_id.id and
    #                            edu['school_name'] == education.school_name for edu in education_records):
    #                     education_records.append({
    #                         'level_id': education.level_id.id,
    #                         'school_name': education.school_name,
    #                         'path': education.path,
    #                         'education_department_id': education.education_department_id.id,
    #                         'grade': education.grade,
    #                         'graduate_date': education.graduate_date,
    #                     })
    #     if not any(members):
    #         all_rehabilitations = self.env['comprehensive.rehabilitation'].search([])
    #         for rehab in all_rehabilitations:
    #             existing_rehab = any(
    #                 r['income_value'] == rehab.income_value and
    #                 r['disability_type_id'] == rehab.disability_type_id.id and
    #                 r['disability_date'] == rehab.disability_date
    #                 for r in rehabilitation_records
    #             )
    #             if not existing_rehab:
    #                 rehabilitation_records.append({
    #                     'income_value': rehab.income_value,
    #                     'disability_type_id': rehab.disability_type_id.id,
    #                     'disability_date': rehab.disability_date,
    #                 })
    #
    #         all_educations = self.env['family.profile.learn'].search([])
    #         for education in all_educations:
    #             if not any(edu['level_id'] == education.level_id.id and
    #                        edu['school_name'] == education.school_name for edu in education_records):
    #                 education_records.append({
    #                     'level_id': education.level_id.id,
    #                     'school_name': education.school_name,
    #                     'path': education.path,
    #                     'education_department_id': education.education_department_id.id,
    #                     'grade': education.grade,
    #                     'graduate_date': education.graduate_date,
    #                 })
    #     if rehabilitation_records:
    #         record.rehabilitation_ids = [(0, 0, rec) for rec in rehabilitation_records]
    #     if education_records:
    #         record.education_ids = [(0, 0, rec) for rec in education_records]
    #
    #     return record

    # @api.model
    # def create(self, vals):
    #     if not vals.get('name'):
    #         vals['name'] = 'Grant Benefit'
    #
    #     record = super(GrantBenefit, self).create(vals)
    #
    #     record.with_context(skip_update_related=True)._update_related_data(all_records=True)
    #
    #     return record
    #
    # def write(self, vals):
    #     if self.env.context.get('skip_update_related'):
    #         return super(GrantBenefit, self).write(vals)
    #
    #     result = super(GrantBenefit, self).write(vals)
    #
    #     self.with_context(skip_update_related=True)._update_related_data(all_records=True)
    #
    #     return result
    #
    # def _update_related_data(self, all_records=False):
    #     self.education_ids = [(5, 0, 0)]
    #     self.rehabilitation_ids = [(5, 0, 0)]
    #
    #     education_records = []
    #     rehabilitation_records = []
    #
    #     if all_records:
    #         all_educations = self.env['family.profile.learn'].search([])
    #         for education in all_educations:
    #             if not any(e['level_id'] == education.level_id.id and
    #                        e['school_name'] == education.school_name
    #                        for e in education_records):
    #                 education_records.append({
    #                     'level_id': education.level_id.id,
    #                     'school_name': education.school_name,
    #                     'path': education.path,
    #                     'education_department_id': education.education_department_id.id,
    #                     'grade': education.grade,
    #                     'graduate_date': education.graduate_date,
    #                 })
    #
    #         all_rehabilitations = self.env['comprehensive.rehabilitation'].search([])
    #         for rehabilitation in all_rehabilitations:
    #             if not any(r['income_value'] == rehabilitation.income_value and
    #                        r['disability_type_id'] == rehabilitation.disability_type_id.id and
    #                        r['disability_date'] == rehabilitation.disability_date
    #                        for r in rehabilitation_records):
    #                 rehabilitation_records.append({
    #                     'income_value': rehabilitation.income_value,
    #                     'disability_type_id': rehabilitation.disability_type_id.id,
    #                     'disability_date': rehabilitation.disability_date,
    #                 })
    #
    #     self.education_ids = [(0, 0, rec) for rec in education_records]
    #     self.rehabilitation_ids = [(0, 0, rec) for rec in rehabilitation_records]


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

# class FamilyMember(models.Model):
#     _inherit = 'res.partner'
#
#     @api.model
#     def create(self, vals):
#         if 'name' not in vals or not vals['name']:
#             vals['name'] = 'Unnamed Contact'
#         return super(FamilyMember, self).create(vals)



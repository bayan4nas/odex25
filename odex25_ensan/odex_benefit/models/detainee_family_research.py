from odoo import models, fields, api, _
from random import randint
import logging

from odoo.exceptions import  ValidationError
class DetaineeFamilyResearch(models.Model):
    _name = 'detainee.family.research'
    # _description = 'Detainee Family Research'
    benefit_id = fields.Many2one(
        'grant.benefit',
        string='Family File',
        required=True,
        domain=[('detainee_file_id.beneficiary_category', '=', 'gust')],
        help="Select the family file (search by ID number is available)."
    )
    detainee_id = fields.Many2one(
        'detainee.file', string="Detainee",
    )

    breadwinner_name = fields.Char(
        string='Family Breadwinner Name',
        related='benefit_id.benefit_breadwinner_ids.member_name.name', store=True, readonly=True)
    breadwinner_id_number = fields.Char(
        string='Breadwinner ID Number',
        related='benefit_id.benefit_breadwinner_ids.member_name.member_id_number', store=True, readonly=True)
    benefit_member_count = fields.Integer(
        string='Family Members Count',
        related='benefit_id.benefit_member_count', store=True, readonly=True)

    detainee_name = fields.Char(
        string='Detainee Name',
        related='detainee_id.name', store=True, readonly=True)

    housing_type = fields.Selection(related="benefit_id.housing_type", string="Housing Type", readonly=True)
    property_type = fields.Selection(related="benefit_id.property_type", string="Property Type", readonly=True)
    housing_status = fields.Selection(
        [
            ('bad', 'Bad'),
            ('good', 'Good'),
            ('excellent', 'Excellent'),
        ],
        string='Housing Condition'
    )

    specialization = fields.Char(string='Specialization')
    is_employee = fields.Boolean(string='Is Employee?')
    experience_years = fields.Integer(string='Years of Experience')
    experience_unit = fields.Selection(
        [('month', 'Month'), ('year', 'Year')],
        string='Experience Unit'
    )

    researcher_report = fields.Text(string='Researcher Report')
    researcher_id = fields.Many2one('family_id.researcher_id', string="Researcher Name")
    researcher_signature = fields.Char(string="Researcher Signature")
    specialist_name = fields.Char(string="Specialist Name")
    specialist_signature = fields.Char(string="Specialist Signature")
    benefit_service_manager_name = fields.Char(string="Beneficiary Service Manager")
    benefit_service_manager_signature = fields.Char(string="Manager Signature")
    ceo_name = fields.Char(string="CEO")
    ceo_signature = fields.Char(string="CEO Signature")

    create_date = fields.Datetime(string='Creation Date', readonly=True)


    # relation_id = fields.Many2one(related="benefit_id.benefit_breadwinner_ids.member_name.relation_id",
    #                               string="صلة القرابة", store=True, readonly=True)

    # marital_status_id = fields.Many2one('family.member', string='Marital Status')
    # # ============= بيانات النزيل =============
    # case_name = fields.Char(
    #     string='القضية',
    #     related='benefit_id.detainee_id.case_name', store=True, readonly=True)
    # period_text = fields.Char(
    #     string='مدة الحكم',
    #     related='benefit_id.detainee_id.period_text', store=True, readonly=True)
    # prison_id = fields.Many2one(
    #     'prison.prison',  #  عدّل الموديل إن كان مختلفاً
    #     string='السجن',
    #     related='benefit_id.detainee_id.prison_id', store=True, readonly=True)

    # city = fields.Char(
    #     string='المدينة',
    #     related='benefit_id.city', store=True, readonly=True)
    #
    # # الحي: مطلوب (قراءة/كتابة)، ومع حفظه يكتب على ملف الأسرة (إن أردت تغييره هناك)
    # district_name = fields.Char(
    #     string='الحي',
    #     related='benefit_id.district_name', store=True, readonly=False)
    # # ============= التعليم/العمل =============
    # level_id = fields.Many2one(
    #     'edu.level',  #  عدّل الموديل حسب نظامك
    #     string='المستوى التعليمي',
    #     related='benefit_id.detainee_id.level_id', store=True, readonly=True)
    #

    #  work_sector =fields.Many2one('work.type', string="جهة العمل")
    # work_type = fields.Char(
    #     string='نوع العمل',
    #     related='benefit_id.breadwinner_job_type',  #  عدّل الحقل حسب تبويب التفاصيل الشخصية للفرد (العائل)
    #     store=True, readonly=True)

    # service_ids = fields.Many2many(
    #     'service.cats',
    #     string="الاحتياجات",
    # )

    type = fields.Selection(
        string='',
        selection=[('male', 'Men'),
                   ('female', 'women'),
                   ('both', 'combined'),
                   ],
        required=False, )

    # @api.constrains('experience_years')
    # def _check_experience_years(self):
    #     for rec in self:
    #         if rec.experience_years and rec.experience_years < 0:
    #             raise ValidationError(_("سنوات الخبرة لا يمكن أن تكون سالبة."))
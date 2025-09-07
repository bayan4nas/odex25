from odoo import models, fields, api, _
from random import randint
import logging

from odoo.exceptions import  ValidationError
class Committees(models.Model):
    _name = 'committees.line'
    detainee_id = fields.Many2one(
        'detainee.file', string="Detainee",
    )
    detainee_file_id = fields.Char(
        related='detainee_id.name', string="Detainee File Number"
    )
    # case_id = fields.Many2one(
    #     related="detainee_id.case_id",
    #     string="Case",
    #     readonly=True,
    #     store=True
    # )
    # case_name = fields.Char(
    #     related="detainee_id.case_id.name",
    #     string="Case Name",
    #     readonly=True,
    #     store=True
    # )
    # period_text = fields.Char(related="detainee_id.period_text", string="مدة الحكم", readonly=True)
    # prison_id = fields.Char(related="detainee_id.prison_id", string="اسم السجن", readonly=True)
    # marital_status_id = fields.Selection(related="detainee_id.marital_status_id", string="Marital Status", readonly=True)
    # level_id = fields.Char(related="detainee_id.level_id", string="Education Level", readonly=True)
    is_trahum = fields.Boolean(string="Are you a Trahum beneficiary?")
    specialization = fields.Char(string="Specialization")
    has_training = fields.Boolean(string="Have you attended prison training courses?")
    training_name = fields.Char(string="Training Name")
    has_talent = fields.Boolean(string="Do you have a talent?")
    talent_name = fields.Char(string="Talent")
    was_employee = fields.Boolean(string="Former Employee?")
    # work_sector =fields.Many2one('work.type', string="جهة العمل")
    work_type = fields.Selection([
        ('government', 'Government'),
        ('private', 'Private'),
        ('freelance', 'Freelance'),
    ], string="Work Type")
    experience_years = fields.Integer(string="Years of Experience")
    experience_unit = fields.Selection([
        ('month', 'Month'),
        ('year', 'Year'),
    ], string="Experience Unit")

    has_family = fields.Boolean(string="Has Family?")
    family_id = fields.Many2one('grant.benefit', string="Family")
    family_file_id = fields.Char(related='family_id.name', string="Family File Name")
    family_id_number = fields.Char(
        related="family_id.benefit_breadwinner_ids.member_name.member_id_number",
        string="Breadwinner ID Number",
        readonly=True
    )
    family_count = fields.Integer(
        related="family_id.benefit_member_count",
        string="Family Members Count",
        readonly=True
    )
    family_head_name = fields.Char(
        related="family_id.benefit_breadwinner_ids.member_name.name",
        string="Family Head Name",
        readonly=True
    )
    family_is_trahum = fields.Boolean(string="Is the family a Trahum beneficiary?")
    housing_type = fields.Selection(related="family_id.housing_type", string="Housing Type", readonly=True)
    property_type = fields.Selection(related="family_id.property_type", string="Property Type", readonly=True)
    # city = fields.Char(related="family_id.benefit_breadwinner_ids.member_name.city.name", string="المدينة", readonly=True)
    # district = fields.Char(related="family_id.benefit_breadwinner_ids.member_name.district_id.name", string="الحي")
    home_status = fields.Selection([
        ('bad', 'Bad'),
        ('good', 'Good'),
        ('excellent', 'Excellent'),
    ], string="Home Status")


    # service_ids = fields.Many2many(
    #     'service.cats',
    #     string="الاحتياجات",
    # )
    researcher_report = fields.Text(string="Researcher Report")
    researcher_id = fields.Char(string="Researcher Name")
    researcher_signature = fields.Char(string="Researcher Signature")
    specialist_name = fields.Char(string="Specialist Name")
    specialist_signature = fields.Char(string="Specialist Signature")
    benefit_service_manager_name = fields.Char(string="Beneficiary Service Manager")
    benefit_service_manager_signature = fields.Char(string="Manager Signature")
    ceo_name = fields.Char(string="CEO")
    ceo_signature = fields.Char(string="CEO Signature")

    create_date = fields.Datetime(string="Creation Date", readonly=True)




    type = fields.Selection(
        string='',
        selection=[('male', 'Men'),
                   ('female', 'women'),
                   ('both', 'combined'),
                   ],
        required=False, )
    branch_custom_id = fields.Many2one("branch.settings", string="Branch")

    # name = fields.Char()
    # employee_id = fields.Many2many('hr.employee')
    # benefit_ids = fields.Many2many('grant.benefit',compute="get_benefit_ids")
    #
    # def get_benefit_ids(self):
    #     obj = self.env["grant.benefit"].search([])
    #     for rec in obj:
    #         if rec.researcher_id.id == self.id:
    #             self.write({'benefit_ids': [(4, rec.id)]})
    #         else:
    #             self.write({'benefit_ids': []})
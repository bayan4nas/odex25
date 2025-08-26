# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from random import randint
import logging

from odoo.exceptions import  ValidationError


_logger = logging.getLogger(__name__)


class BenefitCategory(models.Model):
    _name = 'benefit.category'
    _description = "Benefits - category"

    name = fields.Char(string="Category Name")
    description = fields.Char(string="Description")
    gender = fields.Selection(selection=[('male', _('Male')), ('female', _('Female')) ,('both', _('Both'))], string="Gender")
    age_from = fields.Integer(string="From")
    age_to = fields.Integer(string="To")
    benefit_ids = fields.One2many('grant.benefit', 'benefit_category_id', string="Category Benefits")
    benefits_total = fields.Integer(string="Benefit Total", compute="get_benefits_total")
    mini_income_amount = fields.Float(string="Min Income Amount")
    max_income_amount = fields.Float(string="Max Income Amount")
    expenses_ids = fields.One2many('expenses.line', 'benefit_id')
    state = fields.Selection([('draft', 'Draft'),
                              ('approve', 'Approved'),
                              ('rejected', 'Rejected'), ], default='draft')

    def get_benefits_total(self):
        for rec in self:
            rec.benefits_total = len(rec.benefit_ids)

    def action_approve(self):
        self.state = 'approve'

    def action_reject(self):
        self.state = 'rejected'

    def open_benefits(self):
        return {
            'name': _("Benefits"),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(self.env.ref(
                'odex_benefit.grant_benefit_tree').id, 'tree'),
                      (self.env.ref('odex_benefit.grant_benefit_form').id, 'form')],
            'res_model': 'grant.benefit',
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.benefit_ids.ids)],
            'target': 'current',
        }


class GrantFamily(models.Model):
    _name = 'benefit.family'
    _description = "Benefits - family"

    name = fields.Char(
        string='',
        required=False)
    responsible_benefit_id = fields.Many2one(
        'grant.benefit',
        domain="[('is_responsible','=',True),('family_id','=',id)]")
    housing_id = fields.Many2one(
        'benefit.housing')
    loan_ids = fields.Many2many('benefit.loans', 'family_id')
    total_expenses = fields.Float(
        compute='get_total_needs_percent',
        string='Total Expenses of Family',
        required=False)
    total_income = fields.Float(
        compute='get_total_needs_percent',
        string='Total Income of Family',
        required=False)
    benefit_needs_percent = fields.Float(
        compute='get_total_needs_percent',
        string='',
        store=True,
        required=False)
    is_producer = fields.Boolean(string='Producer')
    description = fields.Char(string="Description")
    benefits_total = fields.Integer(string="Benefit Total", compute="get_benefits_total", store=True)
    benefit_ids = fields.One2many('grant.benefit', 'family_id', string="Benefits")

    @api.depends("benefit_ids")
    def get_benefits_total(self):
        for rec in self:
            rec.benefits_total = len(rec.benefit_ids)

    def get_total_needs_percent(self):
        for rec in self:
            if rec.benefit_ids:
                percent = 0.0
                for amount in rec.benefit_ids:
                    rec.total_income += amount.total_income
                    rec.total_expenses += amount.total_expenses
                    percent += amount.benefit_needs_percent
                rec.benefit_needs_percent = percent / len(rec.benefit_ids)
            else:
                rec.benefit_needs_percent = 0.0
                rec.total_income = 0.0
                rec.total_expenses = 0.0


    def open_benefits(self):
        return {
            'name': "Benefits",
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(self.env.ref(
                'odex_benefit.grant_benefit_tree').id, 'tree'),
                      (self.env.ref('odex_benefit.grant_benefit_form').id, 'form')],
            'res_model': 'grant.benefit',
            'type': 'ir.actions.act_window',
            'domain': "[('family_id','=',%s)]" % (self.id),
            'target': 'current',
        }


class SportLine(models.Model):
    _name = 'sport.line'
    _description = "Benefits - sport"

    benefit_id = fields.Many2one(
        'grant.benefit')
    sport_type = fields.Many2one(
        'sport.type')
    sport_attendance = fields.Boolean(
        string='',
        required=False)
    Subtype = fields.Selection(
        string='Subtype',
        selection=[('daily', 'daily'),
                   ('monthly', 'Monthly'),
                   ('yearly', 'yearly'),
                   ], )
    sport_time = fields.Selection(
        string='Sport Time',
        selection=[('morning', 'Morning'),
                   ('day', 'day'),
                   ('evening', 'evening'),
                   ],
        required=False, )
    sport_club = fields.Char(
        string='',
        required=False)
    sport_amount = fields.Float(
        string='',
        required=False)
    sport_clothing = fields.Char(
        string='',
        required=False)
    sport_equipment = fields.Char(
        string='',
        required=False)


class SportType(models.Model):
    _name = 'sport.type'
    _description = "Benefits - sport Type"

    name = fields.Char(
        string='',
        required=False)
    description = fields.Char(
        string='Description',
        required=False)


class CraftSkills(models.Model):
    _name = 'craft.skills'
    _description = "Benefits - sport"

    name = fields.Char(
        string='',
        required=False)
    benefit_id = fields.Many2one(
        'grant.benefit')
    is_invested = fields.Boolean(
        string='',
        required=False)
    skill_rating = fields.Float(
        string='',
        required=False)
    is_development = fields.Boolean(
        string='',
        required=False)
    is_capital = fields.Boolean(
        string='',
        required=False)
    is_work_place = fields.Boolean(
        string='',
        required=False)
    work_history = fields.Char(
        string='',
        required=False)
    achievements = fields.Char(
        string='',
        required=False)
    certificates = fields.Binary(string="")
    # Awards and certificates # TODO#


class inclination(models.Model):
    _name = 'training.inclinations'
    _description = "Benefits - inclination"

    name = fields.Char(
        string='',
        required=False)
    benefit_id = fields.Many2one(
        'grant.benefit')
    training_type_id = fields.Many2one('training.type',
                                       string='',
                                       required=False)
    is_invested = fields.Boolean(
        string='',
        required=False)
    training_rating = fields.Float(
        string='',
        required=False)
    is_development = fields.Boolean(
        string='',
        required=False)
    is_capital = fields.Boolean(
        string='',
        required=False)
    training_history = fields.Char(
        string='',
        required=False)
    book_history = fields.Char(
        string='What books has he read?',
        required=False)
    courses = fields.Char(
        string='What courses did he take?',
        required=False)
    steps = fields.Char(
        string='',
        required=False)
    training_future = fields.Char(
        string='',
        required=False)
    training_site = fields.Char(
        string='',
        required=False)
    training_records = fields.Char(
        string='',
        required=False)
    achievements = fields.Char()
    certificates = fields.Binary(string="")
    # Awards and certificates


class BenefitBehaviors(models.Model):
    _name = 'benefit.behaviors'
    _description = "Benefits - behaviors"

    name = fields.Char(
        related='behavior_id.name')
    benefit_id = fields.Many2one(
        'grant.benefit')
    behavior_id = fields.Many2one(
        'benefit.behaviors.type')
    behavior_date = fields.Date(
        string='',
        required=False)
    need_help = fields.Boolean(
        string='',
        required=False)


class BenefitBehaviorsType(models.Model):
    _name = 'benefit.behaviors.type'
    _description = "Benefits - behaviors type"

    name = fields.Char(
        string='',
        required=False)
    type = fields.Selection(
        string='',
        selection=[('negative', 'Negative'),
                   ('positive', 'Positive'), ],
        required=False, )


class Salary(models.Model):
    _name = 'salary.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Benefits - Salary line"

    member_id = fields.Many2one('family.member', string='Member', ondelete='cascade',tracking=True)

    benefit_id = fields.Many2one('grant.benefit', string="Benefit",ondelete='cascade',tracking=True)
    salary_type = fields.Char()
    income_type = fields.Many2one('attachments.settings',string='Income Type',tracking=True,domain="[('attach_type','=','income_attach')]")
    salary_amount = fields.Float(
        string='Income Amount',
        required=False)
    salary_attach = fields.Many2many('ir.attachment',string="Attachment",tracking=True)
    attach_start_date = fields.Date(string='Attach Start Date',tracking=True)
    attach_end_date = fields.Date(string='Attach End Date',tracking=True)
    is_required = fields.Boolean(string='Is Required?',tracking=True)
    is_default = fields.Boolean(string='Is Default?',tracking=True)
    state = fields.Selection(string='Status',tracking=True,selection=[('accepted', 'Accepted'),('refused', 'Refused')])
    # total_salary = fields.Float(string="Total Salary", compute='_compute_total_salary',store=True)


    # @api.depends('salary_amount','state')
    # def _compute_total_salary(self):
    #     total = 0
    #     for record in self:
    #         # Apply your custom condition here
    #         records = self.env['salary.line'].search([('state', '=', 'accepted')])
    #         for rec in records:
    #             total += rec.salary_amount
    #         record.total_salary = total

    def action_accept(self):
        self.state = 'accepted'

    def action_refuse(self):
        self.state = 'refused'

class ibanBanks(models.Model):
    _inherit = 'res.bank'
    _description = "Add iban details in bank screen"

    iban = fields.Char("IBAN")
    code = fields.Char(string='Code')


class benefitsExpensesLine(models.Model):
    _name = 'benefit.expenses'
    _description = "Benefits - expenses"

    name = fields.Char()
    benefit_id = fields.Many2one('grant.benefit')
    expenses_type = fields.Selection(
        string='',
        selection=[('governmental', 'Governmental Expenses'),
                   ('medical', 'Medical Expenses'),
                   ('transportation', 'Transportation Expenses'),
                   ('debts', 'Debts Expenses'),
                   ('pandemics', 'Pandemics Expenses'),
                   ('living', 'Living Expenses'),
                   ('educational', 'Educational Expenses'),
                   ('clothing', 'Clothing Expenses'),
                   ],
        required=False, )
    expenses_fees_type = fields.Selection(
        string='Fees Type',
        selection=[('fixed', 'Fixed'),
                   ('dynamic', 'dynamic')], required=False, )
    medicine_type = fields.Selection(
        string='Medicine Type',
        selection=[('pills', 'pills'),
                   ('drink', 'drink'),
                   ('inhalation', 'inhalation')], required=False, )
    diseases_type = fields.Selection(
        string='Diseases Type',
        selection=[('chronic', 'chronic'),
                   ('psycho', 'psycho'),
                   ('organic', 'organic')], required=False, )
    trans_type = fields.Selection(
        string='trans Type',
        selection=[('general', 'General'),
                   ('especially', 'Especially')], required=False, )
    debt_reason = fields.Char(string='', required=False)
    attach = fields.Binary(string="",attachment=True )
    debt_type = fields.Selection(selection=[('necessary', 'Necessary'),
                                            ('need', 'Need'),
                                            ('improve', 'to improve'),
                                            ('case', 'case or not'),
                                            ('Installed', 'Installed or not'),
                                            ])
    pandemics_explain = fields.Char(string='pandemics explain', required=False)
    amount = fields.Float()
    state = fields.Selection([('draft', 'Draft'),
                              ('accreditation', 'Accreditation'),
                              ], string='state', default="draft", tracking=True)

    def action_accepted(self):
        for i in self:
            i.state = 'accreditation'


class cloth(models.Model):
    _name = 'benefit.cloth'

    name = fields.Char()
    benefit_id = fields.Many2one('grant.benefit')
    cloth_type = fields.Many2one('cloth.type')
    cloth_size = fields.Many2one('cloth.size')
    cloth_note = fields.Char()


class ClothType(models.Model):
    _name = 'cloth.type'

    name = fields.Char()


class ClothSize(models.Model):
    _name = 'cloth.size'

    name = fields.Char()


class ExpensesLine(models.Model):
    _name = 'expenses.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    member_id = fields.Many2one('family.member', string='Member', ondelete='cascade',tracking=True)

    category_id = fields.Many2one(
        'benefit.category')
    benefit_id = fields.Many2one('grant.benefit', string="Benefit",ondelete='cascade',tracking=True)
    expenses_type_custom = fields.Many2one('expenses.type',tracking=True)
    expenses_type = fields.Selection(
        string='',
        selection=[('governmental', 'Governmental Expenses'),
                   ('medical', 'Medical Expenses'),
                   ('transportation', 'Transportation Expenses'),
                   ('debts', 'Debts Expenses'),
                   ('pandemics', 'Pandemics Expenses'),
                   ('living', 'Living Expenses'),
                   ('educational', 'Educational Expenses'),
                   ('clothing', 'Clothing Expenses'),
                   ],
        required=False,tracking=True )
    amount = fields.Float(tracking=True)
    note = fields.Char(tracking=True)
    state = fields.Selection(string='Status', selection=[('accepted', 'Accepted'), ('refused', 'Refused')],tracking=True)
    # revenue_periodicity = fields.Selection(string='Revenue Periodicity', selection=[])
    # side = fields.Char(string='The side')
    # attachment = fields.Binary(string="Attachments", attachment=True)

    
    
    def action_accept(self):
        self.state = 'accepted'

    def action_refuse(self):
        self.state = 'refused'

class EntityRefuseReason(models.Model):
    _name = 'entity.refuse_reason'

    name = fields.Text("Refuse Reason")
    user_id = fields.Many2one('res.users', 'Assigned to', default=lambda self: self.env.user, index=True)
    entity_id = fields.Many2one('grant.benefit', 'Benefit Id')
    date = fields.Datetime(string='Refuse Date', default=fields.Datetime.now)


class specialization(models.Model):
    _name = 'specialization.specialization'

    name = fields.Char(
        string='',
        required=False)
    description = fields.Char(
        string='Description',
        required=False)
    is_scientific_specialty = fields.Boolean('Is Scientific Specialty?')
    is_medical_specialty = fields.Boolean('Is Medical Specialty?')


class OtherAssociations(models.Model):
    _name = 'other.associations'

    name = fields.Char(
        string='',
        required=False)
    city_id = fields.Many2one(
        'res.country.city')
    description = fields.Char(
        string='Description',
        required=False)


class Associations(models.Model):
    _name = 'associations.line'

    benefit_id = fields.Many2one(
        'grant.benefit')
    associations_ids = fields.Many2one(
        'other.associations',
        string='Other Associations',
        required=False)
    support_type = fields.Selection(
        string='',
        selection=[('material', 'Material'),
                   ('cash', 'cash'),
                   ('both', 'Both'),
                   ],
        required=False, )
    support_amount = fields.Float(
        string='',
        required=False)
    associations_description = fields.Text(
        string="",
        required=False)


class Hospital(models.Model):
    _name = 'hospital.hospital'

    name = fields.Char(
        string='',
        required=False)
    Location = fields.Char(
        string='',
        required=False)


class InsuranceCompany(models.Model):
    _name = 'insurance.company'

    name = fields.Char(
        string='',
        required=False)
    description = fields.Char(
        string='Description',
        required=False)


class InsuranceType(models.Model):
    _name = 'insurance.type'

    name = fields.Char(
        string='',
        required=False)
    description = fields.Char(
        string='Description',
        required=False)


class Cars(models.Model):
    _name = 'cars.line'

    name = fields.Char()
    benefit_id = fields.Many2one('grant.benefit')
    car_model = fields.Char()
    status = fields.Selection(
        string='',
        selection=[('good', 'Good'),
                   ('bad', 'bad'), ],
        required=False, )  # TODO
    image_1 = fields.Binary(string="", )
    image_2 = fields.Binary(string="", )
    image_3 = fields.Binary(string="", )


class TrainingType(models.Model):
    _name = 'training.type'

    name = fields.Char()


class Committees(models.Model):
    _name = 'committees.line'

    name = fields.Char()
    employee_id = fields.Many2many('hr.employee')
    benefit_ids = fields.Many2many('grant.benefit',compute="get_benefit_ids")
    type = fields.Selection(
        string='',
        selection=[('male', 'Men'),
                   ('female', 'women'),
                   ('both', 'combined'),
                   ],
        required=False, )
    branch_custom_id = fields.Many2one("branch.settings", string="Branch")

    def get_benefit_ids(self):
        obj = self.env["grant.benefit"].search([])
        for rec in obj:
            if rec.researcher_id.id == self.id:
                self.write({'benefit_ids': [(4, rec.id)]})
            else:
                self.write({'benefit_ids': []})

class ResDistricts(models.Model):
    _name = 'res.districts'

    name = fields.Char(string="Name")
    branch_custom_id = fields.Many2one("branch.settings", string="Branch")
    meal_card = fields.Boolean(string='Meal Card')

class VisitsSettings(models.Model):
    _name = 'visits.types'

    name = fields.Char(string="Name")

class SurveySetting(models.Model):
    _name = 'survey.setting'

    survey_url = fields.Char("Survey URL")

class SuspendReason(models.Model):
    _name = 'suspend.reason'
    _description = "Suspend - Reason"

    name = fields.Char(string="Name")

class BranchSettings(models.Model):
    _name = 'branch.settings'
    _description = "Branch Settings"

    name = fields.Char(related='branch.name')
    branch = fields.Many2one('hr.department',string='Branch',domain =[('is_branch', '=', True)])
    branch_type = fields.Selection(
        selection=[
            ('branches', 'Branches'),
            ('governorates', 'Governorates')],
        string='Branch Type')
    branch_code = fields.Char(string='Branch Code')
class RelationSettings(models.Model):
    _name = 'relation.settings'
    _description = "Relation Settings"

    name = fields.Char(string='name')
    relation_type = fields.Selection(
        [('son', _('Son')), ('daughter', _('Daughter')),('mother', _('Mother')),('replacement_mother', _('Replacement Mother')),('other relation', _('Other Relation'))])

class LocationSettings(models.Model):
    _name = 'location.settings'
    _description = "Location Settings"

    name = fields.Char(string='name')
    location_type = fields.Selection([('member', _('Member')), ('mother_location', _('Mother Location'))])
    is_benefit = fields.Boolean(string='Is Benefit?')

class AttachmentsSettings(models.Model):
    _name = 'attachments.settings'
    _description = "Attachments Settings"
    _order = 'family_appearance_seq,member_appearance_seq,income_appearance_seq asc'

    name = fields.Char(string='name')
    hobby_id = fields.Many2one('hobbies.settings',string='Hobbies')
    diseases_id = fields.Many2one('diseases.settings',string='Diseases')
    disabilities_id = fields.Many2one('disabilities.settings',string='Disabilities')
    attach_type = fields.Selection(
        [('family_attach', _('Family Attach')), ('member_attach', _('Member Attach')), ('hobbies_attach', _('Hobbies Attach')),
         ('diseases_attach', _('Diseases Attach')), ('disabilities_attach', _('Disabilities Attach')), ('income_attach', _('Income Attach'))])
    is_required = fields.Boolean(string='Is Required?')
    is_default = fields.Boolean(string='Is Default?')
    family_appearance_seq = fields.Integer(string='Appearance Sequence')
    member_appearance_seq = fields.Integer(string='Appearance Sequence')
    income_appearance_seq = fields.Integer(string='Appearance Sequence')

class EducationIlliterateReason(models.Model):
    _name = 'education.illiterate.reason'
    _description = "Education Illiterate Reason"

    name = fields.Char(string='name')

class IncomeType(models.Model):
    _name = 'income.type'
    _description = "Income Type"

    name = fields.Char(string='name')

class LoanGiver(models.Model):
    _name = 'loan.giver'
    _description = "LoanGiver"

    name = fields.Char(string='name')

class LoanReason(models.Model):
    _name = 'loan.reason'
    _description = "Loan Reason"

    name = fields.Char(string='name')

class HobbiesSettings(models.Model):
    _name = 'hobbies.settings'

    name = fields.Char(string="Name")

class DiseasesSettings(models.Model):
    _name = 'diseases.settings'

    name = fields.Char(string="Name")

class DisabilitiesSettings(models.Model):
    _name = 'disabilities.settings'

    name = fields.Char(string="Name")

class ExceptionReason(models.Model):
    _name = 'exception.reason'

    name = fields.Char(string="Name")

class MaritalStatus(models.Model):
    _name = 'marital.status'

    name = fields.Char(string="Name")
    is_benefit = fields.Boolean(string='Is Benefit?')
    is_dead = fields.Boolean(string='Is Dead?')

class AgeCategory(models.Model):
    _name = 'age.category'

    min_age = fields.Integer(string="From")
    max_age = fields.Integer(string="To")
    name = fields.Char(string="Name", compute="_compute_name", store=True)

    @api.depends('min_age', 'max_age')
    def _compute_name(self):
        for record in self:
            if record.min_age is not None and record.max_age is not None:
                record.name = f"[{record.min_age}:{record.max_age}]"
            else:
                record.name = ""

class ComplaintsCategory(models.Model):
    _name = 'complaints.category'

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char('Category Name', required=True, translate=True)
    color = fields.Integer('Color', default=_get_default_color)


class ServiceAttachmentsSettings(models.Model):
    _name = 'service.attachments.settings'
    _description = "Service Attachments Settings"

    name = fields.Char(string='Name Attachment')
    service_attach = fields.Many2many('ir.attachment','rel_service_attachments', 'service_id', 'attach_id',string="Attachment")
    service_type = fields.Selection(
        [('rent', 'Rent'), ('home_restoration', 'Home Restoration'), ('alternative_housing', 'Alternative Housing'),
         ('home_maintenance', 'Home Maintenance'), ('complete_building_house', 'Complete Building House'), ('electrical_devices', 'Electrical Devices'),
         ('home_furnishing', 'Home furnishing')
            , ('electricity_bill', 'Electricity bill'), ('water_bill', 'Water bill'), ('buy_car', 'Buy Car'),
         ('recruiting_driver', 'Recruiting Driver')
            , ('transportation_insurance', 'Transportation Insurance'), ('debits', 'Debits'),
         ('health_care', 'Health Care'),
         ('providing_medicines_medical_devices_and_needs_the_disabled',
          'Providing Medicines Medical Devices And Needs The Disabled'),
         ('recruiting_domestic_worker_or_nurse', 'Recruiting a domestic worker or nurse'), ('marriage', 'Marriage'),
         ('eid_gift', 'Eid gift'),
         ('winter_clothing', 'Winter clothing'), ('ramadan_basket', 'Ramadan basket'),
         ('natural_disasters', 'Natural disasters'), ('legal_arguments', 'Legal arguments')],string='Service Type',related="service_id.service_type")
    service_id = fields.Many2one('services.settings',string='Service')
    service_request_id = fields.Many2one('service.request',string='Service Request')
    notes = fields.Text(string='Notes')
    attachment = fields.Binary(string='Attachment')
    attachment_type = fields.Boolean(string='Attachment Type')

    @api.constrains('attachment_type', 'attachment')
    def _check_required_attachment(self):
        for rec in self:
            if rec.attachment_type and not rec.attachment:
                raise ValidationError("Attachment is required for line: %s" % (rec.name or ""))


class HomeMaintenanceItems(models.Model):
    _name = 'home.maintenance.items'

    maintenance_items_id = fields.Many2one('home.maintenance.lines', string="Maintenance Items")
    service_request_id = fields.Many2one('service.request',string='Service Request')

class HomeFurnishingItems(models.Model):
    _name = 'home.furnishing.items'

    home_furnishing_items = fields.Many2one('home.furnishing.lines', string='Furnishing Items')
    furnishing_cost = fields.Float(string='Furnishing Cost')
    # max_furnishing_cost = fields.Float(string='Furnishing Cost',related='home_furnishing_items.max_furnishing_amount')
    price_first = fields.Float(string='Price First')
    price_first_attach = fields.Many2many('ir.attachment','rel_first_price_attachments', 'furnishing_id', 'attach_id',string="First Price Attachment")
    price_second = fields.Float(string='Price Second')
    price_second_attach = fields.Many2many('ir.attachment','rel_second_price_attachments', 'furnishing_id', 'attach_id',string="Second Price Attachment")
    service_request_id = fields.Many2one('service.request',string='Service Request')

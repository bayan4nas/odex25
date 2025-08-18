# -*- coding: utf-8 -*-
import logging
from datetime import datetime, date
from dateutil.relativedelta import relativedelta as rd
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import qrcode
import base64
from io import BytesIO
import re

SAUDI_MOBILE_PATTERN = "(^(05|5)(5|0|3|6|4|9|1|8|7)([0-9]{7})$)"

_logger = logging.getLogger(__name__)


class GrantBenefitProfile(models.Model):
    _name = 'grant.benefit'
    _description = "Benefits - Profiles"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _inherits = {'res.partner': 'partner_id'}
    _order = 'code desc'
    def get_url(self):
        return "wwww"

    def name_get(self):
        result = []
        for rec in self:
            if rec.name and rec.code:
                name = rec.name + " " + rec.code
                result.append((rec.id, name))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        if not args:
            args = []

            # Extend the domain filter with custom search conditions
        domain = ['|', '|', '|', ('name', operator, name), ('phone', operator, name),
                  ('code', operator, name), ('father_id_number', operator, name)]

        # Combine domain filter with any existing args (domain filter in Many2one)
        partners = self.search(domain + args, limit=limit)

        return partners.name_get()

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        if self.env.user and self.env.user.id and self.env.user.has_group("odex_benefit.group_benefit_researcher") and not self.env.user.has_group("odex_benefit.group_benefit_manager"):
            args += [('researcher_id.employee_id', '=', self.env.user.employee_id.id)]
        if self.env.user and self.env.user.id and (self.env.user.has_group("odex_benefit.group_benefit_woman_commitee") or self.env.user.has_group("odex_benefit.group_benefit_branch_manager")) and not self.env.user.has_group("odex_benefit.group_benefit_manager"):
            if self.branch_custom_id:
                args += [('branch_custom_id.branch_id', '=', self.env.user.employee_id.department_id.id)]
        if self.env.user and self.env.user.id and self.env.user.has_group("odex_benefit.group_benefit_manager"):
            args += []
        return super(GrantBenefitProfile, self).search(args, offset, limit, order, count)

    profile_step_count = fields.Integer()
    partner_id = fields.Many2one('res.partner', string='partner', required=True, ondelete="cascade")
    code = fields.Char(string="Code", copy=False, readonly=True, default=lambda x: _('New'))
    benefit_type = fields.Selection([('benefit', 'benefit'), ('orphan', 'orphan'), ('widow', 'widow')
                                     ], string='Benefit Type', tracking=True)
    mother_status = fields.Selection(selection=[
        ('benefit', 'Benefit'),
        ('non_benefit', 'Non Benefit'),
    ], string='Mother Status', compute="check_mother_status", store=True, default=False)
    phone2 = fields.Char(string="Phone2")
    relative_phone = fields.Char(string="Relative Phone")
    branch_details_id = fields.Many2one(comodel_name='branch.details', string='Branch Name', tracking=True, required=1)
    relative_relation = fields.Char(string="Relative Relation")
    sms_phone = fields.Char(string="Contact Phone")
    name_in_bank = fields.Char()
    family_bank = fields.Many2one('res.partner.bank')
    acc_number = fields.Char('Account Number',copy=False)
    acc_holder_name = fields.Char('Account Holder Name')
    bank_id = fields.Many2one("res.bank",string='Bank')
    account_relation = fields.Many2one('relation.settings',string="Account Owner Relation")
    orphan_status = fields.Selection(
        selection=[('father', 'Father-Orphan'), ('mother', 'Mother-Orphan'), ('parent', 'Parent-Orphan'), ],
        compute="_compute_orphan_Type", store=True)
    iban_attach = fields.Many2many('ir.attachment',
                                   relation="ir_iban_attach_rel",
                                   column1="iban",
                                   column2="name",
                                   string="Iban Attach")
    id_number_attach = fields.Many2many('ir.attachment',
                                        relation="ir_id_number_attach_rel",
                                        column1="id_number",
                                        column2="name",
                                        string="Id Number Attach")
    instrument_number = fields.Char()
    instrument_attach = fields.Many2many('ir.attachment',
                                         relation="ir_instrument_attach_rel",
                                         column1="instrument_number",
                                         column2="name",
                                         string="Instrument Attach")
    step = fields.Integer('Step')
    has_needs = fields.Boolean(compute='_onchange_is_has_needs',
                               store=True)  # This boolean filed for check if benefit has need in

    researcher_insights = fields.Text(string='Researcher Insights')
    # Job
    job_position = fields.Char()
    job_department = fields.Char()
    job_company = fields.Char()
    # login info
    user_id = fields.Many2one('res.users', string="User")
    password = fields.Char('Password')
    # Category And Family
    benefit_category_id = fields.Many2one('benefit.category', string='Benefit Category', compute="get_benefit_category",store=True)
    family_id = fields.Many2one('benefit.family', string='Benefit Family')
    # address
    housing_id = fields.Many2one('benefit.housing', string='Benefit Housing')
    lat = fields.Float(string='Lat', digits=(16, 5))
    lon = fields.Float(string='Long', digits=(16, 5))
    block = fields.Char(string='block')
    street = fields.Char(string='street')
    house_number = fields.Char(string='house number')
    floor = fields.Char(string='floor')
    housing_number = fields.Char(string='housing number')
    rent_amount = fields.Float(string='Rent Amount')
    housing_type = fields.Selection([
        ('apartment', 'apartment'),
        ('villa', 'villa'),
        ('popular_house', 'popular house'),
        ('tent', 'tent'),
        ('Appendix', 'Appendix'), ], default='apartment')
    property_instrument_number = fields.Char(string='Property Instrument number')
    property_instrument_attach = fields.Many2many('ir.attachment','rel_property_instrument_attach_attachment','benefit_id','attachment_id',string='Property Instrument Attach')
    electricity_attach = fields.Many2many('ir.attachment','rel_electricity_attach_attachment','benefit_id','attachment_id',string='Electricity Attach')
    property_instrument_date = fields.Date(string='Property Instrument Date')
    location_url = fields.Char(string='Location URL')
    location = fields.Char(string='location')
    rooms_number = fields.Integer('Rooms Number')
    water_bill_account_number = fields.Char(string='water Bill Account Number', )
    electricity_bill_account_number = fields.Char(string='Electricity Bill Account Number')
    domestic_labor_ids = fields.Many2many('domestic.labor')
    responsible = fields.Selection(string='responsible', selection=[('father', 'Father'),
                                                                    ('mother', 'mother'),
                                                                    ('other', 'other')], required=False, )
    responsible_id = fields.Many2one('grant.benefit', domain="[('is_responsible','=',True)]", string='', required=False)
    qr_code = fields.Binary( attachment=True, compute='_compute_qr_code')
    ## car data
    car_ids = fields.One2many('cars.line', 'benefit_id')
    car_count = fields.Integer(compute='_onchange_car_count')
    # compute = 'count_car'
    ####clothing data #
    cloth_ids = fields.One2many('benefit.cloth', 'benefit_id')
    expenses_request_ids = fields.One2many('benefit.expenses', 'benefit_id')
    expenses_ids = fields.One2many('expenses.line', 'benefit_id')
    # Father's case and his data # Birth Date # Address # dead data
    # Father's case and his data
    # family_name = fields.Char(string="Family Name", tracking=True)
    # father_name = fields.Char(string="Father First Name", tracking=True)
    # father_second_name = fields.Char(string="Father Second Name", tracking=True)
    # father_third_name = fields.Char(string="Father Third Name", tracking=True)
    # father_family_name = fields.Char(string="Father Family Name", tracking=True)
    father_id_number = fields.Char(string="Id Number", tracking=True)
    father_marital = fields.Selection(
        [('single', _('Single')), ('married', _('Married')), ('widower', _('Widower')), ('divorced', _('Divorced'))],
        _('Marital Status'), default='single', tracking=True)
    father_job = fields.Char(string='Father Job')
    father_id_number_type = fields.Selection([('citizen', _('Citizen')),('resident', _('Resident')),('visitor', _('Visitor'))],string='Father ID number type')
    father_birth_date = fields.Date(string="Birth Date")
    father_age = fields.Integer(string="Age", compute='_compute_get_father_age')
    father_country_id = fields.Many2one('res.country', 'Father Nationality', tracking=True)
    father_city_id = fields.Many2one('res.country.city', string='City')
    father_dead_reason = fields.Char(string='Dead Reason', required=False)
    father_dead_date = fields.Date(string="Father Dead Date")
    father_dead_country_id = fields.Many2one('res.country', string='Father Dead Country', tracking=True)
    father_dead_city_id = fields.Many2one('res.country.city', string='Father Dead City',domain="[('country_id', '=', father_dead_country_id)]")
    father_dead_certificate = fields.Many2many('ir.attachment', 'rel_father_dead_attachment','benefit_id','attachment_id',string='Father Dead Certificate')
    # Mother's case and her data # Birth Date # Address # dead data
    mother_relation = fields.Selection(
        [('mother', _('Mother')), ('replacement_mother', _('Replacement Mother'))])
    mother_relationn = fields.Many2one('relation.settings',domain="['|',('relation_type','=','mother'),('relation_type','=','replacement_mother')]")
    replacement_mother_relation = fields.Many2one('relation.settings',domain="[('relation_type','=','replacement_mother')]")
    mother_id = fields.Many2one('grant.benefit', domain="[('benefit_type','!=','orphan'),('gender','=','female')]")
    mother_name = fields.Char(string="Mother Name", tracking=True)
    mother_second_name = fields.Char(string="Mother Second Name", tracking=True)
    mother_third_name = fields.Char(string="Mother Third Name", tracking=True)
    mother_family_name = fields.Char(string="MotherFamily Name", tracking=True)
    mother_country_id = fields.Many2one('res.country', 'Mother Nationality', tracking=True)
    mother_id_number = fields.Char(string="Id Number", tracking=True)
    mother_id_number_type = fields.Selection([('citizen', _('Citizen')),('resident', _('Resident')),('visitor', _('Visitor'))],string='Mother ID number type')
    mother_marital = fields.Selection(
        [('married', _('Married')), ('widower', _('Widower')), ('divorced', _('Divorced')),
         ('divorced_from_another_man', _('Divorced From Another Man'))
            , ('prisoner', _('Prisoner')), ('dead', _('Dead')), ('hanging', _('Hanging'))],
        _('Marital Status'))
    mother_marital_conf = fields.Many2one('marital.status',string='Mother Marital')
    mother_is_dead = fields.Boolean(string='Mother Is Dead?',related='mother_marital_conf.is_dead')
    mother_dead_country_id = fields.Many2one('res.country', string='Mother Dead Country', tracking=True)
    mother_dead_city_id = fields.Many2one('res.country.city', string='Mother Dead City',domain="[('country_id', '=', mother_dead_country_id)]")
    mother_location = fields.Selection(
        [('with_husband_and_children', _('With Husband And Children')), ('with_children', _('With Children')),
         ('not_live_with_children', _('Not live with children'))], string='Mother Location')
    mother_location_conf = fields.Many2one('location.settings',string='Mother Location',domain="[('location_type','=','mother_location')]")
    is_mother_work = fields.Boolean('Is Mother Work?')
    mother_has_disabilities = fields.Boolean('Has Disabilities?')
    mother_income = fields.Float("Mother Income")
    mother_birth_date = fields.Date(string="Birth Date")
    mother_age = fields.Integer(string="Age", compute='_compute_get_mother_age')
    mother_city_id = fields.Many2one('res.country.city', string='City')
    mother_dead_reason = fields.Char(string='Dead Reason', required=False)
    mother_dead_date = fields.Date(string="Mother Certificate Date")
    mother_dead_certificate = fields.Many2many('ir.attachment', 'rel_mother_dead_attachment','benefit_id','attachment_id',string='Mother Dead Certificate')
    member_ids = fields.One2many('family.member', 'benefit_id')
    # orphan
    orphan_ids = fields.Many2many('grant.benefit', 'orphan_list', 'id_number', 'mother_id',
                                  compute='_orphan_list_compute')
    orphan_count = fields.Integer(
        string='',
        required=False)
    # widows and divorcees
    widows_ids = fields.One2many('widow.family', 'benefit_id', string='Widows', required=False)
    divorcee_ids = fields.One2many('divorcee.family', 'benefit_id', string='divorcee', required=False)
    # Husband info
    husband_name = fields.Char('Husband')
    husband_id = fields.Char('Husband ID')
    date_death_husband = fields.Date()
    date_divorcee = fields.Date()
    # Education_data
    education_status = fields.Selection(string='Education Status',selection=[('educated', 'educated'), ('illiterate', 'illiterate'),('under_study_age','Under Study Age')])
    case_study = fields.Selection(string='Case Study',
                                  selection=[('continuous', 'continuous'), ('intermittent', 'intermittent'),
                                             ('graduate', 'Graduate')])
    illiterate_reason = fields.Char(string='Illiterate Reason')
    intermittent_reason = fields.Many2one('education.illiterate.reason',string='Intermittent Reason')
    education_entity = fields.Selection(string='Education Entity', selection=[('governmental', 'Governmental'),
                                                                              ('special', 'Special')])
    education_start_date = fields.Date(string='Education Start Date')
    education_end_date = fields.Date(string='Education End Date')
    educational_certificate = fields.Many2many('ir.attachment','rel_educational_certificate_attachment','benefit_id','attachment_id',string='Educational Certificate')
    last_education_entity = fields.Selection(string='Last Education Entity',
                                             selection=[('governmental', 'Governmental'),
                                                        ('special', 'Special')])
    entities = fields.Many2one("education.entities", string='Entity')
    last_entities = fields.Many2one("education.entities", string='Last Entity')
    education_levels = fields.Many2one("education.level", string='Education Levels')
    last_education_levels = fields.Many2one("education.level", string='Last Education Levels')
    nearest_literacy_school = fields.Char(string='The Nearest Literacy School', required=False)
    literacy_school_note = fields.Text(string="Literacy School Note", required=False)
    classroom = fields.Many2one('education.classroom', string='Classroom')
    last_classroom = fields.Many2one('education.classroom', string='Last Classroom')
    degree = fields.Many2one('education.result', string='Degree')
    last_degree = fields.Many2one('education.result', string='Last Degree')
    percentage = fields.Float(string="Percentage%")
    last_percentage = fields.Float(string="Last Percentage%")
    last_education_start_date = fields.Date(string='Last Education Start Date')
    last_education_end_date = fields.Date(string='Last Education End Date')
    last_educational_certificate = fields.Many2many('ir.attachment','rel_last_educational_certificate_attachment','benefit_id','attachment_id',string='Last Educational Certificate')
    end_date = fields.Date('End Date')
    specialization_ids = fields.Many2one('specialization.specialization', string='specialization')
    last_specialization_ids = fields.Many2one('specialization.specialization', string='Last Specialization')
    weak_study = fields.Many2many('study.material',relation='grant_benefit_weak_study_rel',string='Weak Study')
    educational_institution_information = fields.Char('Educational institution information')
    graduation_status = fields.Selection(string='Education Status', selection=[('graduated', 'graduated'),
                                                                               ('ungraduated', 'ungraduated'),
                                                                               ('intermittent', 'intermittent')])
    graduation_date = fields.Date('Graduation Date')
    reasons_for_interruption = fields.Char('Reasons for interruption')
    interruption_date = fields.Date('Interruption Date')
    # attach
    study_document_attached = fields.Many2many('ir.attachment','rel_study_document_attachment','benefit_id','attachment_id',string="Study Document Attached")
    acadimec_regsteration_attached = fields.Binary(string="Acadimec Regsteration Attached",attachment=True )
    Transcript_attached = fields.Binary(string="Transcript Attached",attachment=True )
    # Quran memorize
    quran_memorize_name = fields.Char(string='')
    number_parts = fields.Integer(string='')
    # is craft skills
    craft_skill_ids = fields.One2many('craft.skills', 'benefit_id', string='Craft Skill')
    training_inclinations_ids = fields.One2many('training.inclinations', 'benefit_id', string='Training Inclinations')
    ### alhaju , amra and zakat fitr ####
    amra_date = fields.Date(string='')
    ######################
    food_surplus_type = fields.Many2many('food.surplus.type', string='')
    # Income and salary
    salary_ids = fields.One2many('salary.line', 'benefit_id', string='')
    # Commercial Record
    is_active = fields.Boolean(string='')
    commercial_record_code = fields.Char(string='Commercial Record Code')
    commercial_record_attach = fields.Binary(attachment=True)
    commercial_record_amount = fields.Float(string='')
    # other_associations
    associations_ids = fields.One2many('associations.line', 'benefit_id', string='')
    benefit_behavior_ids = fields.One2many('benefit.behaviors', 'benefit_id', string='')
    # Refuse Reason
    first_refusal_reason = fields.Text(string='First Refusal Reason', tracking=True)
    first_refuse_date = fields.Date(tracking=True)
    final_refusal_reason = fields.Text(string='Final Refusal Reason', tracking=True)
    final_refuse_date = fields.Date(tracking=True)
    black_list_reason = fields.Text(string='Black List Reason', tracking=True)
    black_list_message = fields.Text(string='Black List Message')
    # health information#
    # diseases
    hospital_id = fields.Many2one('hospital.hospital', string='')
    hospital_attach = fields.Binary(attach=True)
    diseases_type = fields.Selection(string='Diseases Type', selection=[('chronic', 'chronic'),
                                                                        ('psycho', 'psycho'),
                                                                        ('organic', 'organic')])
    treatment_used = fields.Char(string='')
    treatment_amount = fields.Float(string='')
    is_treatment_amount_country = fields.Boolean(string='')
    treatment_amount_country_Monthly = fields.Float(string='')
    treatment_amount_country_description = fields.Text(string="")
    treatment_amount_country_attach = fields.Binary(attachment=True)
    # Hospital information
    hospital_card = fields.Binary(attachment=True)
    # disability
    disability_type = fields.Char(string='')
    disability_accessories = fields.Char(string='')
    disability_attach = fields.Binary(attachment=True)
    disability_amount = fields.Float()
    # Medical Insurance
    insurance_type = fields.Many2one('insurance.type')
    insurance_company = fields.Many2one('insurance.company')
    insurance_amount = fields.Float()
    insurance_attach = fields.Binary(attachment=True)
    insured_party = fields.Many2one('res.company')
    # Weight rate
    weight = fields.Float('Weight')
    height = fields.Float('Height')
    p_weight = fields.Float('Overweight', store=True, compute="_compute_obesity_rate", )
    sport_ids = fields.One2many('sport.line', 'benefit_id')
    wife_number = fields.Integer(string="Wife")
    child_number = fields.Integer(string="Children")
    old_stage = fields.Char(string='old Stage', tracking=True)
    dead_certificate = fields.Binary(string="Certificate",attachment=True)
    dead_certificate_date = fields.Date(string="Certificate Date")
    approve_date = fields.Date(string="Approve Date")
    benefit_needs_value = fields.Float()
    benefit_needs_percent = fields.Float()
    followers_total = fields.Integer(string="followers Total")
    followers_out_total = fields.Integer(string="followers Total", )
    expenses_total = fields.Integer(string="Expenses", compute="get_total_expenses")
    #################################################################
    # Boolean Fields to use in filters#TODO
    #################################################################
    is_responsible = fields.Boolean(string='')  # Differentiate between a primary beneficiary and a dependent
    father_is_life = fields.Boolean(string="Life")
    mother_is_life = fields.Boolean(string="Life")
    is_widows = fields.Boolean(string='is widows', required=False)
    is_divorcee = fields.Boolean(string='is Divorcee', required=False)
    is_want_education = fields.Boolean(string='is Want Education', required=False)
    is_quran_memorize = fields.Boolean('memorize the quran ?')
    is_craft = fields.Boolean(string='')
    is_alhaju = fields.Boolean(string='IS Hajj')
    is_amra = fields.Boolean(string='IS Umra')
    is_zakat_fitr = fields.Boolean(string='Zakat Al-Fitr')
    is_food_basket = fields.Boolean(string='Audhea')
    has_car= fields.Boolean('Has Car?')
    has_othaim_family_number = fields.Boolean('Has Othaim family number?')
    othaim_family_number = fields.Char(string="Othaim family number")
    is_producer = fields.Boolean(string='Producer')
    is_food_surplus = fields.Boolean(string='food surplus')
    is_loans = fields.Boolean('loans')
    is_al_al_bayt = fields.Boolean(string='Al al-Bayt')
    is_commercial_record = fields.Boolean(string='Commercial Record')
    is_other_associations = fields.Boolean(string='other associations?')
    is_smoke = fields.Boolean('Smoke')
    # health_status
    is_diseases = fields.Boolean()
    is_disability = fields.Boolean(string='')
    is_insurance = fields.Boolean()
    is_sport = fields.Boolean()
    support_separation = fields.Boolean(string="Support Separation", tracking=True)
    is_life = fields.Boolean(string="Life", default=True)
    total_expenses = fields.Float('Total Expenses', compute="get_total_expenses")
    total_income = fields.Float('Total Income', compute="get_total_income")
    benefit_member_count = fields.Integer(string="Members count", compute="get_members_count")
    non_member_count = fields.Integer(string="Non Benefit Members count", compute="get_non_members_count")
    member_income = fields.Integer(string="Member Income Average", compute="get_member_income",store=True)
    request_activity_id = fields.Many2one('mail.activity')
    STATE_SELECTION = [
        ('draft', 'Draft'),
        ('confirm', 'Confirm'),
        ('validate', 'Validate'),
        ('review', 'Approved'),
        ('approve', 'Approve'),
        ('cancelled', 'Cancelled'),
        ('closed', 'Closed'),
    ]

    # add new customuzation
    state = fields.Selection(STATE_SELECTION, default='draft', tracking=True)


    branch_custom_id = fields.Many2one('branch.settings', string="Branch")
    district_id = fields.Many2one('res.districts', string="District", domain="[('branch_custom_id','=',branch_custom_id)]")
    meal_card = fields.Boolean(string="Meal Card",related="district_id.meal_card", store=True,related_sudo=True)
    attachment_ids = fields.One2many('ir.attachment', 'benefit_id')
    family_debits_ids = fields.One2many('family.debits', 'benefit_id')
    researcher_id = fields.Many2one("committees.line", string="Researcher")
    auto_accept_for_member = fields.Boolean(string="Auto Accept For members", default=True)
    last_visit_date = fields.Datetime(string='Last Visit Date')
    # Benefit Housing Information
    # housing_name = fields.Char(compute='_compute_get_name')
    zip = fields.Char('Zip', change_default=True, readonly=False, store=True)
    url = fields.Char()
    url_html = fields.Html(
        sanitize=False,
        compute="get_html")
    image = fields.Binary(string="", )
    image_1 = fields.Binary(string="", )
    image_2 = fields.Binary(string="", )
    image_3 = fields.Binary(string="", )
    image_4 = fields.Binary(string="", )
    nearby_mosque = fields.Char(string='Nearby mosque')
    housing_note = fields.Char(string='housing note')
    note_neighborhood = fields.Char()
    contract_num = fields.Char(string="Contract Number")
    rent_start_date = fields.Date(string='Rent Start Date')
    rent_end_date = fields.Date(string='Rent End Date')
    rent_attachment = fields.Many2many('ir.attachment','rel_rent_attachment_attachment','benefit_id','attachment_id',string='Rent Attachment')
    national_address_attachment = fields.Many2many('ir.attachment','rel_national_address_attachment','benefit_id','attachment_id',string='National Address Attachment')
    payment_type = fields.Selection([('1', 'Yearly'),('2', 'Half Year'),('4', 'Quarterly')],string='Payment Type')
    housing_cat = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('bad', 'Bad'),
        ('collapsible', 'Collapsible')])
    property_type = fields.Selection([
        ('ownership', 'ownership'),
        ('rent', 'rent'),
        ('charitable', 'charitable'),
        ('ownership_shared', 'Ownership Shared'),
        ('rent_shared', 'Rent Shared')])
    room_ids = fields.One2many('benefit.housing.rooms', inverse_name='housing_id')
    request_producer = fields.Many2one('res.partner',string='Request Producer',default=lambda self: self.env.user.partner_id)
    request_producer_relation = fields.Many2one('relation.settings',string='Request Producer Relation',domain="[('relation_type','=','other relation')]")
    # Suspend
    is_excluded_suspension = fields.Boolean('Excluded from suspension?')
    suspend_reason = fields.Many2one('suspend.reason', string='Suspend Reason')
    reason = fields.Text(string='Reason')
    suspend_description = fields.Text(string='Suspend Description')
    suspend_attachment = fields.Many2many('ir.attachment','rel_suspend_attachment_attachment','benefit_id','attachment_id',string='Suspend Attachment')
    suspend_type = fields.Selection(
        selection=[('temporarily_suspend', 'Temporarily Suspended'), ('suspend', 'Suspend')], string="Suspend Type")
    suspend_method = fields.Selection(selection=[('manual', 'Manual'), ('auto', 'Auto')], string="Suspend Method")
    #Exception fields
    exception_reason = fields.Many2one('exception.reason', string='Exception Reason')
    exception_description = fields.Text(string='Exception Description')
    exception_type = fields.Selection(
        selection=[('temporarily_exception', 'Temporarily Exception'), ('permanent_exception', 'Permanent Exception')],
        string="Exception Type")
    exception_attachment = fields.Many2many('ir.attachment','rel_exception_attachment','benefit_id','attachment_id',string='Exception Attachment')
    exception_start_date = fields.Datetime(string='Exception Start Date')
    exception_end_date = fields.Datetime(string='Exception End Date')

    sponsor_id = fields.Many2one('res.partner', string='Sponsor',domain="[('account_type','=','sponsor')]")

    family_monthly_income = fields.Float(string="Family Monthly Income", compute='_get_family_monthly_values')
    family_monthly_meals = fields.Float(string="Family Monthly Meals", compute='_get_family_monthly_values')
    family_monthly_clotting = fields.Float(string="Family Monthly Clotting", compute='_get_family_monthly_values')
    total_family_expenses = fields.Float(string="Total Family Expenses", compute='_get_family_monthly_values')
    total_move_lines = fields.Integer(string="Total Move Lines", compute='_get_total_move_lines')
    invoices_count = fields.Integer(string="Invoices Count", compute='_get_invoices_count')
    required_attach  = fields.Selection(selection=[('true', 'True'), ('false', 'False')],compute='get_required_attach',store=True)
    income_required_attach  = fields.Selection(selection=[('true', 'True'), ('false', 'False')],compute='get_income_required_attach',store=True)
    sa_iban = fields.Char('SA',default='SA',readonly=True)
    #Replacement Mother
    add_replacement_mother = fields.Boolean('Add Replacement Mother?')
    replacement_mother_name = fields.Char(string="Replacement Mother Name", tracking=True)
    replacement_mother_second_name = fields.Char(string="Replacement Mother Second Name", tracking=True)
    replacement_mother_third_name = fields.Char(string="Replacement Mother Third Name", tracking=True)
    replacement_mother_family_name = fields.Char(string="Replacement Mother Family Name", tracking=True)
    replacement_mother_country_id = fields.Many2one('res.country', 'Replacement Mother Nationality', tracking=True)
    replacement_mother_id_number = fields.Char(string="Replacement Mother Id Number", tracking=True)
    replacement_mother_id_number_type = fields.Selection([('citizen', _('Citizen')),('resident', _('Resident')),('visitor', _('Visitor'))],string='Replacement Mother ID number type')
    replacement_mother_marital_conf = fields.Many2one('marital.status', string='Replacement Mother Marital')
    replacement_mother_is_dead = fields.Boolean(string='Replacement Mother Is Dead?',related='replacement_mother_marital_conf.is_dead')
    replacement_mother_dead_country_id = fields.Many2one('res.country', string='Mother Dead Country', tracking=True)
    replacement_mother_dead_city_id = fields.Many2one('res.country.city', string='Mother Dead City',domain="[('country_id', '=', replacement_mother_dead_country_id)]")
    replacement_mother_location = fields.Selection(
        [('with_husband_and_children', _('With Husband And Children')), ('with_children', _('With Children')),
         ('not_live_with_children', _('Not live with children'))], string='Replacement Mother Location')
    replacement_mother_location_conf = fields.Many2one('location.settings',string='Replacement Mother Location',domain="[('location_type','=','mother_location')]")
    replacement_is_mother_work = fields.Boolean('Is Replacement Mother Work?')
    replacement_mother_has_disabilities = fields.Boolean('Has Disabilities?')
    replacement_mother_income = fields.Float("Replacement Mother Income")
    replacement_mother_birth_date = fields.Date(string="Replacement Mother Birth Date")
    replacement_mother_age = fields.Integer(string="Replacement Mother Age", compute='_compute_get_replacement_mother_age')
    replacement_mother_city_id = fields.Many2one('res.country.city', string='City')
    replacement_mother_dead_reason = fields.Char(string='Dead Reason', required=False)
    replacement_mother_dead_date = fields.Date(string="Replacement Mother Certificate Date")
    replacement_mother_dead_certificate = fields.Many2many('ir.attachment', 'rel_replacement_mother_dead_attachment', 'benefit_id', 'attachment_id', string='Replacement Mother Dead Certificate')
    replacement_mother_status = fields.Selection(selection=[
        ('benefit', 'Benefit'),
        ('non_benefit', 'Non Benefit'),
    ], string='Replacement Mother Status', compute="check_replacement_mother_status", store=True, default=False)
    replacement_is_alhaju = fields.Boolean(string='IS Hajj')
    replacement_is_amra = fields.Boolean(string='IS Umra')
    # Education_data for replacement mother
    replacement_education_status = fields.Selection(string='Education Status',selection=[('educated', 'educated'), ('illiterate', 'illiterate'),('under_study_age','Under Study Age')])
    replacement_case_study = fields.Selection(string='Case Study',
                                  selection=[('continuous', 'continuous'), ('intermittent', 'intermittent'),
                                             ('graduate', 'Graduate')])
    replacement_illiterate_reason = fields.Char(string='Illiterate Reason')
    replacement_intermittent_reason = fields.Many2one('education.illiterate.reason', string='Intermittent Reason')
    replacement_education_entity = fields.Selection(string='Education Entity', selection=[('governmental', 'Governmental'),
                                                                              ('special', 'Special')])
    replacement_entities = fields.Many2one("education.entities", string='Entity')
    replacement_specialization_ids = fields.Many2one('specialization.specialization', string='specialization')
    replacement_classroom = fields.Many2one('education.classroom', string='Classroom')
    replacement_degree = fields.Many2one('education.result', string='Degree')
    replacement_percentage = fields.Float(string="Percentage%")
    replacement_education_start_date = fields.Date(string='Education Start Date')
    replacement_education_end_date = fields.Date(string='Education End Date')

    replacement_last_education_entity = fields.Selection(string='Last Education Entity',
                                             selection=[('governmental', 'Governmental'),
                                                        ('special', 'Special')])
    replacement_last_entities = fields.Many2one("education.entities", string='Last Entity')
    replacement_education_levels = fields.Many2one("education.level", string='Education Levels')
    replacement_last_education_levels = fields.Many2one("education.level", string='Last Education Levels')
    replacement_last_specialization_ids = fields.Many2one('specialization.specialization', string='Last Specialization')
    replacement_educational_certificate = fields.Many2many('ir.attachment','rel_replacement_educational_certificate_attachment','benefit_id','attachment_id',string='Educational Certificate')

    replacement_last_classroom = fields.Many2one('education.classroom', string='Last Classroom')
    replacement_last_degree = fields.Many2one('education.result', string='Last Degree')
    replacement_last_percentage = fields.Float(string="Last Percentage%")
    replacement_last_education_start_date = fields.Date(string='Last Education Start Date')
    replacement_last_education_end_date = fields.Date(string='Last Education End Date')
    replacement_last_educational_certificate = fields.Many2many('ir.attachment','rel_replacement_last_educational__certificate_attachment','benefit_id','attachment_id',string='Last Educational Certificate')
    replacement_weak_study = fields.Many2many('study.material',relation='grant_benefit_replacement_weak_study_rel',string='Weak Study')

    member_id = fields.Many2one('family.member', string='Member', ondelete='cascade', )
    benefit_member_ids = fields.One2many('grant.benefit.member', 'grant_benefit_id', string="Benefit Member")

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
    need_calculator = fields.Selection([('high', 'High Need'), ('medium', 'Medium Need'), ('low', 'Low Need'), ],
                                       readonly=1, string="Need Calculator", )
    detainee_file_id = fields.Many2one('detainee.file', string="Detainee File", tracking=True, related='')
    beneficiary_category = fields.Selection(related='detainee_file_id.beneficiary_category',
                                            string='Beneficiary Category')
    benefit_breadwinner_ids = fields.One2many('grant.benefit.breadwinner', 'grant_benefit_ids',
                                              string="Benefit breadwinner")



    member_count = fields.Integer(string="Members Count", compute="_compute_member_count", readonly=1)

    @api.depends('benefit_member_ids')
    def _compute_member_count(self):
        self.member_count = 0
        for rec in self:
            filtered = rec.benefit_breadwinner_ids.filtered(lambda bw: bw.relation_id.name != 'زوجة مطلقة')
            rec.member_count = len(rec.benefit_member_ids) + len(filtered)
    @api.depends('attachment_ids')
    def get_required_attach(self):
        for rec in self.attachment_ids:
            if rec.is_required and not rec.datas:
                self.required_attach = None
                break
            elif rec.is_required and rec.datas:
                self.required_attach = 'true'
            elif rec.is_default and not rec.is_required and (rec.datas or not rec.datas):
                self.required_attach = 'true'
            else:
                self.required_attach = 'true'

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
            'domain': [('benefit_id', '=', self.id)],
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
            'domain': [('benefit_id', '=', self.id)],
            'target': 'current',
        }

    @api.depends('salary_ids')
    def get_income_required_attach(self):
        for rec in self.salary_ids:
            if rec.is_required and not rec.salary_attach:
                self.income_required_attach = None
                break
            elif rec.is_required and rec.salary_attach:
                self.income_required_attach = 'true'
            elif rec.is_default and not rec.is_required and (rec.salary_attach or not rec.salary_attach):
                self.income_required_attach = 'true'
            else:
                self.income_required_attach = 'true'

    def _get_invoices_count(self):
        for rec in self:
            rec.invoices_count = self.env['account.move'].search_count([
                ('benefit_family_ids', 'in', [rec.id]),('move_type','=','in_invoice')
            ])


    def _get_total_move_lines(self):
        for rec in self:
            rec.total_move_lines = self.env['account.move.line'].search_count([('benefit_family_id', '=', rec.id)

            ])

    def action_open_related_move_line_records(self):
        """ Opens a tree view with related records filtered by a dynamic domain """
        move_lines = self.env['account.move.line'].search([
            ('benefit_family_id', '=', self.id)
        ]).ids

        action = {
            'type': 'ir.actions.act_window',
            'name': 'Move Lines',
            'res_model': 'account.move.line',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', move_lines)],
            'target': 'current',
        }
        return action


    def action_open_related_invoice_records(self):
        """ Opens a tree view with related records filtered by a dynamic domain """
        invoices = self.env['account.move'].search([
            ('benefit_family_ids', 'in', [self.id]),('move_type','=','in_invoice')
        ]).ids
        action = {
            'type': 'ir.actions.act_window',
            'name': 'Invoices',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', invoices)],
            'target': 'current',
        }
        return action

    def _get_family_monthly_values(self):
        validation_setting = self.env["family.validation.setting"].search([], limit=1)
        for rec in self:
            if rec.benefit_category_id.id in validation_setting.benefit_category_ids.ids:
                total_family_members = rec.benefit_member_count
                rec.family_monthly_income = total_family_members * validation_setting.cash_expense
                rec.family_monthly_meals = total_family_members * validation_setting.meal_expense
                rec.family_monthly_clotting = total_family_members * validation_setting.clothing_expense
                rec.total_family_expenses = rec.family_monthly_income + rec.family_monthly_meals + rec.family_monthly_clotting
            else:
                rec.family_monthly_income = 0
                rec.family_monthly_meals = 0
                rec.family_monthly_clotting = 0
                rec.total_family_expenses = 0

    def get_html(self):
        for rec in self:
            print(f'<iframe id="custom_src" height="500" width="500" src="{rec.url}"></iframe>')
            rec.url_html = f'<iframe id="custom_src" height="500" width="500" src="{rec.url}"/>'

    # @api.multi
    def open_map(self):
        for Location in self:
            url = "http://maps.google.com/maps?oi=map&q="
            if Location.street:
                url += Location.street.replace(' ', ',')
            if Location.city_id:
                url += '+' + Location.district_id.name.replace(' ', ',')
                # url += '+' + Location.city_id.name.replace(' ', ',')
                url += '+' + Location.city_id.state_id.name.replace(' ', '')
                url += '+' + Location.zip.replace(' ', ',')
                url += '+' + Location.city_id.country_id.name.replace(' ', ',')
            if Location.nearby_mosque:
                url += Location.nearby_mosque.replace(' ', ',')
            return {
                'type': 'ir.actions.act_url',
                'target': 'new',
                'url': url
            }

    @api.onchange('url')
    def onchange_image_url(self):
        if self.image_url:
            self.img_attach = '<img id="img" src="%s"/>' % self.url

    def get_researchers_email(self):
        email_ids = ''
        for rec in self.researcher_id.employee_id:
            if email_ids:
                email_ids = email_ids + ',' + str(rec.work_email)
            else:
                email_ids = str(rec.work_email)
        return email_ids

    @api.depends('room_ids')
    def get_rooms_total(self):
        for rec in self:
            if rec.id:
                rooms = rec.env['benefit.housing.rooms'].sudo().search([('housing_id', '=', rec.id)])
                rec.rooms_number = len(rooms)

    @api.onchange('room_ids')
    def onchange_room_ids(self):
        res = {}
        items_ids = []
        for record in self:
            items_ids.append(record.id)
        res['domain'] = {'items': [('room_id', 'in', items_ids)]}
        return res

    @api.onchange("father_country_id", 'mother_country_id')
    def onchange_father_mother_country_id(self):
        res = {}
        for rec in self:
            if rec.father_country_id and rec.mother_country_id:
                if rec.mother_country_id.code != 'SA' and rec.father_country_id.code != 'SA' and not rec.mother_country_id.is_excluded and not rec.father_country_id.is_excluded :
                    rec.mother_country_id = False
                    res['warning'] = {'title': _('ValidationError'),
                                      'message': _('Non-Saudi mothers and fathers cannot register')}
                    return res

    @api.onchange('father_id_number', 'mother_id_number', 'replacement_mother_id_number')
    def _onchange_id_numbers(self):
        id_numbers = {
            'رقم هوية الأب': self.father_id_number,
            'رقم هوية الأم': self.mother_id_number,
            'رقم هوية الأم البديلة': self.replacement_mother_id_number,
        }

        # Check each ID number for 10-digit format and uniqueness within the parent model
        unique_ids = set()
        for label, id_number in id_numbers.items():
            if id_number:
                if not re.match(r'^\d{10}$', id_number):
                    raise ValidationError(_("%s must contain exactly 10 digits.")%label)
                if id_number in unique_ids:
                    raise ValidationError(_("%s must be unique within the same record.") % label)
                if id_number.startswith('1') and label == 'رقم هوية الأب':
                    self.father_country_id =  self.env["res.country"].search([('code','=','SA')],limit=1).id
                    self.father_id_number_type = 'citizen'
                if id_number.startswith('1') and label == 'رقم هوية الأم':
                    self.mother_country_id =  self.env["res.country"].search([('code','=','SA')],limit=1).id
                    self.mother_id_number_type = 'citizen'
                if id_number.startswith('1') and label == 'رقم هوية الأم البديلة':
                    self.replacement_mother_country_id =  self.env["res.country"].search([('code','=','SA')],limit=1).id
                    self.replacement_mother_id_number_type = 'citizen'
                unique_ids.add(id_number)

        # Check for uniqueness against `member_id_number` in child records and across database records
        for member in self.member_ids:
            if member.member_id_number and member.member_id_number in unique_ids:
                raise ValidationError(_("The ID number %s in the Family Members list must be unique across the record.")%member.member_id_number)
        # Check for duplicate IDs across records in the database
        for id_number in unique_ids:
            duplicate_record_family = self.env['grant.benefit'].search([
                '|','|', ('father_id_number', '=', id_number), ('mother_id_number', '=', id_number),
                ('replacement_mother_id_number', '=', id_number),('id','!=',self._origin.id)
            ], limit=1)
            duplicate_record_member = self.env['family.member'].search([('member_id_number', '=', id_number)], limit=1)
            if duplicate_record_family :
                raise ValidationError(_("The ID number {} already exists in family with code {}. Please enter a unique ID number.").format(id_number, duplicate_record_family.code))
            if duplicate_record_member :
                raise ValidationError(_("The ID number {} already exists in family with code {}. Please enter a unique ID number.").format(id_number, duplicate_record_member.code))

    @api.onchange("family_bank")
    def onchange_family_bank(self):
        for rec in self:
            if rec.family_bank:
                exist = self.search([('family_bank', '=', rec.family_bank.id)])
                if exist:
                    raise ValidationError(
                        _('The Family Bank Already Exist!'))

    @api.model
    def _geo_localize(self, street='', zip='', city='', state='', country=''):
        geo_obj = self.env['base.geocoder']
        search = geo_obj.geo_query_address(
            street=street, zip=zip, city=city, state=state, country=country
        )
        result = geo_obj.geo_find(search, force_country=country)
        if result is None:
            search = geo_obj.geo_query_address(
                city=city, state=state, country=country
            )
            result = geo_obj.geo_find(search, force_country=country)
        return result, search

    def geo_localize(self):
        for location in self.with_context(lang='en_US'):
            result = self._geo_localize(
                street=location.street,
                zip=location.zip,
                city=location.city_id.name,
                state=location.state_id.name,
                country=location.country_id.name,
            )
            if result:
                location.write(
                    {
                        'lat': result[0][0],
                        'lon': result[0][1],
                    }
                )
            return True

    def get_location_on_map(self):
        for location in self.with_context(lang='en_US'):
            url = "http://maps.google.com/maps/search/?api=1&query=%s,%s" % (location.lat, location.lon),
            return {
                'type': 'ir.actions.act_url',
                'target': 'new',
                'url': url
            }

    @api.depends('mother_marital_conf', 'mother_income', 'mother_location_conf', 'mother_country_id', 'state')
    def check_mother_status(self):
        validation_setting = self.env["family.validation.setting"].search([], limit=1)
        mini_income_for_mother = validation_setting.mini_income_for_mother
        max_income_for_mother = validation_setting.max_income_for_mother
        for rec in self:
            rec.mother_status = False
            if not rec.mother_location_conf.is_benefit or not rec.mother_marital_conf.is_benefit or rec.state == 'suspended_second_approve':
                rec.mother_status = 'non_benefit'
            elif rec.mother_marital_conf.is_benefit :
                if rec.is_mother_work and rec.mother_country_id.code == 'SA' or (
                        rec.mother_country_id.code != 'SA' and rec.father_country_id.code == 'SA'):
                    if mini_income_for_mother < rec.mother_income <= max_income_for_mother:
                        rec.mother_status = 'non_benefit'
                    elif rec.mother_income <= mini_income_for_mother:
                        rec.mother_status = 'benefit'
                    elif rec.mother_income > max_income_for_mother:
                        rec.mother_status = 'benefit'
                elif not rec.is_mother_work and rec.mother_country_id.code == 'SA' or (
                        rec.mother_country_id.code != 'SA' and rec.father_country_id.code == 'SA'):
                    rec.mother_status = 'benefit'

    @api.depends('replacement_mother_marital_conf', 'replacement_mother_income', 'replacement_mother_location_conf', 'replacement_mother_country_id', 'state')
    def check_replacement_mother_status(self):
        validation_setting = self.env["family.validation.setting"].search([], limit=1)
        mini_income_for_mother = validation_setting.mini_income_for_mother
        max_income_for_mother = validation_setting.max_income_for_mother
        for rec in self:
            rec.replacement_mother_status = False
            if not rec.replacement_mother_location_conf.is_benefit or not rec.replacement_mother_marital_conf.is_benefit or rec.state == 'suspended_second_approve':
                rec.replacement_mother_status = 'non_benefit'
            elif rec.replacement_mother_marital_conf.is_benefit:
                if rec.replacement_is_mother_work and rec.replacement_mother_country_id.code == 'SA' or (
                        rec.replacement_mother_country_id.code != 'SA' and rec.father_country_id.code == 'SA'):
                    if mini_income_for_mother < rec.replacement_mother_income <= max_income_for_mother:
                        rec.replacement_mother_status = 'non_benefit'
                    elif rec.replacement_mother_income <= mini_income_for_mother:
                        rec.replacement_mother_status = 'benefit'
                    elif rec.replacement_mother_income > max_income_for_mother:
                        rec.replacement_mother_status = 'benefit'
                elif not rec.replacement_is_mother_work and rec.replacement_mother_country_id.code == 'SA' or (
                        rec.replacement_mother_country_id.code != 'SA' and rec.father_country_id.code == 'SA'):
                    rec.replacement_mother_status = 'benefit'

    def delete_from_db(self):
        find_id = self.env['benefit.housing'].search([])
        for r in find_id:
            r.unlink()

    @api.model
    def default_get(self, fields):
        res = super(GrantBenefitProfile, self).default_get(fields)

        # Get default attachments
        default_attachment = self.env["attachments.settings"].search([('is_default', '=', True)])

        # Prepare the list of default attachments for the one2many field
        default_attachments_data = []
        income_attachments_data = []
        for attach in default_attachment:
            if attach.attach_type == 'family_attach':
                default_attachments_data.append((0, 0, {
                    'name': attach.name,
                    'is_required': attach.is_required,
                    'is_default': attach.is_default,
                }))
            if attach.attach_type == 'income_attach':
                income_attachments_data.append((0, 0, {
                    'income_type': attach.id,
                    'is_required': attach.is_required,
                    'is_default': attach.is_default,
                }))

        # Add the default attachments to the res dictionary for attachment_ids
        if 'attachment_ids' in fields:
            res['attachment_ids'] = default_attachments_data
        if 'salary_ids' in fields:
            res['salary_ids'] = income_attachments_data
        return res

    # @api.model
    # def create(self, vals):
    #     res = super(GrantBenefitProfile, self).create(vals)
    #     if not res.code or res.code == _('New'):
    #         res.code = self.env['ir.sequence'].sudo().next_by_code('benefit.sequence') or _('New')
    #     return res

    def unlink(self):
        for order in self:
            if order.state not in ['draft']:
                raise UserError(_('You cannot delete this record'))
        return super(GrantBenefitProfile, self).unlink()

    def copy(self, default=None):
        """Override the copy method to prevent duplicating the record."""
        raise UserError(_('You cannot Duplicate this record'))

    def complete_data(self):
        message = self.create_message('complete_info')
        self.partner_id.send_sms_notification(message, self.phone)
        # self.state = 'complete_info'
        return {
            'name': _('Rerearcher Wizard'),
            'view_mode': 'form',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'res_model': 'researcher.family.wizard',
            'view_id': self.env.ref('odex_benefit.view_resarcher_family_wizard_form').id,
            'target': 'current',
        }

    def finish_complete_data(self):
        message = self.create_message('waiting_approve')
        self.partner_id.send_sms_notification(message, self.phone)
        for rec in self:
            mother_exist = self.env["family.member"].search([('member_id_number', '=', rec.mother_id_number),('relationn.relation_type','=','mother')], limit=1)
            replacement_mother_exist = self.env["family.member"].search([('member_id_number', '=', rec.replacement_mother_id_number),('relationn.relation_type','=','replacement_mother')], limit=1)
            if not mother_exist:
                rec.add_mother_as_member()
            if mother_exist:
                rec.replace_mother_as_member(mother_exist.id)
            if rec.add_replacement_mother:
                if not replacement_mother_exist:
                    rec.add_replacement_mother_as_member()
                if replacement_mother_exist:
                    rec.replace_replacement_mother_as_member(replacement_mother_exist.id)
            self.state = 'waiting_approve'

    def action_first_accepted(self):
        """Accept  registration"""
        for rec in self:
            rec.state = "first_approve"

    def action_second_accepted(self):
        """Accept  registration"""
        for rec in self:
            if not rec.user_id:
                self.create_user()

            rec.user_id.sudo().write({
                'groups_id': [(3, self.env.ref('base.group_user', False).id)],
            })
            # rec.user_id.sudo().write({
            #     'groups_id': [(4, self.env.ref('odex_benefit.group_benefit_user', False).id)],
            # })
            rec.user_id.sudo().write({
                'groups_id': [(4, self.env.ref('base.group_portal', False).id)],
            })
            rec.approve_date = datetime.now()
            self.sudo().send_approval_benefit_email()
            partner_ids = []
            for id in self.message_follower_ids.ids:
                partner_ids.append(self.env['mail.followers'].search([('id', '=', id)]).partner_id)
            self.state = "second_approve"
            self.sudo()._send_notification(partner_ids, rec.state)
        # for member in self.member_ids:
        #     member.create_member_partner()

    # @api.multi
    def action_first_refusal(self):
        """First refusal to entity registration"""
        domain = []
        context = {}
        context = dict(self.env.context or {})
        context['state'] = "first_refusal"
        self.partner_id.send_sms_notification("First Refusal", self.phone)
        context['active_id'] = self.id
        return {
            'name': _('Refuse Reason Wizard'),
            'view_mode': 'form',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'res_model': 'entity.refused.reason.wizard',
            'view_id': self.env.ref('odex_benefit.view_entity_refused_reason_wizard_form').id,
            'target': 'new',
            'domain': domain,
            'context': context,
        }

    # @api.multi
    def action_refuse(self):
        """Refuse entity registration"""
        domain = []
        context = dict(self.env.context or {})
        context['state'] = "refused"
        context['active_id'] = self.id
        return {
            'name': _('Refuse Reason Wizard'),
            'view_mode': 'form',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'res_model': 'entity.refused.reason.wizard',
            'view_id': self.env.ref('odex_benefit.view_entity_final_refused_reason_wizard_form').id,
            'target': 'new',
            'domain': domain,
            'context': context,
        }

    # @api.multi
    def action_black_list(self):
        """Move benefit to black list"""
        domain = []
        context = dict(self.env.context or {})
        context['state'] = "black_list"
        context['active_id'] = self.id
        return {
            'name': _('Black List Wizard'),
            'view_mode': 'form',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'res_model': 'entity.black.list.wizard',
            'view_id': self.env.ref('odex_benefit.view_entity_black_list_wizard_form').id,
            'target': 'new',
            'domain': domain,
            'context': context,
        }

    # @api.multi
    def action_edit_info(self):
        # bank_val = {
        #     'acc_number': self.acc_number,
        #     'acc_holder_name': self.acc_holder_name,
        #     'bank_id': self.bank_id.id,
        # }
        # self.partner_id.write({
        #     'name': self.name,
        #     'email': self.email,
        #     'phone': self.phone,
        #     'account_type': 'family',
        #     'code': self.code,
        #     'bank_ids': [(0, 0, bank_val)]
        # })
        user = self.user_id
        if not user:
            user = self.env['res.users'].sudo().search(
                [('partner_id', '=', self.partner_id.id), ('active', '=', False)])
            if user:
                user.write({'active': True})
            else:
                user = self.create_user()
        group_e = self.env.ref('odex_benefit.group_benefit_edit', False)
        try:
            group_e.sudo().write({'users': [(4, user.id)]})
            self.old_stage = self.state
            template = self.env.ref('odex_benefit.edit_benefit_email', False)
        except:
            pass
        self.state = 'edit_info'

    def not_alive(self):
        self.life = False
        self.state = 'not_leaving'

    def action_suspend(self):
        self.is_excluded_suspension = False
        for rec in self.member_ids:
            rec.is_excluded_suspension = False
            if rec.is_member_workflow:
                rec.is_member_workflow = False
        return {
            'name': _('Suspend Reason Wizard'),
            'view_mode': 'form',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'res_model': 'suspend.reason.wizard',
            'view_id': self.env.ref('odex_benefit.view_suspend_reason_wizard_form').id,
            'target': 'new',
        }
        # rec.state = 'temporarily_suspended'

    def action_suspend_first_accept(self):
        for rec in self:
            rec.state = 'suspended_first_approve'

    def action_suspend_second_accept(self):
        for rec in self:
            rec.state = 'suspended_second_approve'

    def action_auto_suspend(self):
        # Fetch grants in second approval state that are not excluded from suspension
        grants = self.env["grant.benefit"].search(
            [('state', '=', 'second_approve'), ('is_excluded_suspension', '=', False)]
        )

        for grant in grants:
            # Check if there are no benefit members
            if grant.benefit_member_count == 0:
                grant.state = 'suspended_second_approve'
                grant.suspend_method = 'auto'

            # Check if any attachment of the grant is expired
            for attachment in grant.attachment_ids:
                if attachment.attach_status == 'expired':
                    # Change state to temporarily suspended if there are benefit members
                    if grant.benefit_member_count != 0:
                        grant.state = 'temporarily_suspended'
                        grant.suspend_method = 'auto'
                    break  # Exit attachment loop after processing

            # Check each member's attachments
            for member in grant.member_ids:
                for member_attachment in member.attachment_ids:
                    if member_attachment.attach_status == 'expired':
                        # Change state to temporarily suspended if there are benefit members
                        if grant.benefit_member_count != 0:
                            grant.state = 'temporarily_suspended'
                            grant.suspend_method = 'auto'
                        break  # Exit member attachment loop after processing

    def action_suspend_refuse(self):
        for rec in self:
            rec.state = 'second_approve'
            rec.get_member_income()

    #Excption Work flow
    def action_exception(self):
        return {
            'name': _('Exception Wizard'),
            'view_mode': 'form',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'res_model': 'exception.wizard',
            'view_id': self.env.ref('odex_benefit.view_exception_wizard_form').id,
            'target': 'new',
        }

    def action_exception_first_accept(self):
        for rec in self:
            rec.state = 'exception_first_approve'

    def action_exception_second_accept(self):
        for rec in self:
            rec.state = 'exception_second_approve'
    def action_exception_final_accept(self):
        for rec in self:
            rec.is_excluded_suspension = True
            rec.state = 'second_approve'
            for member in self.member_ids:
                member.is_excluded_suspension = True
            rec.get_member_income()

    def action_auto_exception(self):
        obj = self.env["grant.benefit"].search(
            [('state', '=', 'second_approve'), ('is_excluded_suspension', '=',  True)])
        for rec in obj:
            if rec.exception_end_date and rec.exception_end_date <= fields.Datetime.now():
                rec.is_excluded_suspension = False
                rec.state = 'suspended_second_approve'
                for member in rec.member_ids:
                    member.is_excluded_suspension = False

    def action_exception_refuse(self):
        for rec in self:
            rec.state = 'suspended_second_approve'
    # @api.multi
    def action_remove_from_black_list(self):
        """Remove entity from black list"""
        partner_ids = []
        for entity in self:
            if self.old_stage == 'draft':
                entity.state = 'draft'
            else:
                entity.state = 'second_approve'
            entity.black_list_message = False
            user = self.env['res.users'].search([('partner_id', '=', entity.partner_id.id)], limit=1)
            user.toggle_active()
            # activate user
            subject = _('Beneficiaries')
            state_label = dict(entity.fields_get(allfields=['state'])['state']['selection'])[entity.state]
            body = ' '.join(
                (_(u'The Beneficial '), entity.name, _(u' State changed to '), state_label, u'.')).encode(
                'utf-8')
            partner_ids += [(6, 0, entity.message_follower_ids.ids)]
            message_vals = {
                'subject': subject,
                'body': body,
                'partner_ids': partner_ids,
            }
            # entity.message_post(body=body, subject=subject, message_type='email')
            # entity.send_remove_from_black_list_email()

    @api.depends('car_ids')
    def _onchange_car_count(self):
        for rec in self:
            rec.car_count = len(rec.car_ids)

    @api.onchange('is_diseases')
    def onchange_is_diseases(self):
        for rec in self:
            rec.is_diseases = 'sick' if rec.is_diseases else 'healthy'

    def _onchange_is_has_needs(self):
        for rec in self:
            benefits_needs = rec.env['benefits.needs'].sudo().search(['|',
                                                                      ('benefit_id', '=', rec.id),
                                                                      ('benefit_ids', 'in', rec.id)])
            needs = []
            for need in benefits_needs:
                if need.state == 'published' and need.remaining_amount > 0.0:
                    needs.append(need.id)
            if len(needs) > 0:
                rec.sudo().has_needs = True
            elif len(needs) == 0:
                rec.sudo().has_needs = False

    def _orphan_list_compute(self):
        for rec in self:
            benefits = rec.env['grant.benefit'].sudo().search([('mother_id', '=', rec.id)])
            rec.orphan_ids = [(6, 0, benefits.ids)]
            rec.orphan_count = len(rec.orphan_ids)

    def _compute_orphan_Type(self):
        for rec in self:
            if rec.benefit_type == "orphan":
                if not rec.father_is_life and not rec.mother_is_life:
                    rec.orphan_status = 'parent'
                elif not rec.father_is_life:
                    rec.orphan_status = 'father'
                elif not rec.mother_is_life:
                    rec.orphan_status = 'mother'
                else:
                    rec.orphan_type = ''
            else:
                rec.orphan_type = ''

    @api.onchange('birth_date')
    def onchange_category(self):
        for rec in self:
            rec.expenses_ids = False
            for expenses in rec.benefit_category_id:
                if expenses.state == 'second_pprove':
                    for i in expenses.expenses_ids:
                        expenses = {}
                        expenses['expenses_type'] = i.expenses_type
                        expenses['amount'] = i.amount
                        rec.expenses_ids = [(0, 0, expenses)]
            expenses = self.env['benefit.expenses'].sudo().search(
                [('benefit_id', '=', self._origin.id), ('state', '=', 'accreditation')])
            for expenses_extra in expenses:
                expenses = {}
                expenses['expenses_type'] = expenses_extra.expenses_type
                expenses['amount'] = expenses_extra.amount
                expenses['note'] = expenses_extra.name
                rec.expenses_ids = [(0, 0, expenses)]
                # Todo

    def create_message(self, case):
        sms_template = self.env['benefit.sms.configuration'].sudo().search([('state', '=', case)])
        if sms_template:
            message = sms_template.case_text
            if '$اسم_المستفيد' in message:
                if self.name:
                    message = message.replace("$اسم_المستفيد", self.name)
                else:
                    raise ValidationError(_("عفواءً القالب المخصص يتوجب وجود اسم المستفيد"))
            if '$رقم_الهوية' in message:
                if self.id_number:
                    message = message.replace("$رقم_الهوية", self.id_number)
                else:
                    raise ValidationError(_("عفواءً القالب المخصص يتوجب وجود رقم الهوية"))
            if '$اسم_العائلة' in message:
                if self.institution_id:
                    message = message.replace("$اسم_العائلة", self.institution_id.name)
                else:
                    raise ValidationError(_("عفواءً القالب المخصص يتوجب وجود اسم العائلة"))
            return message

    def get_error_response(self, result):
        if result == "105":
            raise ValidationError(_("Sorry, there is not enough credit!"))
        if result == "102":
            raise ValidationError(_("Sorry, wrong username!"))
        if result == "103":
            raise ValidationError(_("Sorry, wrong password!"))
        if result == "106":
            raise ValidationError(_("Sorry, sender name is not available!"))
        if result == "1013":
            raise ValidationError(_("Sorry, no message has been posted!"))
        if result == "1011":
            raise ValidationError(_("Sorry, no message has been posted!"))

    @api.depends('name')
    def _compute_qr_code(self):
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=15,
            border=4,
        )
        name = self.name
        qr.add_data(name)
        qr.make(fit=True)
        img = qr.make_image()
        temp = BytesIO()
        img.save(temp, format="PNG")
        qr_image = base64.b64encode(temp.getvalue())
        self.qr_code = qr_image

    @api.onchange('bank_id')
    def _compute_prefix_iban(self):
        if self.bank_id:
            self.iban = self.bank_id.iban

    @api.onchange('weight', 'height')
    def _compute_obesity_rate(self):
        for rec in self:
            if rec.weight and rec.height:
                height = (rec.height / 100)
                rec.p_weight = (rec.weight / (height * height))

    def get_total_expenses(self):
        for ben in self:
            if ben.id:
                followers = ben.env['benefit.followers'].sudo().search([('benefit_id', '=', ben.id)])
                expenses = ben.env['expenses.line'].sudo().search([('benefit_id', '=', ben.id)])
                total_expenses = 0.0
                if ben.expenses_ids and ben.family_debits_ids:
                    total_expenses = sum(ben.expenses_ids.filtered(lambda e: e.state == 'accepted').mapped('amount')) + sum(ben.family_debits_ids.filtered(lambda e: e.state == 'accepted').mapped('monthly_installment'))
                elif ben.expenses_ids and not ben.family_debits_ids:
                    total_expenses = sum(ben.expenses_ids.filtered(lambda e: e.state == 'accepted').mapped('amount'))
                elif ben.family_debits_ids and not ben.expenses_ids:
                    total_expenses = sum(ben.family_debits_ids.filtered(lambda e: e.state == 'accepted').mapped('monthly_installment'))
                else:
                    total_expenses = 0.0
                for rec in ben:
                    if followers:
                        rec.followers_total = len(followers)
                    if expenses:
                        rec.expenses_total = len(expenses)
                    rec.total_expenses = total_expenses
            else:
                self.total_expenses = 0.0

    def get_total_income(self):
        validation_setting = self.env["family.validation.setting"].search([], limit=1)
        mini_income_for_mother = validation_setting.mini_income_for_mother

        for rec in self:
            rec.total_income = 0.0

            # Helper function to calculate income based on mother/replacement_mother status and salary_ids
            def calculate_income(income, status, salary_ids):
                total = 0.0
                accepted_salaries = sum(salary_ids.filtered(lambda e: e.state == 'accepted').mapped('salary_amount'))

                if status == 'non_benefit':
                    total = accepted_salaries
                elif status == 'benefit':
                    if not salary_ids:
                        total = income if income > mini_income_for_mother else 0.0
                    else:
                        total = accepted_salaries + (income if income > mini_income_for_mother else 0.0)
                return total
            if not rec.add_replacement_mother:
                # Calculate total income for mother
                rec.total_income = calculate_income(rec.mother_income, rec.mother_status, rec.salary_ids)
            if rec.add_replacement_mother:
                # Calculate total income for replacement mother if applicable
                rec.total_income += calculate_income(rec.replacement_mother_income, rec.replacement_mother_status,
                                                 rec.salary_ids)


    def get_mother_name(self):
        for rec in self:
            name = ''
            if all([rec.mother_name, rec.mother_second_name, rec.mother_third_name, rec.mother_family_name]):
                name = rec.mother_name + " " + rec.mother_second_name + " " + rec.mother_third_name + " " + rec.mother_family_name
            else:
                name = name
        return name

    def get_replacement_mother_name(self):
        for rec in self:
            name = ''
            if all([rec.replacement_mother_name, rec.replacement_mother_second_name, rec.replacement_mother_third_name, rec.replacement_mother_family_name]):
                name = rec.replacement_mother_name + " " + rec.replacement_mother_second_name + " " + rec.replacement_mother_third_name + " " + rec.replacement_mother_family_name
            else:
                name = name
        return name
    def add_mother_as_member(self):
        for rec in self:
            mother_name = rec.get_mother_name()
            val = {
                'name': mother_name,
                'mother_first_name': rec.mother_name,
                'mother_second_name': rec.mother_second_name,
                'mother_third_name': rec.mother_third_name,
                'mother_family_name': rec.mother_family_name,
                'member_id_number': rec.mother_id_number,
                'is_mother':True,
                'birth_date': rec.mother_birth_date,
                'gender': 'female',
                'relationn': self.env['relation.settings'].search([('relation_type','=','mother')]).id,
                'mother_marital_conf': rec.mother_marital_conf.id,
                'mother_location_conf': rec.mother_location_conf.id,
                'age': rec.mother_age,
                'is_work': rec.is_mother_work,
                'has_disabilities':rec.mother_has_disabilities,
                'member_income': rec.mother_income,
                'is_alhaju': rec.is_alhaju,
                'is_amra': rec.is_amra,
                'education_status': rec.education_status,
                'case_study': rec.case_study,
                'education_entity': rec.education_entity,
                'last_education_entity': rec.last_education_entity,
                'entities': rec.entities.id,
                'last_entities': rec.last_entities.id,
                'education_levels': rec.education_levels.id,
                'last_education_levels': rec.last_education_levels.id,
                'specialization_ids': rec.specialization_ids.id,
                'last_specialization_ids': rec.last_specialization_ids.id,
                'classroom': rec.classroom.id,
                'last_classroom': rec.last_classroom.id,
                'degree': rec.degree.id,
                'last_degree': rec.last_degree.id,
                'percentage': rec.percentage,
                'last_percentage': rec.last_percentage,
                'weak_study': rec.weak_study.ids,
                'member_status': rec.mother_status,
                'education_start_date':rec.education_start_date,
                'education_end_date':rec.education_end_date,
                'educational_certificate':rec.educational_certificate,
                'last_education_start_date': rec.last_education_start_date,
                'last_education_end_date': rec.last_education_end_date,
                'last_educational_certificate': rec.last_educational_certificate,
            }
        self.write({
            'member_ids': [(0, 0, val)]
        })
    def add_replacement_mother_as_member(self):
        for rec in self:
            mother_name = rec.get_replacement_mother_name()
            val = {
                'name': mother_name,
                'mother_first_name': rec.replacement_mother_name,
                'mother_second_name': rec.replacement_mother_second_name,
                'mother_third_name': rec.replacement_mother_third_name,
                'mother_family_name': rec.replacement_mother_family_name,
                'member_id_number': rec.replacement_mother_id_number,
                'is_mother':True,
                'birth_date': rec.replacement_mother_birth_date,
                'gender': 'female',
                'relationn': rec.replacement_mother_relation.id,
                'mother_marital_conf': rec.replacement_mother_marital_conf.id,
                'mother_location_conf': rec.replacement_mother_location_conf.id,
                'age': rec.replacement_mother_age,
                'is_work': rec.replacement_is_mother_work,
                'has_disabilities': rec.replacement_mother_has_disabilities,
                'member_income': rec.replacement_mother_income,
                'is_alhaju': rec.replacement_is_alhaju,
                'is_amra': rec.replacement_is_amra,
                'education_status': rec.replacement_education_status,
                'case_study': rec.replacement_case_study,
                'education_entity': rec.replacement_education_entity,
                'last_education_entity': rec.replacement_last_education_entity,
                'entities': rec.replacement_entities.id,
                'last_entities': rec.replacement_last_entities.id,
                'education_levels': rec.replacement_education_levels.id,
                'last_education_levels': rec.replacement_last_education_levels.id,
                'specialization_ids': rec.replacement_specialization_ids.id,
                'last_specialization_ids': rec.replacement_last_specialization_ids.id,
                'classroom': rec.replacement_classroom.id,
                'last_classroom': rec.replacement_last_classroom.id,
                'degree': rec.replacement_degree.id,
                'last_degree': rec.replacement_last_degree.id,
                'percentage': rec.replacement_percentage,
                'weak_study': rec.replacement_weak_study.ids,
                'member_status': rec.replacement_mother_status,
                'education_start_date': rec.replacement_education_start_date,
                'education_end_date': rec.replacement_education_end_date,
                'educational_certificate': rec.replacement_educational_certificate,
                'last_education_start_date': rec.replacement_last_education_start_date,
                'last_education_end_date': rec.replacement_last_education_end_date,
                'last_educational_certificate': rec.replacement_last_educational_certificate,
            }
        self.write({
            'member_ids': [(0, 0, val)]
        })

    def replace_mother_as_member(self, id):
        for rec in self:
            mother_name = rec.get_mother_name()
            val = {
                'name': mother_name,
                'mother_first_name': rec.mother_name,
                'mother_second_name': rec.mother_second_name,
                'mother_third_name': rec.mother_third_name,
                'mother_family_name': rec.mother_family_name,
                'member_id_number': rec.mother_id_number,
                'is_mother': True,
                'birth_date': rec.mother_birth_date,
                'gender': 'female',
                'relationn': self.env['relation.settings'].search([('relation_type','=','mother')]).id,
                'mother_marital_conf': rec.mother_marital_conf.id,
                'mother_location_conf': rec.mother_location_conf.id,
                'age': rec.mother_age,
                'is_work': rec.is_mother_work,
                'has_disabilities': rec.mother_has_disabilities,
                'member_income': rec.mother_income,
                'is_alhaju': rec.is_alhaju,
                'is_amra': rec.is_amra,
                'education_status': rec.education_status,
                'case_study': rec.case_study,
                'education_entity': rec.education_entity,
                'last_education_entity': rec.last_education_entity,
                'entities': rec.entities.id,
                'last_entities': rec.last_entities.id,
                'education_levels': rec.education_levels.id,
                'last_education_levels': rec.last_education_levels.id,
                'specialization_ids': rec.specialization_ids.id,
                'last_specialization_ids': rec.last_specialization_ids.id,
                'classroom': rec.classroom.id,
                'last_classroom': rec.last_classroom.id,
                'degree': rec.degree.id,
                'last_degree': rec.last_degree.id,
                'percentage': rec.percentage,
                'last_percentage': rec.last_percentage,
                'weak_study': rec.weak_study.ids,
                'member_status': rec.mother_status,
                'education_start_date': rec.education_start_date,
                'education_end_date': rec.education_end_date,
                'educational_certificate': rec.educational_certificate,
                'last_education_start_date': rec.last_education_start_date,
                'last_education_end_date': rec.last_education_end_date,
                'last_educational_certificate': rec.last_educational_certificate,
            }
            member = self.member_ids.browse(id)
            if member:
                member.write(val)
    def replace_replacement_mother_as_member(self, id):
        for rec in self:
            mother_name = rec.get_replacement_mother_name()
            val = {
                'name': mother_name,
                'mother_first_name': rec.replacement_mother_name,
                'mother_second_name': rec.replacement_mother_second_name,
                'mother_third_name': rec.replacement_mother_third_name,
                'mother_family_name': rec.replacement_mother_family_name,
                'member_id_number': rec.replacement_mother_id_number,
                'is_mother': True,
                'birth_date': rec.replacement_mother_birth_date,
                'gender': 'female',
                'relationn': rec.replacement_mother_relation.id,
                'mother_marital_conf': rec.replacement_mother_marital_conf.id,
                'mother_location_conf': rec.replacement_mother_location_conf.id,
                'age': rec.replacement_mother_age,
                'is_work': rec.replacement_is_mother_work,
                'has_disabilities': rec.replacement_mother_has_disabilities,
                'member_income': rec.replacement_mother_income,
                'is_alhaju': rec.replacement_is_alhaju,
                'is_amra': rec.replacement_is_amra,
                'education_status': rec.replacement_education_status,
                'case_study': rec.replacement_case_study,
                'education_entity': rec.replacement_education_entity,
                'last_education_entity': rec.replacement_last_education_entity,
                'entities': rec.replacement_entities.id,
                'last_entities': rec.replacement_last_entities.id,
                'education_levels': rec.replacement_education_levels.id,
                'last_education_levels': rec.replacement_last_education_levels.id,
                'specialization_ids': rec.replacement_specialization_ids.id,
                'last_specialization_ids': rec.replacement_last_specialization_ids.id,
                'classroom': rec.replacement_classroom.id,
                'last_classroom': rec.replacement_last_classroom.id,
                'degree': rec.replacement_degree.id,
                'last_degree': rec.replacement_last_degree.id,
                'percentage': rec.replacement_percentage,
                'last_percentage': rec.replacement_last_percentage,
                'weak_study': rec.replacement_weak_study.ids,
                'member_status': rec.replacement_mother_status,
                'education_start_date': rec.replacement_education_start_date,
                'education_end_date': rec.replacement_education_end_date,
                'educational_certificate': rec.replacement_educational_certificate,
                'last_education_start_date': rec.replacement_last_education_start_date,
                'last_education_end_date': rec.replacement_last_education_end_date,
                'last_educational_certificate': rec.replacement_last_educational_certificate,
            }
            member = self.member_ids.browse(id)
            if member:
                member.write(val)

    def get_members_count(self):
        for ben in self:
            if ben.id:
                ben.benefit_member_count = len(ben.member_ids.filtered(lambda x: x.member_status == 'benefit'))
            else:
                ben.benefit_member_count = 0.0

    def get_non_members_count(self):
        for ben in self:
            if ben.id:
                ben.non_member_count = len(ben.member_ids.filtered(lambda x: x.member_status == 'non_benefit'))
            else:
                ben.non_member_count = 0.0

    @api.depends('salary_ids', 'expenses_ids', 'family_debits_ids.monthly_installment','mother_income','member_ids','family_debits_ids.state','expenses_ids.state','salary_ids.state')
    def get_member_income(self):
        validation_setting = self.env["family.validation.setting"].search([], limit=1)
        max_income_for_mother = validation_setting.max_income_for_mother
        total = 0
        for ben in self:
            if ben.mother_income >= max_income_for_mother and ben.family_debits_ids:
                family_income = ben.total_income - ben.total_expenses
            elif ben.mother_income >= max_income_for_mother:
                family_income = ben.total_income - ben.total_expenses
            elif ben.family_debits_ids:
                family_income = ben.total_income - ben.total_expenses
            else:
                family_income = ben.total_income - ben.total_expenses
            if ben.benefit_member_count:
                if ben.benefit_member_count > 3:
                    ben.member_income = family_income / ben.benefit_member_count
                elif ben.benefit_member_count <= 3:
                    ben.member_income = family_income / 3
            else:
                ben.member_income = 0
    @api.depends("member_income")
    def get_benefit_category(self):
        for rec in self:
            if rec.member_income:
                result = self.env['benefit.category'].sudo().search(
                    [('mini_income_amount', '<=', rec.member_income), ('max_income_amount', '>=', rec.member_income)])
                rec.benefit_category_id = result.id
            else:
                rec.benefit_category_id = None

    def open_followers(self):
        context = {}
        context['default_benefit_id'] = self.id
        return {
            'name': _('Benefit Followers'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(self.env.ref(
                'odex_benefit.benefit_followers_tree').id, 'tree'),
                      (self.env.ref('odex_benefit.benefit_followers_form').id, 'form')],
            'res_model': 'benefit.followers',
            'type': 'ir.actions.act_window',
            'context': context,
            'domain': "[('benefit_id','=',%s)]" % (self.id),
            'target': 'current',
        }

    def open_expenses(self):
        context = {}
        context['default_benefit_id'] = self.id
        return {
            'name': _('Benefit Expenses'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(self.env.ref(
                'odex_benefit.benefit_expenses_tree').id, 'tree'),
                      (self.env.ref('odex_benefit.expenses_line_form').id, 'form')],
            'res_model': 'benefit.expenses',
            'type': 'ir.actions.act_window',
            'context': context,
            'domain': "[('benefit_id','=',%s)]" % (self.id),
            'target': 'current',
        }

    @api.depends('birth_date')
    def _compute_get_father_age(self):
        for rec in self:
            if rec.birth_date:
                today = date.today()
                day = datetime.strptime(str(rec.birth_date), DEFAULT_SERVER_DATE_FORMAT)
                age = rd(today, day)
                rec.father_age = age.years
            rec.father_age = 0

    @api.depends('mother_birth_date')
    def _compute_get_mother_age(self):
        for rec in self:
            if rec.mother_birth_date:
                today = date.today()
                day = datetime.strptime(str(rec.mother_birth_date), DEFAULT_SERVER_DATE_FORMAT)
                age = rd(today, day)
                rec.mother_age = age.years
            else:
                rec.mother_age = 0

    @api.depends('replacement_mother_birth_date')
    def _compute_get_replacement_mother_age(self):
        for rec in self:
            if rec.replacement_mother_birth_date:
                today = date.today()
                day = datetime.strptime(str(rec.replacement_mother_birth_date), DEFAULT_SERVER_DATE_FORMAT)
                age = rd(today, day)
                rec.replacement_mother_age = age.years
            else:
                rec.replacement_mother_age = 0

    def action_finish_edit(self):
        for rec in self:
            group_e = self.env.ref('odex_benefit.group_benefit_edit', False)
            group_e.write({'users': [(3, self.user_id.id)]})
            rec.state = rec.old_stage

    # @api.multi
    def edit_password(self):
        if self.user_id:
            self.user_id.sudo().action_reset_password()

    def create_family_partner(self):
        bank_val = {
            'acc_number':self.acc_number,
            'acc_holder_name':self.acc_holder_name,
            'bank_id':self.bank_id.id,
        }
        partner = self.env['res.partner'].create({
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            'account_type':'family',
            'code':self.code,
            'bank_ids': [(0,0,bank_val)]
        })
        self.partner_id = partner.id
    # def create_member_partner(self):
    #     # bank_val = {
    #     #     'acc_number':self.acc_number,
    #     #     'partner_id':self.account_holder,
    #     #     'bank_name':self.bank_name,
    #     # }
    #     partner = self.env['res.partner'].create({
    #         'name': self.name,
    #         'email': self.email,
    #         'phone': self.phone,
    #         'account_type':'member',
    #         'code':self.code,
    #         # 'bank_ids': [(0,0,bank_val)]
    #     })
    #     self.partner_id = partner.id

    def create_user(self):
        bank_val = {
            'acc_number':self.acc_number,
            'acc_holder_name':self.acc_holder_name,
            'bank_id':self.bank_id.id,
        }
        for follower in self['message_follower_ids']:
            follower.sudo().unlink()
        if not self.partner_id:
            partner = self.create_family_partner()
        self.partner_id.write({
            'name': self.name,
            'email': self.sms_phone,
            'phone': self.phone,
            'account_type': 'family',
            'code': self.code,
            'bank_ids': [(0,0,bank_val)]
        })
        user = self.env['res.users'].sudo().with_context(no_reset_password=True).create({
            'name': self.name,
            'login': self.email,
            'partner_id': self.partner_id.id,
            'active': True,

        })
        self.user_id = user.id
        if self.password:
            user.sudo().write({'password': self.password, })

        user.sudo().write({
            'groups_id': [(3, self.env.ref('base.group_user', False).id)],
        })
        # user.sudo().write({
        #     'groups_id': [(4, self.env.ref('odex_benefit.group_benefit_user', False).id)],
        # })
        user.sudo().write({
            'groups_id': [(4, self.env.ref('base.group_portal', False).id)],
        })

    # @api.multi
    def send_approval_benefit_email(self):
        """Send approval email when benefit registration is accepted"""
        template = self.env.ref('odex_benefit.approval_benefit_email', False)
        if not template:
            return
        template.with_context(lang=self.env.user.lang).send_mail(self.id, force_send=True, raise_exception=False)

    # @api.multi
    def _send_notification(self, partner_ids, state):
        """Send notification when entity state changes"""
        subject = _('Beneficial')
        state_label = dict(self.fields_get(allfields=['state'])['state']['selection'])[state]
        body = ' '.join((_(u'The Beneficiaries '), self.name, _(u' State changed to '), state_label, u'.')).encode(
            'utf-8')
        partner_list_ids = []
        for id in partner_ids:
            partner_list_ids.append(id.id)
        message_vals = {
            'subject': subject,
            'body': body,
            'partner_ids': partner_list_ids,
            # 'model': self._name,
            # 'res_id': self.id,
        }
        test = self.sudo().message_post(message_type="notification", subtype_xmlid="mt_comment",
                                        **message_vals)

    def send_black_list_email(self):
        """Send black list email when entity black list"""
        template = self.env.ref('odex_benefit.black_list_entity_email', False)
        if not template:
            return
        template.with_context(lang=self.env.user.lang).send_mail(self.id, force_send=True, raise_exception=False)

    # @api.multi
    def send_remove_from_black_list_email(self):
        """Send black list email when entity black list"""
        template = self.env.ref('odex_benefit.black_list_remove_benefit_email', False)
        if not template:
            return
        template.with_context(lang=self.env.user.lang).send_mail(self.id, force_send=True, raise_exception=False)

    # # Validation Opertaion
    # @api.onchange('phone', 'phone2','sms_phone')
    # def _onchange_mobile_validation(self):
    #     if self.phone:
    #         if self.phone.startswith('+966'):
    #             phone = self.phone[4:]
    #             self.phone = phone
    #         if re.match(SAUDI_MOBILE_PATTERN, self.phone) == None:
    #             raise ValidationError(
    #                 _('Enter a valid Saudi mobile number'))
    #     if self.phone2:
    #         if self.phone2.startswith('+966'):
    #             phone2 = self.phone2[4:]
    #             self.phone2 = phone2
    #         if re.match(SAUDI_MOBILE_PATTERN, self.phone2) == None:
    #             raise ValidationError(
    #                 _('Enter a valid Saudi mobile number'))
    #     if self.sms_phone:
    #         if self.sms_phone.startswith('+966'):
    #             sms_phone = self.sms_phone[4:]
    #             self.sms_phone = sms_phone
    #         if re.match(SAUDI_MOBILE_PATTERN, self.sms_phone) == None:
    #             raise ValidationError(
    #                 _('Enter a valid Saudi mobile number'))

    @api.onchange('phone', 'phone2','sms_phone')
    def _onchange_phone_numbers(self):
        phone_numbers = {
            'الهاتف': self.phone,
            'رقم الجوال الثاني': self.phone2,
            'رقم الجوال للتواصل': self.sms_phone,
        }

        # Check each ID number for 10-digit format and uniqueness within the parent model
        unique_ids = set()
        for label, phone_number in phone_numbers.items():
            if phone_number:
                if re.match(SAUDI_MOBILE_PATTERN,phone_number) == None:
                    raise ValidationError(
                        _('Enter a valid Saudi mobile number'))
                if phone_number in unique_ids:
                    raise ValidationError(_("%s must be unique within the same record.") % label)
                unique_ids.add(phone_number)

        # Check for uniqueness against `member_phone` in child records and across database records
        for member in self.member_ids:
            if member.member_phone and member.member_phone in unique_ids:
                raise ValidationError(
                    _("The Phone Number %s in the Family Members list must be unique across the record.") % member.member_phone)
        # Check for duplicate IDs across records in the database
        for phone_number in unique_ids:
            duplicate_record_family = self.env['grant.benefit'].search([
                '|', '|', ('phone', '=', phone_number), ('phone2', '=', phone_number),
                ('sms_phone', '=', phone_number), ('id', '!=', self._origin.id)
            ], limit=1)
            duplicate_record_member = self.env['family.member'].search([('member_phone', '=', phone_number)], limit=1)
            if duplicate_record_family:
                raise ValidationError(
                    _("The phone number {} already exists in family with code {}.").format(
                        phone_number, duplicate_record_family.code))
            if duplicate_record_member:
                raise ValidationError(
                    _("The phone {} already exists in family with code {}.").format(
                        phone_number, duplicate_record_member.benefit_id.code))

    @api.onchange('email')
    def onchange_email(self):
        if self.email:
            for rec in self:
                exist = self.search([('email', '=', rec.email)])
                if exist:
                    raise ValidationError(
                        _('The Email Already Exist!'))

    @api.onchange('sms_phone')
    def onchange_sms_phone(self):
        if self.sms_phone:
            for rec in self:
                exist = self.search([('sms_phone', '=', rec.sms_phone)])
                if exist:
                    raise ValidationError(
                        _('The SMS phone Already Exist!'))

    @api.onchange('acc_number')
    def onchange_acc_number(self):
        if self.acc_number:
            # Check if the value is numeric before anything else
            if not self.acc_number.isdigit():
                raise ValidationError(_("The account number should contain only digits."))

            # Check if the account number contains exactly 22 digits
            if len(self.acc_number) != 22:
                raise ValidationError(_("The IBAN number must contain exactly 22 digits."))

            # Check if the account number already exists in the partner bank or benefit
            partner_exist = self.env['res.partner.bank'].search([('acc_number', '=', self.acc_number)], limit=1)
            benefit_exist = self.search([('acc_number', '=', self.acc_number)], limit=1)

            if partner_exist or benefit_exist:
                raise ValidationError(_("The account number already exists!"))

    @api.onchange('mother_marital_conf', 'mother_location_conf', 'mother_income')
    def _onchange_mother_info(self):
        res = {}
        for rec in self:
            if rec.mother_status == 'non_benefit':
                res['warning'] = {'title': _('ValidationError'),
                                  'message': _('Not Benefit')}
                return res

    @api.onchange('replacement_mother_marital_conf', 'replacement_mother_location_conf', 'replacement_mother_income')
    def _onchange_replacement_mother_info(self):
        res = {}
        for rec in self:
            if rec.replacement_mother_status == 'non_benefit':
                res['warning'] = {'title': _('ValidationError'),
                                  'message': _('Not Benefit')}
                return res

    def create_scheduled_visit(self):
        records = self.env["grant.benefit"].search([('state', '=', 'second_approve')])
        for rec in records:
            self.env['visit.location'].create({
                'benefit_id': rec.id,
                'visit_date': date.today(),
                'visit_types': 2,
                'contact_type': 'email',
                'selector': 'researcher',
                'researcher_id': rec.researcher_id.id,
                # 'researcher_team': rec.researcher_team.id,
                'state': 'draft'
            })

    def create_manual_visit(self):
        self.env['visit.location'].create({
            'benefit_id': self.id,
            'visit_date': date.today(),
            'visit_types': 2,
            'contact_type': 'email',
            'selector': 'researcher',
            'researcher_id': self.researcher_id.id,
            # 'researcher_team': rec.researcher_team.id,
            'state': 'draft'
        })
    def change_attachment_status(self):
        obj = self.env["grant.benefit"].search([])
        for attach in obj.attachment_ids:
            attach.get_status()

    # Notifications
    def send_expiry_date_notification(self):
        self.change_attachment_status()
        obj = self.env["grant.benefit"].search([])
        for rec in obj:
            for attach in rec.attachment_ids:
                if attach.attach_status == 'expired':
                    template = self.env.ref('odex_benefit.attachment_expiration_family_email_template', False)
                    if not template:
                        return
                    template.with_context(lang=self.env.user.lang).send_mail(rec.id, force_send=True,
                                                                             raise_exception=False)
    #Update data automatically daily
    def update_data_automatically(self):
        obj = self.env["grant.benefit"].search([])
        for member in obj.member_ids:
            # member._compute_get_age_date()
            member.check_member_status()
        self.action_auto_suspend()


class BenefitFollowers(models.Model):
    _name = 'benefit.followers'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    benefit_id = fields.Many2one('grant.benefit', )
    name = fields.Many2one('grant.benefit', domain="[('is_responsible','=',False)]")
    follower_type = fields.Selection(
        [('benefit', 'benefit'), ('orphan', 'orphan'), ('widow', 'widow'), ('poor', 'poor'), ('other', 'other'),
         ], string='Benefit Type', tracking=True, related="name.benefit_type", )
    birth_date = fields.Date(related="name.birth_date", string="Birth Date")
    age = fields.Integer(string="Age", compute='_compute_get_age_date', store=True)
    gender = fields.Selection(selection=[('male', 'Male'), ('female', 'Female')], string="Gender",
                              related="name.gender", )
    is_live_with_family = fields.Boolean('Is Live With Family')

    @api.depends('birth_date')
    def _compute_get_age_date(self):
        for rec in self:
            if rec.birth_date:
                today = date.today()
                day = datetime.strptime(rec.birth_date, DEFAULT_SERVER_DATE_FORMAT)
                age = rd(today, day)
                rec.age = age.years


class WidowFamily(models.Model):
    _name = 'widow.family'

    benefit_id = fields.Many2one('grant.benefit')
    widow_name = fields.Many2one('grant.benefit', domain="[('benefit_type','=','widow')]", string='Widow Name')
    widows_husband = fields.Char('Widows Husband', related="widow_name.husband_name")
    widows_husband_id = fields.Char('Widows Husband ID', related="widow_name.husband_id")
    date_death_husband = fields.Date(related="widow_name.date_death_husband")


class divorceeFamily(models.Model):
    _name = 'divorcee.family'

    benefit_id = fields.Many2one('grant.benefit')
    divorcee_name = fields.Many2one('grant.benefit', 'divorcee Name')
    divorcee_husband = fields.Char('Widows Husband', related="divorcee_name.husband_name")
    divorcee_husband_id = fields.Char('Widows Husband ID', related="divorcee_name.husband_id")
    date_divorcee = fields.Date(related="divorcee_name.date_divorcee")


class ExternalBenefit(models.Model):
    _name = 'external.benefits'
    _inherits = {'res.partner': 'partner_id'}
    _inherit = ['mail.thread', 'mail.activity.mixin']

    location = fields.Char(string='location')
    benefit_nationality = fields.Many2one('res.country', 'Benefit Nationality')
    block = fields.Char('Benefit Block')
    work = fields.Char()
    partner_id = fields.Many2one('res.partner', string='partner', required=True, ondelete="cascade")

    @api.onchange('first_name', 'second_name', 'middle_name', 'family_name')
    def get_benefit_name(self):
        for rec in self:
            if rec.first_name and rec.second_name and rec.middle_name and rec.family_name:
                rec.name = rec.first_name + " " + rec.second_name + " " + rec.middle_name + " " + rec.family_name

    def create_partner(self):
        partner = self.env['res.partner'].create({
            'name': self.name,
            'email': self.email,
            'phone': self.phone,
            # 'city': self.city_id.name if self.city_id else False,
            # 'country_id': self.country_id.id,
        })
        self.partner_id = partner.id


# neighborhood representative
class Representative(models.Model):
    _name = 'benefits.representative'
    _inherits = {'res.partner': 'partner_id'}
    _inherit = ['mail.thread', 'mail.activity.mixin']

    location = fields.Char(string='location')
    block = fields.Char('Benefit Block')
    work = fields.Char()
    partner_id = fields.Many2one('res.partner', string='partner', required=True, ondelete="cascade")

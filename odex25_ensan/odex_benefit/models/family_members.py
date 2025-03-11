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
SAUDI_MOBILE_PATTERN = "(^(05|5)(5|0|3|6|4|9|1|8|7)([0-9]{7})$)"
import re

_logger = logging.getLogger(__name__)


class FamilyMemberProfile(models.Model):
    _name = 'family.member'
    _description = "Member - Profiles"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    # _inherits = {'res.partner': 'partner_id'}
    _order = 'age desc'

    def _default_benefit(self):
        return self._context.get('active_id')

    member_first_name = fields.Char(string="Member First Name")
    member_second_name = fields.Char(string="Member Second Name",related="benefit_id.father_name")
    member_third_name = fields.Char(string="Member Third Name",related="benefit_id.father_second_name")
    member_family_name = fields.Char(string="Member Family Name",related="benefit_id.father_family_name")
    mother_first_name = fields.Char(string="Mother First Name")
    mother_second_name = fields.Char(string="Mother Second Name")
    mother_third_name = fields.Char(string="Mother Third Name")
    mother_family_name = fields.Char(string="MotherFamily Name")
    name = fields.Char(string="Name", compute='get_partner_name', store=True,readonly = False)
    member_id_number = fields.Char(string="Member Id Number")
    benefit_id = fields.Many2one("grant.benefit",string="Responsable",default=_default_benefit)
    gender = fields.Selection(selection=[('male', 'Male'), ('female', 'Female')], string="Gender")
    member_phone = fields.Char(string="Member Phone")
    member_location = fields.Selection(selection=[('with_family', 'With Family'), ('with_relative', 'with a relative'),
                                                  ('study_inside_saudi_arabia', 'Study Inside Saudi Arabia'),('study_outside_saudi_arabia', 'Study Outside Saudi Arabia'),
                                                  ('rehabilitation_center_for_the_disabled', 'Rehabilitation center for the disabled'),('house_of_social_observations', 'House of Social Observations'),
                                                  ('girls_home','Girls Home'),('university_housing','University Housing'),('with_husband','With_husband'),('work_inside_saudi_arabia','Work Inside Saudi Arabia')], string="Member Location")
    member_location_conf = fields.Many2one('location.settings',string='Member Location',domain="[('location_type','=','member')]")
    # member_location = fields.Many2one('member.location', string="Member Location")
    birth_date = fields.Date(string="Birth Date")
    age = fields.Integer(string="Age", compute='_compute_get_age_date',store=True)
    is_work = fields.Boolean('Is Work?')
    is_dead = fields.Boolean('Is Dead?')
    member_income = fields.Float('Member Income')
    is_married = fields.Boolean('Is Married?')
    relationn = fields.Many2one('relation.settings',domain="['|',('relation_type','=','son'),('relation_type','=','daughter')]",string="Relation")
    relation = fields.Selection(
        [('son', _('Son')), ('daughter', _('Daughter'))])
    mother_marital = fields.Selection(
        [('married', _('Married')), ('widower', _('Widower')), ('divorced', _('Divorced')),
         ('divorced_from_another_man', _('Divorced From Another Man')), ('prisoner', _('Prisoner')), ('dead', _('Dead')), ('hanging', _('Hanging'))],
        _('Marital Status'))
    mother_marital_conf = fields.Many2one('marital.status',string='Mother Marital')
    mother_location = fields.Selection(
        [('with_husband_and_children', _('With Husband And Children')), ('with_children', _('With Children')),
         ('not_live_with_children', _('Not live with children'))], string='Mother Location')
    mother_location_conf = fields.Many2one('location.settings',string='Mother Location',domain="[('location_type','=','mother_location')]")
    need_transportation = fields.Boolean('Need Transportation?')
    attachment_ids = fields.One2many("ir.attachment",'member_id',domain=[('hobbies_id', '=', False),('diseases_id', '=', False),('disabilities_id', '=', False)])
    hobbies_attachment_ids = fields.One2many('ir.attachment', 'member_id', string='Hobbies Attachments',domain=[('hobbies_id', '!=', False)])
    diseases_attachment_ids = fields.One2many('ir.attachment', 'member_id', string='Diseases Attachments',domain=[('diseases_id', '!=', False)])
    disabilities_attachment_ids = fields.One2many('ir.attachment','member_id', string='Disabilities Attachments',domain=[('disabilities_id', '!=', False)])
    hobbies_ids = fields.One2many("member.hobbies",'member_id')
    diseases_ids = fields.One2many("member.diseases",'member_id')
    disabilities_ids = fields.One2many("member.disabilities",'member_id')
    is_scientific_specialty = fields.Boolean('Is Scientific Specialty?',related="specialization_ids.is_scientific_specialty")
    is_medical_specialty = fields.Boolean('Is Medical Specialty?',related="specialization_ids.is_medical_specialty")
    has_disabilities = fields.Boolean('Has Disabilities?')
    minor_siblings = fields.Boolean('minor siblings?')
    is_alhaju = fields.Boolean(string='Member Hajj')
    is_amra = fields.Boolean(string='Member Umra')
    # Education_data
    education_status = fields.Selection(string='Education Status',selection=[('educated', 'educated'), ('illiterate', 'illiterate'),('under_study_age', 'Under Study Age')])
    case_study = fields.Selection(string='Case Study',
                                  selection=[('continuous', 'continuous'), ('intermittent', 'intermittent'),
                                             ('graduate', 'Graduate')])
    illiterate_reason = fields.Char(string='Illiterate Reason')
    intermittent_reason = fields.Many2one('education.illiterate.reason',string='Intermittent Reason')
    educational_certificate = fields.Binary(attachment=True,string='Educational Certificate')
    education_entity = fields.Selection(string='Education Entity', selection=[('governmental', 'Governmental'),
                                                                              ('special', 'Special')])
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
    last_educational_certificate = fields.Binary(attachment=True,string='Last Educational Certificate')
    degree = fields.Many2one('education.result', string='Degree')
    last_degree = fields.Many2one('education.result', string='Last Degree')
    percentage = fields.Float(string="Percentage%")
    last_percentage = fields.Float(string="Last Percentage%")
    education_start_date = fields.Date(string='Education Start Date')
    education_end_date = fields.Date(string='Education End Date')
    end_date = fields.Date('End Date')
    specialization_ids = fields.Many2one('specialization.specialization', string='specialization')
    last_specialization_ids = fields.Many2one('specialization.specialization', string='Last Specialization')
    last_education_start_date = fields.Date(string='Last Education Start Date')
    last_education_end_date = fields.Date(string='Last Education End Date')
    weak_study = fields.Many2many('study.material', string='Weak Study')
    is_want_education = fields.Boolean(string='is Want Education', required=False)
    is_quran_memorize = fields.Boolean('memorize the quran ?')
    partner_id = fields.Many2one('res.partner')
    # Replacement Mother
    add_replacement_mother = fields.Boolean('Add Replacement Mother?')
    # replacement_mother_name = fields.Char(string="Replacement Mother Name", tracking=True)
    # replacement_mother_second_name = fields.Char(string="Replacement Mother Second Name", tracking=True)
    # replacement_mother_third_name = fields.Char(string="Replacement Mother Third Name", tracking=True)
    # replacement_mother_family_name = fields.Char(string="Replacement Mother Family Name", tracking=True)
    # replacement_mother_country_id = fields.Many2one('res.country', 'Replacement Mother Nationality', tracking=True)
    # replacement_mother_id_number = fields.Char(string="Replacement Mother Id Number", tracking=True)
    # replacement_mother_marital_conf = fields.Many2one('marital.status', string='Replacement Mother Marital')
    # replacement_mother_location = fields.Selection(
    #     [('with_husband_and_children', _('With Husband And Children')), ('with_children', _('With Children')),
    #      ('not_live_with_children', _('Not live with children'))], string='Replacement Mother Location')
    # replacement_is_mother_work = fields.Boolean('Is Replacement Mother Work?')
    # replacement_mother_income = fields.Float("Replacement Mother Income")
    # replacement_mother_birth_date = fields.Date(string="Replacement Mother Birth Date")
    # replacement_mother_age = fields.Integer(string="Replacement Mother Age",
    #                                         compute='_compute_get_replacement_mother_age')
    # replacement_mother_city_id = fields.Many2one('res.country.city', string='City')
    # replacement_mother_dead_reason = fields.Char(string='Dead Reason', required=False)
    # replacement_mother_dead_date = fields.Date(string="Certificate Date")
    # replacement_mother_dead_city_id = fields.Many2one('res.country.city', string='Dead City')
    # replacement_mother_status = fields.Selection(selection=[
    #     ('benefit', 'Benefit'),
    #     ('non_benefit', 'Non Benefit'),
    # ], string='Replacement Mother Status', compute="check_replacement_mother_status", store=True, default=False)
    # replacement_is_alhaju = fields.Boolean(string='IS Hajj')
    # replacement_is_amra = fields.Boolean(string='IS Umra')
    # # Education_data for replacement mother
    # replacement_education_status = fields.Selection(string='Education Status',
    #                                                 selection=[('educated', 'educated'), ('illiterate', 'illiterate')])
    # replacement_case_study = fields.Selection(string='Mother Case Study',
    #                                           selection=[('continuous', 'continuous'), ('intermittent', 'intermittent'),
    #                                                      ('graduate', 'Graduate')])
    # replacement_illiterate_reason = fields.Char(string='Illiterate Reason')
    # replacement_intermittent_reason = fields.Many2one('education.illiterate.reason',
    #                                                   string='Intermittent Reason')
    # replacement_education_entity = fields.Selection(string='Education Entity',
    #                                                 selection=[('governmental', 'Governmental'),
    #                                                            ('special', 'Special')])
    # replacement_entities = fields.Many2one("education.entities", string='Entity')
    # replacement_specialization_ids = fields.Many2one('specialization.specialization', string='specialization')
    # replacement_classroom = fields.Many2one('education.classroom', string='Classroom')
    # replacement_degree = fields.Many2one('education.result', string='Degree')
    # replacement_percentage = fields.Float(string="Percentage%")
    # replacement_education_start_date = fields.Date(string='Education Start Date')
    # replacement_education_end_date = fields.Date(string='Education End Date')
    #
    # replacement_last_education_entity = fields.Selection(string='Last Education Entity',
    #                                                      selection=[('governmental', 'Governmental'),
    #                                                                 ('special', 'Special')])
    # replacement_last_entities = fields.Many2one("education.entities", string='Last Entity')
    # replacement_education_levels = fields.Many2one("education.level", string='Education Levels')
    # replacement_last_education_levels = fields.Many2one("education.level", string='Last Education Levels')
    # replacement_last_specialization_ids = fields.Many2one('specialization.specialization', string='Last Specialization')
    #
    # replacement_last_classroom = fields.Many2one('education.classroom', string='Last Classroom')
    # replacement_last_degree = fields.Many2one('education.result', string='Last Degree')
    # replacement_last_percentage = fields.Float(string="Last Percentage%")
    # replacement_last_education_start_date = fields.Date(string='Last Education Start Date')
    # replacement_last_education_end_date = fields.Date(string='Last Education End Date')
    # replacement_last_educational_certificate = fields.Binary(attachment=True, string='Last Educational Certificate')
    # replacement_weak_study = fields.Many2many('study.material', string='Weak Study')

    # state = fields.Selection([
    #     ('draft', 'Draft'),
    #     ('complete_info', 'Complete Information'),
    #     ('waiting_approve', 'Waiting Approved'),
    #     ('woman_manager', 'Woman Manager'),
    #     ('researcher_team', 'Researcher Team'),
    #     ('edit_info', 'Edit Information'),
    #     ('first_refusal', 'First Refusal'),
    #     ('first_approve', 'Approved'),
    #     ('refused', 'Refused'),
    #     ('not_leaving', 'Not Leaving'),
    #     ('black_list', 'Black List'),
    # ], string='state', default="draft", tracking=True,related="benefit_id.state")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('complete_info', 'Complete Information'),
        ('waiting_approve', 'Waiting Approved'),
        ('woman_manager', 'Woman Manager'),
        ('researcher_team', 'Researcher Team'),
        ('edit_info', 'Edit Information'),
        ('first_refusal', 'First Refusal'),
        ('first_approve', 'First Approved'),
        ('second_approve', 'Second Approved'),
        ('refused', 'Refused'),
        ('temporarily_suspended', 'Temporarily suspended'),
        ('suspended', 'suspended'),
        ('suspended_first_approve', 'Suspended First Approved'),
        ('suspended_second_approve', 'Suspended Second Approved'),
        ('temporarily_exception', 'Temporarily Exception'),
        ('exception_first_approve', 'Exception First Approve'),
        ('exception_second_approve', 'Exception Second Approve'),
        ('not_leaving', 'Not Leaving'),
        ('black_list', 'Black List'),
    ], string='state', tracking=True,compute='_get_state',store = True)
    state_a = fields.Selection([
        ('draft', 'Draft'),
        ('complete_info', 'Complete Information'),
        ('waiting_approve', 'Waiting Approved'),
        ('woman_manager', 'Woman Manager'),
        ('researcher_team', 'Researcher Team'),
        ('edit_info', 'Edit Information'),
        ('first_refusal', 'First Refusal'),
        ('first_approve', 'First Approved'),
        ('second_approve', 'Second Approved'),
        ('refused', 'Refused'),
        ('temporarily_suspended', 'Temporarily suspended'),
        ('suspended', 'suspended'),
        ('suspended_first_approve', 'Suspended First Approved'),
        ('suspended_second_approve', 'Suspended Second Approved'),
        ('temporarily_exception', 'Temporarily Exception'),
        ('exception_first_approve', 'Exception First Approve'),
        ('exception_second_approve', 'Exception Second Approve'),
        ('not_leaving', 'Not Leaving'),
        ('black_list', 'Black List'),
    ], string='stateA', default="draft", tracking=True)
    member_status = fields.Selection(selection=[
        ('benefit', 'Benefit'),
        ('non_benefit', 'Non Benefit'),
    ], string='Benefit Status', compute="check_member_status",default = False,store=True)
    suspend_reason = fields.Many2one('suspend.reason', string='Suspend Reason')
    reason = fields.Text(string='Reason')
    suspend_description = fields.Text(string='Suspend Description')
    suspend_attachment = fields.Binary(string='Suspend Attachment', attachment=True)
    suspend_type = fields.Selection(
        selection=[('temporarily_suspend', 'Temporarily Suspended'), ('suspend', 'Suspend')], string="Suspend Type")
    suspend_method = fields.Selection(selection=[('manual', 'Manual'), ('auto', 'Auto')], string="Suspend Method",default='auto')
    is_member_workflow = fields.Boolean('Is Member Workflow?')
    sponsor_id = fields.Many2one('res.partner', string='Sponsor',domain="[('account_type','=','sponsor')]")
    required_attach = fields.Selection(selection=[('true', 'True'), ('false', 'False')], compute='get_required_attach',store=True,string='Member Required Attach')
    # Exception fields
    exception_reason = fields.Many2one('exception.reason', string='Exception Reason')
    exception_description = fields.Text(string='Exception Description')
    exception_type = fields.Selection(
        selection=[('temporarily_exception', 'Temporarily Exception'), ('permanent_exception', 'Permanent Exception')],
        string="Exception Type")
    exception_attachment = fields.Binary(string='Exception Attachment', attachment=True)
    exception_start_date = fields.Datetime(string='Exception Start Date')
    exception_end_date = fields.Datetime(string='Exception End Date')
    is_excluded_suspension = fields.Boolean('Excluded from suspension?')
    is_mother = fields.Boolean('Is Mother?')

    expenses_ids = fields.One2many(
        "expenses.line", "member_id", string="Expenses"
    )

    salary_ids = fields.One2many(
        "salary.line", "member_id", string="Salaries"
    )

    

    def unlink(self):
        for order in self:
            if order.state not in ['draft']:
                raise UserError(_('You cannot delete this record'))
        return super(FamilyMemberProfile, self).unlink()

    @api.depends('is_member_workflow', 'benefit_id.state','state_a')
    def _get_state(self):
        for rec in self:
            if not rec.is_member_workflow:
                rec.state = rec.benefit_id.state
            else:
                rec.state = rec.state_a

    @api.depends('member_first_name', 'member_second_name', 'member_third_name', 'member_family_name')
    def get_partner_name(self):
        for rec in self:
            rec.name = ''
            if all([rec.member_second_name, rec.member_first_name, rec.member_third_name, rec.member_family_name]):
                rec.name = rec.member_first_name + " " + rec.member_second_name + " " + rec.member_third_name + " " + rec.member_family_name
            elif all([rec.mother_second_name, rec.mother_first_name, rec.mother_third_name, rec.mother_family_name]):
                rec.name = rec.mother_first_name + " " + rec.mother_second_name + " " + rec.mother_third_name + " " + rec.mother_family_name
            else:
                rec.name = ''

    @api.model
    def default_get(self, fields):
        res = super(FamilyMemberProfile, self).default_get(fields)

        # Get default attachments
        default_attachment = self.env["attachments.settings"].search([('is_default', '=', True)])

        # Prepare the list of default attachments for the one2many field
        default_attachments_data = []
        for attach in default_attachment:
            if attach.attach_type == 'member_attach':
                if not attach.name:  # Ensure name is set
                    raise ValidationError('The attachment name is missing.')
                default_attachments_data.append((0, 0, {
                    'name': attach.name,
                    'attach_id':attach.id,
                    'is_required': attach.is_required,
                    'is_default': attach.is_default,
                }))

        # Add the default attachments to the res dictionary for attachment_ids
        if 'attachment_ids' in fields:
            res['attachment_ids'] = default_attachments_data

        return res

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

    # def create_member_partner(self):
    #     self.partner_id.write({
    #         'email': self.email,
    #         'phone': self.phone,
    #         'account_type': 'benefit',
    #         'code': self.benefit_id.code,
    #     })
    @api.depends('relationn','birth_date', 'is_scientific_specialty', 'is_medical_specialty', 'has_disabilities', 'is_married',
                  'minor_siblings','member_income','is_married','member_location_conf','education_status','case_study','state','is_dead')
    def check_member_status(self):
        for rec in self:
            if rec.state == 'second_approve' and rec.is_excluded_suspension:
                rec.member_status = 'benefit'
                continue
            if rec.birth_date:
                validation_setting = self.env["family.validation.setting"].search([], limit=1)
                female_benefit_age = validation_setting.female_benefit_age
                male_benefit_age = validation_setting.male_benefit_age
                exceptional_age_scientific_specialty = validation_setting.exceptional_age_scientific_specialty
                exceptional_age_medical_specialty = validation_setting.exceptional_age_medical_specialty
                exceptional_age_has_disabilities = validation_setting.exceptional_age_has_disabilities
                minor_siblings_age = validation_setting.minor_siblings_age
                max_income_for_benefit = validation_setting.max_income_for_benefit
                rec.member_status = 'benefit'  # Default to benefit
                if rec.relationn.relation_type == 'mother':
                    rec.member_status = rec.benefit_id.mother_status
                if rec.relationn.relation_type == 'replacement_mother':
                    rec.member_status = rec.benefit_id.replacement_mother_status
                    if rec.state == 'suspended_second_approve':
                        rec.member_status = 'non_benefit'
                    # continue  # Skip further checks for mothers
                # Gender-specific checks
                if rec.relationn.relation_type == 'son':
                    if rec.age > male_benefit_age:
                        if rec.has_disabilities and rec.age > exceptional_age_has_disabilities:
                            rec.member_status = 'non_benefit'
                        elif rec.is_scientific_specialty and rec.age > exceptional_age_scientific_specialty and not rec.has_disabilities and not rec.minor_siblings :
                            rec.member_status = 'non_benefit'
                        elif rec.is_medical_specialty and rec.age > exceptional_age_medical_specialty and not rec.has_disabilities and not rec.minor_siblings:
                            rec.member_status = 'non_benefit'
                        elif not any([rec.is_scientific_specialty, rec.is_medical_specialty, rec.has_disabilities]):
                            rec.member_status = 'non_benefit'
                    if rec.is_work:
                        if rec.member_income > max_income_for_benefit:
                            rec.member_status = 'non_benefit'
                        if not rec.is_married and rec.education_status in ['illiterate']:
                            rec.member_status = 'non_benefit'
                        if not rec.is_married and rec.education_status in ['educated'] and rec.case_study in [
                            'graduate', 'intermittent']:
                            rec.member_status = 'non_benefit'
                    if not rec.member_location_conf.is_benefit:
                        rec.member_status = 'non_benefit'
                    if rec.state == 'suspended_second_approve' or rec.is_dead == True:
                        rec.member_status = 'non_benefit'
                elif rec.relationn.relation_type == 'daughter':
                    if rec.age < female_benefit_age and rec.is_married:
                       rec.member_status = 'non_benefit'
                    if rec.age < female_benefit_age and rec.is_work and rec.education_status not in ['educated'] and rec.case_study != 'continuous':
                        rec.member_status = 'non_benefit'
                    if rec.age > female_benefit_age:
                        if rec.age > minor_siblings_age and not rec.minor_siblings:
                            rec.member_status = 'non_benefit'
                        elif not rec.minor_siblings:
                            rec.member_status = 'non_benefit'
                        elif rec.minor_siblings and rec.age > minor_siblings_age:
                            rec.member_status = 'non_benefit'
                        # elif rec.is_work and rec.education_status in ['illiterate'] and rec.case_study in [
                        #     'graduate', 'intermittent']:
                        #     rec.member_status = 'non_benefit'
                        elif rec.is_married:
                            rec.member_status = 'non_benefit'
                        # elif not rec.minor_siblings:
                        #     rec.member_status = 'non_benefit'
                    if rec.is_work and rec.member_income > max_income_for_benefit and rec.education_status in ['educated'] and rec.case_study == 'continuous':
                        rec.member_status = 'non_benefit'
                    if rec.is_work and rec.education_status in ['illiterate'] :
                            rec.member_status = 'non_benefit'
                    if rec.is_work and rec.education_status in ['educated'] and rec.case_study in [
                            'graduate', 'intermittent']:
                            rec.member_status = 'non_benefit'
                    if not rec.member_location_conf.is_benefit:
                        rec.member_status = 'non_benefit'
                    if rec.state == 'suspended_second_approve' or rec.is_dead == True:
                        rec.member_status = 'non_benefit'
                # General checks for all members
                # if rec.is_work:
                #     if rec.member_income > max_income_for_benefit:
                #         rec.member_status = 'non_benefit'
                #     if not rec.is_married and rec.education_status in ['illiterate'] and rec.case_study in [
                #         'graduate', 'intermittent']:
                #         rec.member_status = 'non_benefit'
                # if rec.member_location in ['with_relative', 'study_outside_saudi_arabia']:
                #     rec.member_status = 'non_benefit'
            else:
                rec.member_status = False

    @api.depends('birth_date')
    def _compute_get_age_date(self):
        for rec in self:
            if rec.birth_date:
                today = date.today()
                day = datetime.strptime(str(rec.birth_date), DEFAULT_SERVER_DATE_FORMAT)
                age = rd(today, day)
                rec.age = age.years
            else:
                rec.age = 0

    @api.onchange("member_id_number")
    def onchange_member_id_number(self):
        for rec in self:
            if rec.member_id_number:
                # Check if the value is numeric
                if not rec.member_id_number.isdigit():
                    raise ValidationError(_("The ID number should contain only digits."))

                # Check if the ID number contains exactly 10 digits
                if len(rec.member_id_number) != 10:
                    raise ValidationError(_("The ID number must contain exactly 10 digits."))

                # Check if the father ID and mother ID are the same on the same record
                if rec.member_id_number == rec.benefit_id.mother_id_number or rec.member_id_number == rec.benefit_id.father_id_number or rec.member_id_number == rec.benefit_id.replacement_mother_id_number:
                    raise ValidationError(_("ID number cannot be the same with mother or replacement mother or father id number"))

                # Check if the ID number exists in other records or in family members
                exist = self.search([
                    ('member_id_number', '=', rec.member_id_number)
                ],limit=1)
                exist_in_family = self.env["grant.benefit"].search([
                    '|','|',
                    ('father_id_number', '=', rec.member_id_number),
                    ('mother_id_number', '=', rec.member_id_number),
                    ('replacement_mother_id_number', '=', rec.member_id_number),
                ],limit=1)
                if exist or exist_in_family:
                    if exist_in_family:
                        raise ValidationError(_("The ID Number already exists in Family with code %s")%exist_in_family.code)
                    if exist :
                        raise ValidationError(
                            _("The ID Number already exists in Family with code %s") % exist.benefit_id.code)
    # @api.onchange("member_id_number")
    # def onchange_member_id_number(self):
    #     for rec in self:
    #         if rec.member_id_number:
    #             exist = self.search([('member_id_number', '=', rec.member_id_number)])
    #             if exist:
    #                 raise ValidationError(
    #                     _('The ID Number Already Exist!'))

    @api.onchange('relationn','member_status','gender','birth_date', 'is_scientific_specialty', 'is_medical_specialty', 'has_disabilities', 'is_married',
                  'minor_siblings','member_income','is_married','member_location_conf','education_status','case_study')
    def onchange_member_status(self):
        res ={}
        for rec in self:
            if rec.member_status == 'non_benefit':
                res['warning'] = {'title': _('ValidationError'),
                                       'message': _('Not Benefit')}
                return res

    #Member Suspend Manual
    def action_suspend(self):
        for rec in self :
            rec.is_member_workflow = True
            rec.is_excluded_suspension = False
        return {
            'name': _('Suspend Reason Wizard'),
            'view_mode': 'form',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'res_model': 'suspend.reason.wizard',
            'view_id': self.env.ref('odex_benefit.view_suspend_member_reason_wizard_form').id,
            'target': 'new',
        }
    def action_suspend_first_accept(self):
        for rec in self:
            rec.state_a = 'suspended_first_approve'
    def action_suspend_second_accept(self):
        for rec in self:
            rec.state_a = 'suspended_second_approve'
    def action_suspend_refuse(self):
        for rec in self:
            rec.state_a = 'second_approve'
            rec.is_member_workflow = False
    # Excption Work flow
    def action_exception(self):
        for rec in self:
            rec.is_member_workflow = True
        return {
            'name': _('Exception Wizard'),
            'view_mode': 'form',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'res_model': 'exception.wizard',
            'view_id': self.env.ref('odex_benefit.view_exception_member_wizard_form').id,
            'target': 'new',
        }

    def action_exception_first_accept(self):
        for rec in self:
            rec.state_a = 'exception_first_approve'

    def action_exception_second_accept(self):
        for rec in self:
            rec.is_excluded_suspension = True
            rec.state_a = 'exception_second_approve'
            # rec.is_member_workflow = False

    def action_exception_final_accept(self):
        for rec in self:
            rec.is_excluded_suspension = True
            rec.state_a = 'second_approve'
            # rec.is_member_workflow = False

    def action_auto_exception(self):
        obj = self.env["family.member"].search(
            [('state', '=', 'second_approve'), ('is_excluded_suspension', '=', True)])
        for rec in obj:
            if rec.exception_end_date and rec.exception_end_date <= fields.Datetime.now():
                rec.is_excluded_suspension = False
                rec.state = 'suspended_second_approve'

    def action_exception_refuse(self):
        for rec in self:
            rec.state_a = 'suspended_second_approve'
            rec.is_member_workflow = False

    # Methods for Work flow for Member
    def complete_data(self):
        # message = self.create_message('complete_info')
        # self.partner_id.send_sms_notification(message, self.phone)
        self.state_a = 'complete_info'
        return {
            'name': _('Rerearcher Wizard'),
            'view_mode': 'form',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'res_model': 'researcher.member.wizard',
            'view_id': self.env.ref('odex_benefit.view_resarcher_member_wizard_form').id,
            'target': 'new',
        }

    def finish_complete_data(self):
        message = self.create_message('waiting_approve')
        # self.partner_id.send_sms_notification(message, self.phone)
        self.state_a = 'waiting_approve'
    def action_accepted(self):
        """Accept  registration"""
        self.state_a = "second_approve"
    def action_first_refusal(self):
        """First refusal to entity registration"""
        domain = []
        context = {}
        context = dict(self.env.context or {})
        context['state_a'] = "first_refusal"
        # self.partner_id.send_sms_notification("First Refusal", self.phone)
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
    def action_edit_info(self):
        # user = self.user_id
        # if not user:
        #     user = self.env['res.users'].sudo().search(
        #         [('partner_id', '=', self.partner_id.id), ('active', '=', False)])
        #     if user:
        #         user.write({'active': True})
        #     else:
        #         user = self.create_user()
        # group_e = self.env.ref('odex_benefit.group_benefit_edit', False)
        # try:
        #     group_e.sudo().write({'users': [(4, user.id)]})
        #     self.old_stage = self.state
        #     template = self.env.ref('odex_benefit.edit_benefit_email', False)
        # except:
        #     pass
        self.state = 'edit_info'
    def action_finish_edit(self):
        for rec in self:
            # group_e = self.env.ref('odex_benefit.group_benefit_edit', False)
            # group_e.write({'users': [(3, self.user_id.id)]})
            rec.state_a = rec.old_stage
    def create_manual_visit(self):
        self.env['visit.location'].create({
            'benefit_id': self.id,
            'visit_date': date.today(),
            'visit_types': 2,
            'contact_type': 'email',
            # 'selector': 'researcher',
            'researcher_id': self.researcher_id.id,
            # 'researcher_team': rec.researcher_team.id,
            'state': 'draft'
        })
    def not_alive(self):
        self.life = False
        self.state_a = 'not_leaving'

    @api.onchange('member_phone')
    def _onchange_member_phone_validation(self):
        if self.member_phone:
            if self.member_phone.startswith('+966'):
                member_phone = self.member_phone[4:]
                self.member_phone = member_phone
            if re.match(SAUDI_MOBILE_PATTERN, self.member_phone) == None:
                raise ValidationError(
                    _('Enter a valid Saudi mobile number'))
            exist = self.search([('member_phone', '=', self.member_phone)])
            if exist:
                raise ValidationError(
                    _('This Phone Already Exist!'))
                # Check if the father ID and mother ID are the same on the same record
            if self.member_phone == self.benefit_id.phone or self.member_phone == self.benefit_id.phone2 or self.member_phone == self.benefit_id.sms_phone:
                raise ValidationError(
                    _("Phone number cannot be the same in The Family"))

            # Check if the ID number exists in other records or in family members
            exist = self.search([
                ('member_phone', '=', self.member_phone)
            ], limit=1)
            exist_in_family = self.env["grant.benefit"].search([
                '|', '|',
                ('phone', '=', self.member_phone),
                ('phone2', '=', self.member_phone),
                ('sms_phone', '=', self.member_phone),
            ], limit=1)
            if exist or exist_in_family:
                if exist_in_family:
                    raise ValidationError(
                        _("The phone Number already exists in Family with code %s") % exist_in_family.code)
                if exist:
                    raise ValidationError(
                        _("The phone Number already exists in Family with code %s") % exist.benefit_id.code)





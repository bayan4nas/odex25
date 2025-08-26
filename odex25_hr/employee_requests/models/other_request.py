# -*- coding: utf-8 -*-

from odoo import api, fields, models, _, exceptions
from hijri_converter import convert
from typing import List, Dict
from dateutil.relativedelta import relativedelta
from odoo.exceptions import ValidationError


class EmployeeOtherRequest(models.Model):
    _name = 'employee.other.request'
    _rec_name = 'employee_id'
    _description = 'Other Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    from_hr = fields.Boolean()
    iqama_number = fields.Many2one(comodel_name="hr.employee.document", domain=[("document_type", "=", "Iqama")],
                                   tracking=True, string="Identity")
    def print_with_details(self):
        return self.env.ref('employee_requests.salary_def_report_act').report_action(self)

    def get_employee_totalallownce(self):
        self.ensure_one()
        allowance_record = self.env['hr.payslip'].search([
            ('employee_id', '=', self.employee_id.id),
            ('contract_id', '=', self.employee_id.contract_id.id),
            ('date_from', '<=', self.date),  # Ensure request_date is after or equal to date_from
            ('date_to', '>=', self.date),  # Ensure request_date is before or equal
        ], limit=1).mapped('total_allowances')

        return allowance_record

    def get_employee_allowances(self) -> List[Dict[str, float]]:
        """
        Retrieve allowance names and amounts for the same employee
        and the same payslip period (date_from, date_to).

        Returns:
            List[Dict[str, float]]: A list of dictionaries containing
            allowance name and amount.
        """
        self.ensure_one()  # Ensure the method is called on a single record

        # Search for payslips with the same employee and period
        allowance_records = self.env['hr.payslip'].search([
            ('employee_id', '=', self.employee_id.id),
            ('contract_id', '=', self.employee_id.contract_id.id),
            ('date_from', '<=', self.date),  # Ensure request_date is after or equal to date_from
            ('date_to', '>=', self.date),  # Ensure request_date is before or equal
        ], limit=1).mapped('allowance_ids')

        # Extract allowance name and amount into a list of dictionaries
        allowances_data = [
            {'name': allowance.name, 'amount': allowance.amount}
            for allowance in allowance_records
            if allowance.code != 'basic'  # Exclude allowances with code 'basic'
        ]

        return allowances_data

    # add new field
    passport_number = fields.Char(related='employee_id.passport_id.passport_id', readonly=True,
                                  string='Passport Number', store=True)
    date = fields.Date(default=lambda self: fields.Date.today())
    comment = fields.Text()
    state = fields.Selection(selection=[('draft', _('Draft')),
                                        ('submit', _('Waiting Direct Manager')),
                                        ('hcm', _('Human Capital manager')),
                                        ('confirm', _('Wait HR Department')),
                                        ('approved', _('Approval')),
                                        ('refuse', _('Refused'))],
                             default='draft', tracking=True)
    request_type = fields.Selection(selection=[('dependent', _('Dependent')),
                                               ('insurance', _('Insurance')), ('card', _('Business Card')),
                                               ('qualification', _('Qualification')),
                                               ('certification', _('Certification')),
                                               ('salary_define', _('Salary Define')),
                                               ('salary_fixing', _('Salary Fixing')),
                                               ('suggestion', _('Suggestion')),
                                               ('complaint', _('Complaint')),
                                               ('years_of_experienc', _('Years of Experienc')),

                                               ('other_requests', _('Other Requests'))], tracking=True)

    # relational fields
    employee_id = fields.Many2one('hr.employee', default=lambda item: item.get_user_id(),
                                  domain=[('state', '=', 'open')])
    employee_no = fields.Char(related='employee_id.emp_no', readonly=True, string='Employee Number', store=True)
    department_id = fields.Many2one(comodel_name='hr.department', related='employee_id.department_id', readonly=True,
                                    store=True)
    job_id = fields.Many2one(comodel_name='hr.job', related='employee_id.job_id', readonly=True)
    contract_statuss = fields.Selection(related='employee_id.contract_id.contract_status', readonly=True)

    employee_dependant = fields.One2many('hr.employee.dependent', 'request_id', _('Employee Dependants'))

    qualification_employee = fields.One2many('hr.qualification', 'request_id', _('Employee Qualification'))
    certification_employee = fields.One2many('hr.certification', 'request_id', _('Employee Certification'))
    create_insurance_request = fields.Boolean()
    print_type = fields.Selection(selection=[('detail', _("With Details")),
                                             ('no_detail', _("Without Details")),
                                             ('no_salary', _("Without Salary"))], string='Print Type')
    destination = fields.Many2one('salary.destination', string='Destination')
    parent_request_id = fields.Many2one('employee.other.request')
    destination_english = fields.Char(string='Destination English')


    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.user.company_id)

    is_branch = fields.Many2one(related='department_id.branch_name', store=True, readonly=True)
    experience_line_ids = fields.One2many(
        'employee.request.experience.line',
        'request_id',
        string="Previous Experience Lines")

    # def print_with_details(self):
    #     return self.env.ref('employee_requests.action_report_employee_identification').report_action(self)

    def print_with_details2(self):
        return self.env.ref('employee_requests.action_report_employee_identify_2').report_action(self)

    def print_with_details3(self):
        return self.env.ref('employee_requests.action_report_employee_identify_3').report_action(self)

    def print_without_details(self):
        return self.env.ref('employee_requests.action_report_employee_identify_3').report_action(self)

    def print_salary_confirmation(self):
        return self.env.ref('employee_requests.salary_conf_report_act').report_action(self)

    '''@api.onchange('employee_id')
    def chick_hiring_date(self):
        for item in self:
            if item.employee_id:
                if not item.employee_id.first_hiring_date:
                    raise exceptions.Warning(
                        _('You can not Request Other Request The Employee have Not First Hiring Date'))'''

    def get_user_id(self):
        employee_id = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)
        if employee_id:
            return employee_id.sudo().id
        else:
            return False

    def submit(self):
        for item in self:
            if item.employee_id:
                if not item.employee_id.first_hiring_date:
                    raise exceptions.Warning(
                        _('You can not Request Other Request The Employee has Not First Hiring Date'))
            if item.request_type == 'dependent':
                if not item.employee_dependant:
                    raise exceptions.Warning(_('Please The dependents were not Included'))

                for rec in item.employee_dependant:
                    if not rec.attachment:
                        raise exceptions.Warning(_('Please Insert dependents Attachments Files Below!'))

                #if item.employee_id.contract_id.contract_status == 'single':
                    #raise exceptions.Warning(_('You can not Add Family record Because Employee is Single'))
            if item.request_type == 'years_of_experienc':
                if not item.experience_line_ids:
                    raise exceptions.Warning(_('Please insert previous experience details before submitting.'))
                for line in item.experience_line_ids:

                    missing_fields = []

                    if not line.company_name:
                        missing_fields.append(_("Company Name"))
                    if not line.job_field:
                        missing_fields.append(_("Position"))
                    if not line.job_domain_id:
                        missing_fields.append(_("Job Domain"))
                    if not line.date_start:
                        missing_fields.append(_("Start Date"))
                    if not line.date_end:
                        missing_fields.append(_("End Date"))
                    if not line.country_id:
                        missing_fields.append(_("Country"))

                    if missing_fields:
                        raise ValidationError(_(
                            "One of the experience lines is missing required fields.\nPlease fill in the following fields:\n- " +
                            "\n- ".join(missing_fields)
                        ))

            if item.request_type == 'qualification':
                if not item.qualification_employee:
                    raise exceptions.Warning(_('Please The qualification or certification were not Insert Below!'))

                for rec in item.qualification_employee:
                    if not rec.attachment:
                        raise exceptions.Warning(_('Please Insert Attachments Files Below!'))

            if item.request_type == 'certification':
                if not item.certification_employee:
                    raise exceptions.Warning(_('Please The qualification or certification were not Insert Below!'))

                for rec in item.certification_employee:
                    if not rec.attachment:
                        raise exceptions.Warning(_('Please Insert Attachments Files Below!'))

            item.state = "submit"

    def confirm(self):
        # self.state = 'confirm'
        for rec in self:
            # manager = rec.sudo().employee_id.parent_id
            # hr_manager = rec.sudo().employee_id.company_id.hr_manager_id
            # if manager:
            #     if (manager.user_id.id == rec.env.uid or hr_manager.user_id.id == rec.env.uid):
            #         rec.write({'state': 'confirm'})
            #     else:
            #         raise exceptions.Warning(
            #             _("Sorry, The Approval For The Direct Manager '%s' Only OR HR Manager!") % (
            #                 rec.employee_id.parent_id.name))
            # else:
                if rec.request_type == 'qualification' or rec.request_type == 'certification' or 'years_of_experienc':
                    rec.write({'state': 'hcm'})
                else:
                    rec.write({'state': 'confirm'})


    def approved_hcm(self):
        for rec in self:
            rec.write({'state': 'confirm'})

    def approved(self):
        for item in self:
            if item.request_type == 'dependent':
                if item.employee_dependant:
                    item.employee_dependant.write({
                        'contract_id': item.employee_id.contract_id.id,
                    })
                    if self.create_insurance_request:
                        self.env['employee.other.request'].create({
                            'employee_id': item.employee_id.id,
                            'department_id': item.department_id.id,
                            'job_id': item.job_id.id,
                            'contract_statuss': item.contract_statuss,
                            'date': item.date,
                            'request_type': 'insurance',
                            'parent_request_id': item.id,
                            'comment': item.comment,
                            # 'employee_dependant': [(0, 0, line) for line in line_vals],
                            'state': 'submit'
                        })

            if item.request_type == 'qualification':
                if item.qualification_employee:
                    item.qualification_employee.write({
                        'qualification_relation_name': item.employee_id.id,
                    })

            if item.request_type == 'certification':
                if item.certification_employee:
                    item.certification_employee.write({
                        'certification_relation': item.employee_id.id,
                    })
            if item.request_type == 'years_of_experienc':
                for line in item.experience_line_ids:

                    history = self.env['hr.employee.history'].create({
                        'employement_history': item.employee_id.id,
                        'name': line.company_name,
                        'employeer': '',
                        'position': line.job_field,
                        'salary': 0.0,
                        'date_from': line.date_start,
                        'date_to': line.date_end,
                        'country': line.country_id.id,
                        'job_domain_id': line.job_domain_id.id,
                        'address':''
                    })
                    self.env['emplpyee.attachment'].create({
                        'employee_attaches_id': item.employee_id.id,
                        'doc_name': self.env.ref('employee_requests.employee_attachment_name_experience').id,
                        'attachment': line.attachment,
                        'name': line.attachment_filename,
                    })

        self.state = 'approved'

    def refuse(self):
        for item in self:
            if item.request_type == 'dependent':
                if item.employee_dependant:
                    item.employee_dependant.write({
                        'contract_id': False
                    })

            if item.request_type == 'qualification':
                if item.qualification_employee:
                    item.qualification_employee.write({
                        'qualification_relation_name': False
                    })

            if item.request_type == 'certification':
                if item.certification_employee:
                    item.certification_employee.write({
                        'certification_relation': False
                    })

        self.state = 'refuse'

    # Refuse For The Direct Manager
    def direct_manager_refused(self):
        for rec in self:
            manager = rec.sudo().employee_id.parent_id
            hr_manager = rec.sudo().employee_id.company_id.hr_manager_id
            if manager:
                if manager.user_id.id == rec.env.uid or hr_manager.user_id.id == rec.env.uid:
                    rec.refuse()
                else:
                    raise exceptions.Warning(
                        _("Sorry, The Refuse For The Direct Manager '%s' Only OR HR Manager!") % (manager.name))
            else:
                rec.refuse()

    def draft(self):
        for item in self:
            if item.request_type == 'dependent':
                if item.employee_dependant:
                    item.employee_dependant.write({
                        'contract_id': False
                    })

        self.state = 'draft'

    def change_current_date_hijri(self):
        date = fields.Date.from_string(self.date)
        year = date.year
        day = date.day
        month = date.month
        hijri_date = convert.Gregorian(year, month, day).to_hijri()
        return hijri_date

    @api.constrains('certification_employee')
    def check_attachment(self):
        if self.certification_employee:
            for rec in self.certification_employee:
                if not rec.attachment:
                    raise ValidationError(_("You must add an attachment for all certifications."))


class salaryDestination(models.Model):
    _name = 'salary.destination'
    _description = 'Salary Destination'

    name = fields.Char(string='Name')
    english_name = fields.Char(string='English Name')


# Hr_Employee_dependent
class EmployeeDependent(models.Model):
    _inherit = 'hr.employee.dependent'

    request_id = fields.Many2one('employee.other.request')
    iqama_number = fields.Many2one(comodel_name="hr.employee.document", domain=[("document_type", "=", "Iqama")],
                                   tracking=True, string="Identity")

# Hr_Employee_Qualification
class Qualification(models.Model):
    _inherit = 'hr.qualification'

    request_id = fields.Many2one('employee.other.request')


# Hr_Employee_Certification
class HrCertification(models.Model):
    _inherit = 'hr.certification'

    request_id = fields.Many2one('employee.other.request')



class EmployeeRequestExperienceLine(models.Model):
    _name = 'employee.request.experience.line'
    _description = 'Employee Previous Experience Line'

    request_id = fields.Many2one('employee.other.request', string="Other Request", ondelete="cascade")
    company_name = fields.Char(string="Company Name" )
    job_field = fields.Char(string="Job Field / Position")
    job_domain_id = fields.Many2one('employee.job.domain', string="Job Domain" )
    date_start = fields.Date(string="Start Date")
    date_end = fields.Date(string="End Date")
    country_id = fields.Many2one('res.country', string="Country")
    attachment = fields.Binary(string="Attachment")
    attachment_filename = fields.Char(string="Attachment File Name")

    duration = fields.Char(string="Duration", compute="_compute_duration", store=True)



    @api.depends('date_start', 'date_end')
    def _compute_duration(self):
        for rec in self:
            if rec.date_start and rec.date_end and rec.date_end >= rec.date_start:
                delta = relativedelta(rec.date_end, rec.date_start)
                years = delta.years
                months = delta.months
                days = delta.days

                duration_parts = []
                if years > 0:
                    duration_parts.append(f"{years} سنة")
                if months > 0:
                    duration_parts.append(f"{months} شهر")
                if days > 0:
                    duration_parts.append(f"{days} يوم")

                if duration_parts:
                    text = '، '.join(duration_parts)
                    rec.duration = '\u200F' + text
                else:
                    rec.duration = "0 يوم"
            else:
                rec.duration = "—"

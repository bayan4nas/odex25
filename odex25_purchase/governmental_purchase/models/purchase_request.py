# -*- coding: utf-8 -*-
from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.tools.misc import get_lang


class PurchaseRequest(models.Model):
    _inherit = 'purchase.request'

    state = fields.Selection(
        [('draft', 'Draft'),
         ('dm', 'Management Manager'),
         ('direct_manager', 'Technical Department'),
         ('send_budget', 'Send to Budget Confirmation'),
         ('wait_budget', 'Wait Budget'),
         ('ceo_purchase', 'Manager OF Purchasing And Contract'),
         ('executive_vice', 'Executive Vice President'),
         ('general_supervisor', 'Chief Executive Officer'),
         ('waiting', 'Procurement Department'),
         ('done', 'Done'),
         ('refuse', 'Refuse')], default="draft", tracking=True)
    project_name = fields.Char('Project Name', copy=False)
    sub_project = fields.Char('Sub Project', copy=False)
    project_duration = fields.Char('Project Duration', copy=False)
    strategic_objective = fields.Selection([
        ('e_d_p', '3.1.1 Ease of doing business'),
        ('a_f_d_i', '3.1.6 Attracting foreign direct investment'),
        ('d_r_s', '3.3.5 Development of the retail sector'),
        ('i_c_e', '4.3.2 Increasing SMEs contribution to the economy'),
        ('other', 'Other')
    ], string='Strategic Objective', copy=False)

    other_strategic_objective = fields.Char('Other Strategic objective', copy=False)
    vision_program_name = fields.Char('Vision Program Name', copy=False)
    initiative_name = fields.Char('Initiative Name', copy=False)
    initiative_end_date = fields.Date('Initiative End Date', copy=False)
    is_direct_manager = fields.Boolean('Sent Technical Department', copy=False)
    cso_agreed = fields.Selection([
        ('agreed', 'Agreed'),
        ('not_agreed', 'Not Agreed'),
    ], string='Agreed', copy=False)
    cso_compatible = fields.Selection([
        ('compatible', 'Compatible with scope '),
        ('Incompatible', 'Incompatible with scope '),
    ], string='Compatible', copy=False)
    company_id = fields.Many2one(string='Company', comodel_name='res.company',
                                 default=lambda self: self.env.user.company_id)
    attachment_booklet_uploade = fields.Binary(string="Upload Booklet", copy=False)
    document_cost = fields.Char('Document cost', copy=False)
    body_technical = fields.Char('Body Technical', copy=False)
    pre_qualification = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string='Pre-Qualification Linked ?', copy=False)
    initial_guarantee_percentage = fields.Float(
        'Initial Guarantee Percentage (%)', copy=False)
    applying_address = fields.Char('Applying Address', copy=False)
    alternative_offer_allowed = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string='Alternative Offer Allowed ?', copy=False)
    is_competition_divisible = fields.Selection([
        ('yes', 'Yes'),
        ('no', 'No')
    ], string='Is Competition Divisible?', copy=False)
    classify_des = fields.Text('Classify', copy=False)

    tender_name = fields.Char('Tender Name', copy=False)
    purpose_of_tender = fields.Char('Purpose of Tender ', copy=False)
    is_delivered = fields.Selection([
        ('no', 'NO'),
        ('yes', 'YES')
    ], string='Do samples need to delivered', copy=False)

    samples_delivery_address = fields.Char('Samples  Address', copy=False)
    delivery_building = fields.Char('building', copy=False)
    delivery_floor = fields.Char('Floor', copy=False)
    delivery_unit = fields.Char('Unit', copy=False)
    date_time = fields.Datetime('Date and Time', copy=False)
    Delivery_place = fields.Selection([
        ('out', 'Out of Saudi Arabia'),
        ('inside', 'Inside  Saudi Arabia')
    ], string='Delivery_place', copy=False)
    other_details = fields.Text('Other details', copy=False)
    # activities = fields.Many2many('activity.type', string='Activities', copy=False)
    activity_description = fields.Text('Activity Description', copy=False)
    competion_description = fields.Text('Competion Description', copy=False)
    list_documentaries = fields.Text('List documentaries', copy=False)
    attachment_scope_project = fields.Binary(string="Attachment Scope Project", copy=False)
    program_action = fields.Char('Program of action', copy=False)
    work_location_district = fields.Char('Work Location District', copy=False)
    work_location_city = fields.Char('Work Location City', copy=False)
    work_location_state = fields.Char('Work Location State', copy=False)
    work_location_GPS = fields.Char('Work Location GPS', copy=False)
    cancel_reason = fields.Char(string='Reason')
    user_id = fields.Many2one(comodel_name='res.users',string='User id')


    def action_dm_confirm(self):
        if len(self.line_ids) == 0:
            raise ValidationError(_("Can't Confirm Request With No Item!"))
        if not self.department_id:
            raise ValidationError(_("Please Select department for employee"))
        for rec in self.line_ids:
            if rec.request_id.is_analytic:
                if not rec.account_id:
                    raise ValidationError(_("Please select an analytic account"))
            if rec.sum_total <= 0:
                raise ValidationError(_("Total Amount MUST be greater than 0 !!!"))

        self.write({'state': 'dm'})
       

    def approve_department(self):
        self.write({'state': 'send_budget'})

    def action_pc_confirm(self):
        amount = 0
        for rec in self.line_ids:
            amount = amount + rec.sum_total
        if amount >= self.company_id.direct_purchase:
            self.write({'state': 'executive_vice'})
        else:
            self.write({'state': 'waiting'})

    def approve_executive_vice(self):
        amount = 0
        for rec in self.line_ids:
            amount = amount + rec.sum_total
        if amount >= self.company_id.chief_executive_officer:
            self.write({'state': 'general_supervisor'})
        else:
            self.write({'state': 'waiting'})

    def action_general_supervisor_approve(self):
        for request in self:
            request.write({'state': 'waiting'})

    def action_refuse(self):
        self.write({'state': 'refuse'})

    def download_url(self):
        return {
            "type": "ir.actions.act_url",
            "url": '/web/content/res.company/%s/attachment_booklet_exp/الكراسة الالكترونية الموحدة.docx' % self.company_id.id,
            "target": "new",
        }

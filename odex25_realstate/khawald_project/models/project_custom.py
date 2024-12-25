# -*- coding: utf-8 -*-
##############################################################################
#
#   Expert (LCT, Life Connection Technology)
#    Copyright (C) 2021-2022 LCT
#
##############################################################################

import string
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ProjectCustom(models.Model):
    _inherit = 'project.project'
    _description = "Khawald Project"

    project_type_id = fields.Many2one('project.type', string="Project Type")
    # project_status_id = fields.Many2one('project.status', string="Project Status")
    land_state_id = fields.Many2one('land.state', string="Land State")
    project_face_ids = fields.Many2many('project.face', string="Project Face")
    basement = fields.Selection([('yes', 'Yes'),
                                 ('no', 'NO')], string="Basement Available ?", default='no')
    owner_id = fields.Many2one('res.partner', string="Owner")
    agent_id = fields.Many2one('res.partner', string="GOV Agent")
    supervisor_id = fields.Many2one('res.partner', string="Supervisor")
    engineer_id = fields.Many2one('res.partner', string="Project Engineer")
    stamp = fields.Char(string="Stamp")
    building_license = fields.Char(string="Building License")
    building_certificate = fields.Char(string="Building Certificate")
    insurance_policy = fields.Char(string="Insurance Policy")
    space = fields.Float(string="Project Space")
    land_space = fields.Float(string="Land Space")
    building_factor = fields.Char(string="Building Factor")
    sale_space = fields.Char(string="Sale Space")
    location_x = fields.Char(string="Location X")
    location_y = fields.Char(string="Location Y")
    total_days = fields.Char(string="Total Days", compute="get_work_days", stroe=True)
    building_count = fields.Integer(string="Building count")
    floor_count = fields.Integer(string="Floor count")
    unit_count = fields.Integer(string="Unit in floor count")
    unit_space = fields.Float(string="Unit Space")
    total_unit = fields.Float(string="Total Unit", compute="get_unit_count", store=True)
    advantage_ids = fields.Many2many('project.advantage', string="Advantage", ondelete="cascade")
    project_state_ids = fields.Many2many('project.state', string="Project State", ondelete="cascade")
    project_task_ids = fields.Many2many('khawald.project.task', string="Project Task", ondelete="cascade")
    project_insurance_ids = fields.One2many('project.insurance', 'project_id', string="Insurance")
    invoice_ref = fields.Char(string="Contract/Invoice REF")
    state = fields.Selection([('draft', 'In Progress'),
                              ('in_progess', 'In Executing'),
                              ('sale', 'Selling'),
                              ('done', 'Sold'),
                              ('cancel', 'Cancelled'), ], string="Status", default='draft')
    created = fields.Boolean(string="Created")
    unit_counts = fields.Integer(string='Unit Count', compute='count_unit_number')
    project_expense_ids = fields.One2many('project.expense', 'project_id', string="Expense")
    stamping = fields.Char(string="Stamping Number")
    stamping_date = fields.Date(string="Stamping Date")
    stamping_attach = fields.Binary("Stamping Attach", attachment=True)

    room_no = fields.Integer(string="Room Count")
    bathroom_no = fields.Integer(string="Bathroom Count")
    hall_no = fields.Integer(string="Hall Count")
    kitchen_no = fields.Integer(string="kitchen Count")

    suppl_payment_amount = fields.Float('Supplier Payments Amount', compute="get_payment_amount")
    engineer_payment_amount = fields.Float('Engineering Payment', compute="get_payment_amount")
    subcontractor_payment_amount = fields.Float('Subcontractor Payment', compute="get_payment_amount")
    total_payment = fields.Float('Total Payment', compute="get_payment_amount")


    def count_unit_number(self):
        unit_count = self.env['re.unit'].search_count([('project_id', '=', self.id)])
        self.unit_counts = unit_count

    def get_unit(self):
        unit_ids = self.env['re.unit'].search(
            [('project_id', '=', self.id)])
        form_id = self.env.ref('real_estate.unit_form_view').id
        domain = [('id', 'in', unit_ids.ids)]
        return {
            'name': _('Units'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 're.unit',
            'views': [(False, 'tree'), (form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': domain,
        }


    def get_payment_amount(self):
        suppl_payment_amount = sum(self.project_expense_ids.mapped('amount'))
        engineering_payment_ids = self.env['project.payment.request'].search([('project_id', '=', self.id),
                                                                                      ('type', '=', 'eng_office')])
        subcontractor_payment_ids = self.env['project.payment.request'].search([('project_id', '=', self.id),
                                                                          ('type', '=', 'subcontractor')])

        self.suppl_payment_amount = suppl_payment_amount
        self.engineer_payment_amount = sum(engineering_payment_ids.mapped('amount'))
        self.subcontractor_payment_amount = sum(subcontractor_payment_ids.mapped('amount'))
        self.total_payment = suppl_payment_amount + sum(engineering_payment_ids.mapped('amount')) + sum(subcontractor_payment_ids.mapped('amount'))


    def get_supplier_payment(self):
        domain = [('id', 'in', self.project_expense_ids.ids)]
        tree_id = self.env.ref('khawald_project.project_expense_tree_view').id
        return {
            'name': _('Supplier Payments'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'project.expense',
            'views': [(tree_id, 'tree')],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': domain,
        }

    @api.model
    def create(self, vals):
        res = super(ProjectCustom, self).create(vals)
        for line in res:
            for tasks in line.project_task_ids:
                self.env['project.task'].create({
                    'name': tasks.name,
                    'project_id': line.id,
                    'days': tasks.tasks_time,
                    'description': tasks.description,
                    'project_type_id': line.project_type_id.id,
                    'project_task_id': tasks.id,
                    'state': 'draft'
                })
        return res

    def create_unit_building(self):
        letters = list(string.ascii_uppercase)
        for rec in self:
            no_unit = rec.total_unit / rec.building_count
            for building in range(rec.building_count):
                build = self.env['internal.property'].create({
                    'name': rec.code + '/' + letters[
                        building] if building <= 26 else rec.code + '/' + building if rec.project_type_id.name == 'apartment' else rec.code,
                    'city_id': rec.city.id,
                    'project_id': rec.id,
                    'floors_count': rec.floor_count,
                    'unit_floor_count': rec.unit_count,
                    'district_id': rec.district.id,
                    'stamping': rec.stamping,
                    'stamping_date': rec.stamping_date,
                    'stamping_attach': rec.stamping_attach,
                    'room_no':rec.room_no * rec.total_unit,
                    'bathroom_no':rec.bathroom_no * rec.total_unit,
                    'hall_no':rec.hall_no * rec.total_unit,
                    'kitchen_no':rec.kitchen_no * rec.total_unit,})
                for unit in range(int(no_unit)):
                    self.env['re.unit'].create({
                        'name': build.name + '/' + str(unit + 1),
                        'project_id': rec.id,
                        'space': rec.unit_space,
                        'property_id': build.id,
                        'stamping': rec.stamping,
                        'stamping_date': rec.stamping_date,
                        'stamping_attach': rec.stamping_attach,
                        'room_no':rec.room_no,
                        'bathroom_no':rec.bathroom_no,
                        'hall_no':rec.hall_no,
                        'kitchen_no':rec.kitchen_no,})
            rec.created = True

    def action_selling(self):
        self.state = 'sale'

    @api.onchange('project_type_id')
    def set_state_project(self):
        """
        set project tasks and state based on project type
        :return:
        """
        task_ids = []
        if self._context.get('project_type_id'):
            for record in self:
                state_ids = self.env['project.state'].search(
                    [('project_type_ids', 'in', [self._context.get('project_type_id')]), ('default', '=', True)])
                for state in state_ids:
                    for line in state.project_task_ids:
                        task_ids.append(line.id)
                record.write({'project_state_ids': state_ids.ids,
                              'project_task_ids': task_ids })


    @api.onchange('project_state_ids')
    def onchange_project_state_ids(self):
        """ get task related with state """

        self.project_task_ids = self.project_state_ids.mapped('project_task_ids').ids


    @api.depends('floor_count', 'unit_count')
    def get_unit_count(self):
        for rec in self:
            rec.total_unit = (rec.floor_count * rec.unit_count) * rec.building_count

    @api.depends('resource_calendar_id', 'date_start', 'date')
    def get_work_days(self):
        for rec in self:
            rec.total_days = 0.0
            if rec.date_start and rec.date_end:
                date_start = datetime.strptime(datetime.strftime(rec.date_start, '%Y-%m-%d'), '%Y-%m-%d')
                date_end = datetime.strptime(datetime.strftime(rec.date_end, '%Y-%m-%d'), '%Y-%m-%d')
                duration_data = self.resource_calendar_id.get_work_duration_data(date_start, date_end)
                rec.total_days = duration_data['days']
                


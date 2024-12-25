# -*- coding: utf-8 -*-
##############################################################################
#
#   Expert (LCT, Life Connection Technology)
#    Copyright (C) 2021-2022 LCT
#
##############################################################################


from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from random import randint

class ProjectExpenseConf(models.Model):
    _name = 'project.expense.conf'
    _description = "Project Expense"

    name = fields.Char(string="Name")


class ProjectTasks(models.Model):
    _name = 'khawald.project.task'
    _description = "Project Task Custom"

    name = fields.Char(string="Name")
    tasks_time = fields.Char(string="Task Days")
    description = fields.Text(string="Task Description")
    parent_id = fields.Many2one('khawald.project.task', string="Parent Task")

    @api.constrains('parent_id')
    def _check_parent_id(self):
        if not self._check_recursion():
            raise ValidationError(_('You cannot create recursive task.'))


class ProjectState(models.Model):
    _name = 'project.state'
    _description = "Project State"

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Char(string="Name")
    dependency_id = fields.Many2one('project.state', string="Dependency")
    parent_id = fields.Many2one('project.state', string="Parent")
    project_type_ids = fields.Many2many('project.type', 'project_type_state_rel', string="Project Type")
    project_id = fields.Many2one('project.project', string="Project", ondelete="cascade")
    project_task_ids = fields.Many2many('khawald.project.task', string="Task")
    total_tasks = fields.Integer(dtring="Total of Tasks", compute="get_total_task", store=True)
    default = fields.Boolean(string="Default")
    color = fields.Integer(string='Color', default=_get_default_color)
    rating_active = fields.Boolean('Customer Ratings',
                                   default=lambda self: self.env.user.has_group('project.group_project_rating'))
    rating_percentage_satisfaction = fields.Integer(
        "Rating Satisfaction",
       default=1, help="Percentage of happy ratings")
    is_favorite = fields.Boolean( string='Show Project on dashboard',default=True,
                                 help="Whether this project should be displayed on your dashboard.")

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "State name already exists!"),
    ]

    @api.depends('project_task_ids')
    def get_total_task(self):
        print(self, ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>111111111")
        for rec in self:
            rec.total_tasks = len(rec.project_task_ids)


    @api.constrains('parent_id')
    def _check_parent_id(self):
        if not self._check_recursion():
            raise ValidationError(_('You cannot create recursive state.'))


class ProjectType(models.Model):
    _name = 'project.type'
    _description = 'Project Type'

    def _get_default_color(self):
        return randint(1, 11)

    name = fields.Selection([('apartment', 'Apartment'),
                             ('vila', 'Vila'),
                             ('construction','Construction'),
                             ('general_service','General Service'),
                             ('oil_gas','Oil & Gas'),
                             ('mining','Mining')], string="Name")
    color = fields.Integer(string='Color', default=_get_default_color)


    @api.depends('name')
    def name_get(self):
        res = []
        for record in self:
            name = dict(record.fields_get(allfields=['name'])['name']['selection'])[record.name]
            res.append((record.id, name))
        return res

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Type name already exists!"),
    ]



class ProjectIssues(models.Model):
    _name = 'project.issue'
    _description = 'Project Issue'

    name = fields.Char(string="Issue")


class ProjectStatus(models.Model):
    _name = 'project.status'
    _description = 'Project Status'

    name = fields.Char(string="Status", required=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Status name already exists!"),
    ]


class LandState(models.Model):
    _name = 'land.state'
    _description = 'Land State'

    name = fields.Char(string="Land Sate", required=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Land State name already exists!"),
    ]


class ProjectFace(models.Model):
    _name = 'project.face'
    _description = 'Project Face'

    name = fields.Char(string="Face", required=True)

    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Project Face already exists!"),
    ]


class ProjectAdvantage(models.Model):
    _name = 'project.advantage'
    _description = 'Project Advantage'

    name = fields.Char(string="Advantage Name")
    price = fields.Monetary(string="Price", currency_field='company_currency_id')
    company_id = fields.Many2one('res.company', required=True, readonly=True, default=lambda self: self.env.company)
    company_currency_id = fields.Many2one(string='Company Currency', readonly=True,
                                          related='company_id.currency_id')
    project_id = fields.Many2one('project.project', string="Project", ondelete="cascade")


    _sql_constraints = [
        ('name_uniq', 'unique (name)', "Type name already exists!"),
    ]

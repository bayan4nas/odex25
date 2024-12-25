# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class Project(models.Model):
    _inherit = "project.project"

    project_customer_team_ids = fields.One2many('project.customer.team','project_id',string="Project Customer Team")

class ProjectTeam(models.Model):
    _name = "project.customer.team"

    name = fields.Char(string="Employee")
    project_id = fields.Many2one('project.project',string="Project")
    phone = fields.Char(string="Phone")
    email = fields.Char(string="E-mail")
    job = fields.Char(string="Job In Project")


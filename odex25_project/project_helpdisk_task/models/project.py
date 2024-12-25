# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class Project(models.Model):
    _inherit = "project.project"

    link_helpdisk_task = fields.Boolean(string="Link with Helpdisk")
    module_project_helpdisk_task = fields.Boolean(string="Link with Helpdisk",related='company_id.module_project_helpdisk_task')


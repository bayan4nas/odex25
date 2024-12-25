# -*- coding: utf-8 -*-
##############################################################################
#
#   Expert (LCT, Life Connection Technology)
#    Copyright (C) 2021-2022 LCT
#
##############################################################################

from odoo import models, fields


class Branches(models.Model):
    _name = 'res.branches'
    _description = "Branches"

    name = fields.Char(string="Name")
    manager_id = fields.Many2one('res.users', string="Supervisor")


class ProjectTaskType(models.Model):
    _inherit = 'project.task.type'

    case_default = fields.Boolean(string="Default in new project")



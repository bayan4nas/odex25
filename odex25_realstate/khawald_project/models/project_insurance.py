# -*- coding: utf-8 -*-
##############################################################################
#
#   Expert (LCT, Life Connection Technology)
#    Copyright (C) 2021-2022 LCT
#
##############################################################################

from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from dateutil.relativedelta import relativedelta

class ProjectInsurance(models.Model):
    _name = 'project.insurance'
    _description = "Project Insurance"
    _rec_name = ''

    partner_id = fields.Many2one('res.partner', string="Insurance Provider")
    project_insur_line_id = fields.Many2one('project.insurance.line',string='Description')
    project_id = fields.Many2one('project.project', string="Project")
    duration = fields.Integer(string="Insurance Duration", default=1)
    duration_kind = fields.Selection([('year', 'Year'),
                                      ('month', 'Month'),
                                      ], string="Duration Kind", default='year')
    date_from = fields.Date(string="Date from", default=fields.Date.today)
    date_to = fields.Date(string="Date To", compute="get_to_date", store=True)

    @api.depends('date_from', 'duration', 'duration_kind')
    def get_to_date(self):
        for rec in self:
            if rec.date_from and rec.duration and rec.duration_kind:
                date_from = datetime.strptime(datetime.strftime(rec.date_from, '%Y-%m-%d'), '%Y-%m-%d').date()
                date_from = date_from - relativedelta(days=int(1))
                if rec.duration_kind == 'year':
                    date_to = date_from + relativedelta(years=int(rec.duration))
                    rec.date_to = date_to.strftime('%Y-%m-%d')
                elif rec.duration_kind == 'month':
                    date_to = date_from + relativedelta(months=int(rec.duration))
                    rec.date_to = date_to.strftime('%Y-%m-%d')


class ProjectInsuranceLine(models.Model):
    _name = 'project.insurance.line'
    _description = "Project Insurance Line"

    name = fields.Char(string='Name', required=True)

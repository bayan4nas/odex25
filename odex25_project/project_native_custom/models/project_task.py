# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class Project(models.Model):
    _inherit = "project.project"

    scheduling_type = fields.Selection('_get_scheduling_type',
                                       string='Scheduling Type',
                                       required=True,
                                       default='manual')

    @api.onchange('start')
    def _onchange_start_date(self):
        if self.start:
            self.date_start = self.start
            
    @api.onchange('date')
    def _onchange_end_date(self):
        if self.date:
            self.date_end = self.date

                      
    
class ProjectTas(models.Model):
    _inherit = 'project.task'

    on_gantt = fields.Boolean("Task name on gantt", default=True)
    color_gantt_set = fields.Boolean("Set Color Task", default=True)






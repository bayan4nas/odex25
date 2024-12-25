# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class ProjectTask(models.Model):
    _inherit = "project.task"

    ticket_id = fields.Many2one('odex25_helpdesk.ticket', string="Ticket Name")
    ticket_ip_address = fields.Char(string="IP Address")
    ticket_db_name = fields.Char(string="Database name")
    link_helpdisk_task = fields.Boolean(string="Link with Helpdisk",related='project_id.link_helpdisk_task')






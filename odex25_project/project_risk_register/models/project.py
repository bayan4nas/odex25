# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class Project(models.Model):
    _inherit = "project.project"

    risk_register_id = fields.One2many('project.risk.register', 'project_id', string="Risk register")

class ProjectRiskRegister(models.Model):
    _name = "project.risk.register"

    name = fields.Char(string="Description")
    risk_id = fields.Char(string="ID")
    action = fields.Char(string="Action(s)")
    project_id = fields.Many2one('project.project', string="project")
    source = fields.Selection([
        ('internal', 'Internal'),
        ('external', 'External')], string='Source', copy=False)
    type = fields.Selection([
        ('risk', 'Risk'),
        ('issue', 'Issue')], string='Type', copy=False)
    impact = fields.Selection([
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low')], string='Impact of the risk', copy=False)
    responsible_id = fields.Char(string="Responsible", copy=False)
    plan = fields.Text(string="Contingency Plan")
    lock = fields.Boolean('Lock')

    def do_lock(self):
        return self.write({'lock': True})

    def do_unlock(self):
        return self.write({'lock': False})



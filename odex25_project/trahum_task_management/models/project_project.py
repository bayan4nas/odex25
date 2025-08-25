from odoo import api, fields, models, _


class Project(models.Model):
    _inherit = "project.project"
    is_department = fields.Boolean('Is department')

from odoo import fields, models, api, _

class ServiceSettingsInherit(models.Model):

    _inherit = 'services.settings'

    project_create = fields.Boolean(string='Project Create?')
    category_id = fields.Many2one('project.category', string='Project Category')

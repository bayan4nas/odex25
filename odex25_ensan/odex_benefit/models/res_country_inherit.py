from odoo import fields, models

class MemberHobbies(models.Model):
    _inherit = 'res.country'

    is_excluded = fields.Boolean(string='Is Excluded?')


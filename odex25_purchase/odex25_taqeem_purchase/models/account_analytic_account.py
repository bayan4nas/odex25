from odoo import fields, models, _


class AccountAnalyticAccount(models.Model):
    _inherit = "account.analytic.account"

    item_executive_officer = fields.Many2one('hr.employee', string='Budget executive Officer')
    department_id = fields.Many2one('hr.department', string='department')

from odoo import models, fields, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    invoice_method = fields.Selection([
        ('per_stage', 'Invoicing per Stage'),
        ('per_period', 'Invoicing per Period'),
        ], default='per_stage', string='Invoicing Method')
    invoice_period = fields.Integer(string="Invoicing Period",default=30)
    module_project_risk_register = fields.Boolean(string="Project Risk Register")
    module_project_customer_team = fields.Boolean(string="Project Customer Team")
    module_project_scrum_agile = fields.Boolean(string="Project Customer Team")
    module_project_helpdisk_task = fields.Boolean(string="Link with Helpdisk")
    module_project_variation_order = fields.Boolean(string="Project Variation Order")
    module_project_metrics = fields.Boolean(string="Project Metrics")
    module_project_budget = fields.Boolean(string="Project Budget")
    type = fields.Selection([('revenue', 'Revenue'),
                             ('expense', 'Expense'),
                             ('internal', 'Internal')], default='revenue',string='Type')
    account_id = fields.Many2one('account.account', string="Account")
    analytic_account_id = fields.Many2one('account.analytic.account', string="Analytic Account")


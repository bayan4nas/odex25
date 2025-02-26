from odoo import models, fields, _, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    invoice_method = fields.Selection(string='Invoicing Method',related='company_id.invoice_method',readonly=False)
    invoice_period = fields.Integer(string="Invoicing Period",related='company_id.invoice_period',readonly=False)
    module_project_risk_register = fields.Boolean(string="Project Risk Register",related='company_id.module_project_risk_register',readonly=False)
    module_project_customer_team = fields.Boolean(string="Project Customer Team",related='company_id.module_project_customer_team',readonly=False)
    module_project_scrum_agile = fields.Boolean(string="Scrum Agile",related='company_id.module_project_scrum_agile',readonly=False)
    module_project_helpdisk_task = fields.Boolean(string="Link with Helpdisk",related='company_id.module_project_helpdisk_task',readonly=False)
    module_project_variation_order = fields.Boolean(string="Project Variation Order",related='company_id.module_project_variation_order',readonly=False)
    module_project_metrics = fields.Boolean(string="Project Metrics",related='company_id.module_project_metrics',readonly=False)
    module_project_budget = fields.Boolean(string="Project Budget",related='company_id.module_project_budget',readonly=False)
    type = fields.Selection([('revenue', 'Revenue'),
                             ('expense', 'Expense')], string='Type',related='company_id.type',readonly=False)
    account_id = fields.Many2one(
    'account.account',
    string="Account",
    related='company_id.account_id',
    readonly=False,  
    store=True  
    )

    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string="Analytic Account",
        related='company_id.analytic_account_id',
        readonly=False,
        store=True
    )

from odoo import models, fields, api

# [IMP] account_budget_custom: Prepare models for access rights extension from purchase_requisition_custom


class CrossoveredBudget(models.Model):
    _inherit = 'crossovered.budget'


    pass



class AccountBudgetPost(models.Model):
    _inherit = 'account.budget.post'


    pass

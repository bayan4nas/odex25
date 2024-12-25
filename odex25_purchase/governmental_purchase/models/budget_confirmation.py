from odoo import fields, api ,models, _


class BudgetConfirmationCustom(models.Model):
    _inherit = 'budget.confirmation'

    budget_scope = fields.Selection([
        ('operational_budget', 'Operational Budget'),
        ('initiative', 'Initiative'),
        ('KSAgreement_budget', 'Korean Side Agreement Budget'),
        ('revenue_budget', 'Revenue Budget'),
        ('strategy','National Strategy Budget'),
        ('other','Other')
    ], string="Budget Scope")
    
    permission = fields.Selection([
        ('allowed', 'Item Allows'),
        ('not_allowed', 'Item Not Allows'),
    ], string="Permission")
    

        
class BudgetConfirmationLineCustom(models.Model):
    _inherit = 'budget.confirmation.line'
    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Cost Center',
        required=False
    )
    
    @api.onchange('analytic_account_id')
    def _onchange_analytic_account_id(self):
        rec_remain = self.analytic_account_id.crossovered_budget_line.\
            filtered(lambda x : x.date_from <= self.date and x.date_to >= self.date)
        if rec_remain :
            self.remain =  rec_remain[0].remain
            

        
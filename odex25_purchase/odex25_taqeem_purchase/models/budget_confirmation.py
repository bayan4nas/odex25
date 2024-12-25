from odoo import fields, models, _


class BudgetConfirmationCustom(models.Model):
    _inherit = 'budget.confirmation'

    def done(self):
        super(BudgetConfirmationCustom, self).done()
        if self.request_id and self.type == 'purchase.request':
            self.request_id.write({'state': 'budget_approve'})

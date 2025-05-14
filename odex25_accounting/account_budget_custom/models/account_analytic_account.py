from odoo import api, fields, models, _


# from odoo.exceptions import UserError, ValidationError

class AccountAnalyticAccount(models.Model):
    _inherit = 'account.analytic.account'

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        User = self.env.user
        print(User, 'etetetete')
        if User.has_group('account_budget_custom.group_user_budget_department'):
            managed_departments = self.env['hr.department'].search([('manager_id.user_id', '=', User.id)])
            analytic_ids = managed_departments.mapped('analytic_account_id').ids
            args += [('id', 'in', analytic_ids)]
        return super().search(args, offset=offset, limit=limit, order=order, count=count)

from odoo import api, fields, models, _


class AccountAccount(models.Model):
    _inherit = "account.account"
    type = fields.Selection(related='user_type_id.type')


class AccountBudgetPost(models.Model):
    _inherit = "account.budget.post"
    account_ids = fields.Many2many(
        domain="[('deprecated', '=', False), ('company_id', '=', company_id),('type','!=','view')]")

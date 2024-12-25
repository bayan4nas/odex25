from odoo import fields, models, api, _


class ExpensesType(models.Model):
    _name = 'expenses.type'

    name = fields.Char(string='Name', required=False)

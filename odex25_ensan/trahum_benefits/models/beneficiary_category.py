from odoo import fields, models, api, _


class BeneficiaryCategories(models.Model):
    _name = 'beneficiary.categories'
    _description = 'Beneficiary Categories'
    _rec_name = 'name'

    name = fields.Char(string='Name')
    group_guest = fields.Boolean(string=" Is Guest?")

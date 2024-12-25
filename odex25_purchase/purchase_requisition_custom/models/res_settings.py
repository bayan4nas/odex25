from odoo import fields, models


class ResSetting(models.TransientModel):
    _inherit = 'res.config.settings'


    chief_executive_officer = fields.Float(string='Chief Executive Officer', readonly=False, related="company_id.chief_executive_officer")
    direct_purchase = fields.Float(string='Direct Purchase Amount', readonly=False, related="company_id.direct_purchase")
    # exceptional_amount = fields.Float(string='Exceptional Amount', readonly=False, related="company_id.exceptional_amount")
    second_approve = fields.Integer(string='second approve', related="company_id.second_approve", readonly=False)
    purchase_budget = fields.Boolean(string='Purchase budget', related="company_id.purchase_budget", readonly=False)
    purchase_analytic_account = fields.Many2one('account.analytic.account', related="company_id.purchase_analytic_account", readonly=False)



class Company(models.Model):
    _inherit = 'res.company'

    second_approve = fields.Integer(string='second approve')
    purchase_budget = fields.Boolean(string='Purchase budget')
    purchase_analytic_account = fields.Many2one('account.analytic.account')
    # exceptional_amount = fields.Float(string='Exceptional Amount')
    chief_executive_officer = fields.Float(string='Exceptional Amount')
    direct_purchase = fields.Float(string='Direct Purchase Amount')
    general_supervisor_id = fields.Many2one(string='General Supervisor',comodel_name='hr.employee')






class VendorTypes(models.Model):
    _name = 'vendor.type'
    _description = 'vendor.type'

    name = fields.Char('Name',required=True)

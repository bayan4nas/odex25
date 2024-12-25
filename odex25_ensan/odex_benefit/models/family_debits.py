from random import randint
from odoo import fields, models, api, _


class FamilyDebits(models.Model):
    _name = 'family.debits'
    _description = "Family - Debits"


    loan_giver = fields.Many2one("loan.giver",string='Loan Giver')
    loan_amount = fields.Float(string='Loan Amount')
    loan_total_paid = fields.Float(string='Loan Total Paid')
    loan_remaining = fields.Float(string='Loan Remaining',compute='_compute_loan_remaining',store=True)
    monthly_installment = fields.Float(string='Monthly Installment')
    number_of_installments = fields.Integer(string='Number of installments')
    last_paid_amount = fields.Float(string='Last Paid Amount')
    last_paid_amount_date = fields.Date(string='Last Paid Amount Date')
    loan_start_date = fields.Date(string='Loan Start Date')
    loan_end_date = fields.Date(string='Loan End Date')
    loan_reason = fields.Many2one("loan.reason",string='Loan Reason')
    benefit_id = fields.Many2one("grant.benefit")
    loan_attach = fields.Binary(attachment=True,string='Loan Attach')
    description = fields.Char(string='Description')
    state = fields.Selection(string='Status', selection=[('accepted', 'Accepted'), ('refused', 'Refused')])

    def action_accept(self):
        self.state = 'accepted'

    def action_refuse(self):
        self.state = 'refused'

    @api.depends('loan_amount','loan_total_paid')
    def _compute_loan_remaining(self):
        for rec in self:
            rec.loan_remaining = rec.loan_amount - rec.loan_total_paid

    # @api.depends('loan_amount','number_of_installments')
    # def get_monthly_installment(self):
    #     for rec in self:
    #         if rec.loan_amount and rec.number_of_installments > 0 :
    #             rec.monthly_installment = rec.loan_amount / rec.number_of_installments
    #         else:
    #             rec.monthly_installment = 0


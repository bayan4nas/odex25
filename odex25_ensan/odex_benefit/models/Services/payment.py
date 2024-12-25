from odoo import fields, models, api


class BenefitServicesPayment(models.Model):
    _inherit = "account.payment"

    benefit_loan_id = fields.Many2one('benefit.loans')
    receive_benefit_loan_id = fields.Many2one('receive.benefit.loans')
    receive_food_basket = fields.Many2one('receive.food.basket')
    receive_zkat = fields.Many2one('benefit.zkat')

from odoo import models,fields


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    benefit_family_id = fields.Many2one(comodel_name='grant.benefit', string='Benefit Family')
    family_confirm_id = fields.Many2one(comodel_name='confirm.benefit.expense', string='Benefit Family')
    family_code = fields.Char(string='Family Code', related='benefit_family_id.code',readonly=True)

class AccountMove(models.Model):
    _inherit = 'account.move'
    family_confirm_id = fields.Many2one(comodel_name='confirm.benefit.expense', string='Benefit Family')
    payment_order_id = fields.Many2one(comodel_name='payment.orders', string='Payment Orders')

    benefit_family_ids = fields.Many2many(comodel_name='grant.benefit',relation='account_move_grant_family_rel',
    column1='move_id',column2='family_id', string='Benefit Family')
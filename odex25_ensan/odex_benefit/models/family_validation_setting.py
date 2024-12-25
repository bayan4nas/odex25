from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class FamilyValidationSetting(models.Model):
    _name = 'family.validation.setting'

    female_benefit_age = fields.Integer(string='Female Benefit Age')
    male_benefit_age = fields.Integer(string='Male Benefit Age')
    exceptional_age_scientific_specialty = fields.Integer(string='Exceptional Age Scientific Specialty')
    exceptional_age_medical_specialty = fields.Integer(string='Exceptional Age Medical Specialty')
    exceptional_age_has_disabilities = fields.Integer(string='Exceptional Age Has Disabilities')
    max_income_for_benefit = fields.Float(string='Max Income Benefit')
    mini_income_for_mother = fields.Float(string='Min Income Mother')
    max_income_for_mother = fields.Float(string='Max Income Mother')
    minor_siblings_age = fields.Integer(string='Minor Siblings Age')

    cash_expense = fields.Float(string='Cash Expense')
    cash_expense_account_id = fields.Many2one('account.account', string='Cash Expense Account',
                                              domain=[('deprecated', '=', False), ('internal_type', '=', 'other')])
    meal_expense = fields.Float(string='Meal Expense')
    meal_expense_account_id = fields.Many2one('account.account', string='Meal Expense Account',
                                              domain=[('deprecated', '=', False), ('internal_type', '=', 'other')])
    clothing_expense = fields.Float(string='Clothing Expense')
    clothing_expense_account_id = fields.Many2one('account.account', string='Clothing Expense Account',
                                                  domain=[('deprecated', '=', False), ('internal_type', '=', 'other')])

    benefit_category_ids = fields.Many2many(comodel_name='benefit.category',
                                            relation='benefit_category_family_validation_rel',
                                            column1='family_id', column2='categ_id', string='Benefit Categories')

    meal_partner_id = fields.Many2one('res.partner', string='Meal Partner')
    journal_id = fields.Many2one('account.journal', string='Journal')
    account_id = fields.Many2one('account.account',string='Expenses Account')

    @api.constrains('meal_expense_account_id', 'clothing_expense_account_id', 'cash_expense_account_id')
    def _constraint_amount_should_be_positive_if_account_selected(self):
        for rec in self:
            if rec.meal_expense_account_id:
                if rec.meal_expense <= 0:
                    raise ValidationError(_('Meal Expense should be positive if meal account selected'))
            if rec.clothing_expense_account_id:
                if rec.clothing_expense <= 0:
                    raise ValidationError(_('Clothing Expense should be positive if clothing account selected'))
            if rec.cash_expense_account_id:
                if rec.cash_expense <= 0:
                    raise ValidationError(_('Cash Expense should be positive if cash account selected'))

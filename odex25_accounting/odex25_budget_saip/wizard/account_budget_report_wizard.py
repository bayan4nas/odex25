# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.misc import format_date, formatLang


class BudgetReportWizard(models.TransientModel):
    _name = 'account.budget.report.wizard'
    _description = 'Budget Report'

    date_from = fields.Date('Date From')
    date_to = fields.Date('Date To')
    fiscalyear_id = fields.Many2one('account.fiscal.year', 'Fiscal Year')
    general_budget_id = fields.Many2one('account.budget.post', 'Budgetary Position')
    item_budget_id = fields.Many2many('item.budget', string='Budget Item')
    analytic_account_id = fields.Many2one('account.analytic.account', 'Analytic Account')

    @api.onchange('fiscalyear_id')
    def _onchange_fiscalyear_id(self):
        if self.fiscalyear_id:
            self.date_from = self.fiscalyear_id.date_from
            self.date_to = self.fiscalyear_id.date_to

    @api.onchange('general_budget_id')
    def _onchange_general_budget_id(self):
        if self.general_budget_id:
            return {'domain': {'item_budget_id': [('id', 'in', self.general_budget_id.item_budget_ids.ids)]}}

    def check_data(self):
        # if self.date_from and not self.date_to or not self.date_from and self.date_to:
        #     raise UserError(_('Choose Date From and Date To'))
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise UserError(_('Date From must be less than or equal Date To'))
        return {'form': (self.read()[0])}

    def print_report_pdf(self):
        datas = self.check_data()
        return self.env.ref('odex25_budget_saip.account_budget_report_action_pdf').report_action(self, data=datas)

    def print_report_xlsx(self):
        datas = self.check_data()
        return self.env.ref('odex25_budget_saip.account_budget_report_action_xlsx').report_action(self, data=datas)

    def print_report_html(self):
        datas = self.check_data()
        return self.env.ref('odex25_budget_saip.account_budget_report_action_html').report_action(self, data=datas)


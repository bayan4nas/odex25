# -*- coding: utf-8 -*-
from odoo import api, models, _


class AccountBudgetReport(models.AbstractModel):
    _name = 'report.odex25_budget_saip.account_budget_report'
    _description = "Budget Report"

    def get_selection_value(self, model, field, key):
        """Helper function to get the selection label for a given key."""
        return dict(self.env[model].fields_get([field], ['selection'])[field]['selection']).get(key)

    def get_item_type_name(self, item_budget):
        return self.get_selection_value('crossovered.budget.lines', 'item_type', item_budget.item_type)

    def get_period_name(self, item_budget):
        return self.get_selection_value('crossovered.budget.lines', 'period', item_budget.period)

    def get_result_domain(self, data):
        form = data['form']
        domain = [('date_from', '>=', form['date_from']), ('date_to', '<=', form['date_to']),
                  ('crossovered_budget_id.state', '=', 'done')]
        if form.get('fiscalyear_id'):
            domain.append(('crossovered_budget_id.fiscalyear_id', '=', form['fiscalyear_id'][0]))
        if form.get('general_budget_id'):
            domain.append(('general_budget_id', '=', form['general_budget_id'][0]))
        if form.get('item_budget_id'):
            domain.append(('item_budget_id', 'in', form['item_budget_id']))
        if form.get('analytic_account_id'):
            domain.append(('analytic_account_id', '=', form['analytic_account_id'][0]))

        return domain

    def accumulate_records(self, records):
        accumulated_data = {}
        for record in records:
            key = record.item_budget_id.id
            if key not in accumulated_data:
                accumulated_data[key] = {
                    'item_budget_id': record.item_budget_id,
                    'general_budget_id': record.general_budget_id,
                    'currency_id': record.currency_id,
                    'item_type': self.get_item_type_name(record),
                    'period': self.get_period_name(record),
                    'planned_amount': 0.0,
                    'additions': 0.0,
                    'transfer_debit': 0.0,
                    'transfer_credit': 0.0,
                    'cost_amount': 0.0,
                    'after_modification': 0.0,
                    'initial_reserve': 0.0,
                    'contract_reserve': 0.0,
                    'current_year_payment_contract': 0.0,
                    'contract_count': 0,
                    'financial_reserve': 0.0,
                    'current_year_payment': 0.0,
                    'previous_year_payment': 0.0,
                    'remain': 0.0,
                    'available_liquidity': 0.0,
                    'percentage': 0.0,
                }

            acc = accumulated_data[key]
            acc['planned_amount'] += record.planned_amount
            acc['additions'] += record.additions
            acc['transfer_debit'] += record.transfer_debit
            acc['transfer_credit'] += record.transfer_credit
            acc['cost_amount'] += record.cost_amount
            acc['after_modification'] += record.after_modification
            acc['initial_reserve'] += record.initial_reserve
            acc['contract_reserve'] += record.contract_reserve
            acc['current_year_payment_contract'] += record.current_year_payment_contract
            acc['contract_count'] += record.contract_count
            acc['financial_reserve'] += record.financial_reserve
            acc['current_year_payment'] += record.current_year_payment
            acc['previous_year_payment'] += record.previous_year_payment
            acc['remain'] += record.remain
            acc['available_liquidity'] += record.available_liquidity
            acc['percentage'] = max(acc['percentage'], record.percentage)  # Taking max percentage

        return list(accumulated_data.values())

    def get_records(self, data):
        domain = self.get_result_domain(data)
        records = self.env['crossovered.budget.lines'].search(domain).sorted(key=lambda r: r.general_budget_id.id)
        return self.accumulate_records(records)

    def get_labels(self):
        return [
            _('Item/Programme/Project number'),
            _('Name of The Item/Programme/Project'),
            _('Economic Classification'),
            _('Capital/Operating'),
            _('Annual/Non-Annual'),
            _('Original Credit'),
            _('Add-Ons'),
            _('Moved To (+)'),
            _('Copied From (-)'),
            _('Cost Amount'),
            _('Accreditation After Modification'),
            _('Initial Engagements'),
            _('Total Contract value'),
            _('Total Expenditure On Contracts To Date'),
            _('Total Number Of Associated Contracts'),
            _('Financial Reservations'),
            _('Current Year Outgoing'),
            _('Disbursed Until The End Of Last Year'),
            _('Available Accreditation'),
            _('Available Liquidity'),
            _('%')
        ]

    @api.model
    def _get_report_values(self, docids, data=None):
        records = self.get_records(data)
        labels = self.get_labels()
        form = data['form']
        date_from = form.get('date_from')
        date_to = form.get('date_to')
        return {
            'labels': labels,
            'records': records,
            'date_from': date_from,
            'date_to': date_to,
        }


class AccountBudgetReportXlsx(models.AbstractModel):
    _name = 'report.odex25_budget_saip.account_budget_report_xlsx'
    _description = "Budget Report"
    _inherit = 'report.report_xlsx.abstract'

    def get_selection_value(self, model, field, key):
        """Helper function to get the selection label for a given key."""
        return dict(self.env[model].fields_get([field], ['selection'])[field]['selection']).get(key)

    def get_item_type_name(self, item_budget):
        return self.get_selection_value('crossovered.budget.lines', 'item_type', item_budget.item_type)

    def get_period_name(self, item_budget):
        return self.get_selection_value('crossovered.budget.lines', 'period', item_budget.period)

    @api.model
    def generate_xlsx_report(self, workbook, data, objs):
        self = self.with_context(lang=self.env.user.lang)
        if not data:
            return
        AccountBudgetReport = self.env['report.odex25_budget_saip.account_budget_report']
        docs = AccountBudgetReport.get_records(data)
        sheet = workbook.add_worksheet(_('Account Budget Report'))
        if self.env.user.lang != 'en_US':
            sheet.right_to_left()

        format0 = workbook.add_format(
            {'bottom': True, 'bg_color': '#006666', 'right': True, 'left': True, 'top': True, 'bold': True,
             'align': 'center', 'font_color': 'white'})
        format1 = workbook.add_format({'align': 'center'})
        number_format = workbook.add_format(
            {'num_format': '#,##0.00', 'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'center'})
        percentage_format = workbook.add_format({'num_format': '0.00%', 'align': 'center'})

        sheet.set_column('A:A', 20)
        sheet.set_column('B:B', 40)
        sheet.set_column('N:N', 25)
        sheet.set_column('C:M', 15)
        sheet.set_column('O:T', 20)
        sheet.set_column('U:U', 10)

        # Write labels
        row = 0
        for idx, label in enumerate(AccountBudgetReport.get_labels()):
            sheet.write(row, idx, label, format0)

        # Write records
        row = 1
        for rec in docs:
            sheet.write(row, 0, rec['item_budget_id'].item_no, format1)
            sheet.write(row, 1, rec['item_budget_id'].name, format1)
            sheet.write(row, 2, rec['general_budget_id'].name, format1)
            sheet.write(row, 3, self.get_item_type_name(rec['item_budget_id']), format1)
            sheet.write(row, 4, self.get_period_name(rec['item_budget_id']), format1)
            sheet.write_number(row, 5, rec['planned_amount'], number_format)
            sheet.write_number(row, 6, rec['additions'], number_format)
            sheet.write_number(row, 7, rec['transfer_debit'], number_format)
            sheet.write_number(row, 8, rec['transfer_credit'], number_format)
            sheet.write_number(row, 9, rec['cost_amount'], number_format)
            sheet.write_number(row, 10, rec['after_modification'], number_format)
            sheet.write_number(row, 11, rec['initial_reserve'], number_format)
            sheet.write_number(row, 12, rec['contract_reserve'], number_format)
            sheet.write_number(row, 13, rec['current_year_payment_contract'], number_format)
            sheet.write_number(row, 14, rec['contract_count'], format1)
            sheet.write_number(row, 15, rec['financial_reserve'], number_format)
            sheet.write_number(row, 16, rec['current_year_payment'], number_format)
            sheet.write_number(row, 17, rec['previous_year_payment'], number_format)
            sheet.write_number(row, 18, rec['remain'], number_format)
            sheet.write_number(row, 19, rec['available_liquidity'], number_format)
            sheet.write_number(row, 20, rec['percentage'], percentage_format)
            row += 1

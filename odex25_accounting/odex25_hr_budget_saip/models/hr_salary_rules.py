# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import itertools as it
from operator import itemgetter
from odoo.exceptions import UserError, ValidationError


class AccountJournal(models.Model):
    _inherit = "account.journal"

    hr_journal = fields.Boolean(string='HR Journal Entries', default=False)
    commitee_expense = fields.Boolean(string="Commitee Expenses")



class HrSalaryScale(models.Model):
    _inherit = 'hr.payroll.structure'

    transfer_type = fields.Selection(selection_add=[('bill', 'Dues')])


class HrSalaryRules(models.Model):
    _inherit = 'hr.salary.rule'

    item_budget_id = fields.Many2one('item.budget', 'Budget Item')
    compensation_rule = fields.Boolean('Compensation Rule')

    def get_item_budget_id(self, emp_type):
        if not self.transfer_by_emp_type :  return self.item_budget_id
        account_mapping = self.account_ids.filtered(lambda a: a.emp_type_id.id == emp_type.id)
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!",account_mapping)
        for i in self.account_ids:
            print("##########################id",i.emp_type_id.id)
            print("##########################emp_type",emp_type.id)
            print("##########################item_budget_id",i.item_budget_id)
        # print("@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@2",account_mapping[0])
        # print("$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$",account_mapping[0].item_budget_id)
        return account_mapping[0].item_budget_id if account_mapping else False

class HrSalaryRuleAccount(models.Model):
    _inherit = 'hr.salary.rule.account'

    item_budget_id = fields.Many2one('item.budget', 'Budget Item')

class HrPayslipRun(models.Model):
    _inherit = 'hr.payslip.run'

    company_id = fields.Many2one('res.company', default=lambda self: self.env.user.company_id)

    @api.depends('salary_scale.transfer_type')
    def compute_type(self):
        if self.salary_scale.transfer_type in ['all', 'bill']:
            self.required_condition = True
        else:
            self.required_condition = False

    def new_merge_lists(self, l1, key, key2, key3):
        grupos = it.groupby(sorted(l1, key=itemgetter(key)), key=itemgetter(key, key2, key3))
        res = []
        for v, items in grupos:
            new_items = list(items)
            res.append({
                'name': v[0],
                'account_id': v[1],
                'item_budget_id': v[2],
                'price_unit': sum(dicc['price_unit'] for dicc in new_items),
            })
        return res

    def transfer(self):
        list_of_vals = []
        if self.salary_scale.transfer_type != 'bill':
            super(HrPayslipRun, self).transfer()
        else:
            total_of_list = []
            for line in self.slip_ids:
                emp_type = line.employee_id.get_emp_type_id()
                print("1111111111111111111111111111", line.employee_id.name)
                total_allow, total_ded, total_loan = 0.0, 0.0, 0.0
                total_list = []
                move_vals = dict()
                journal = self.journal_id

                if list_of_vals:
                    for item in list_of_vals:
                        if item.get('move') == journal.id:
                            move_vals = item
                            break
                for l in line.allowance_ids:
                    amount_allow = l.total
                    account = l.salary_rule_id.get_debit_account_id(emp_type)
                    # if not account:
                    #     raise ValidationError(_('Employee type is not exit in salary structure: {}').format(emp_type.name))
                    print("##########################l", l.name)
                    print("##########################account", account)
                    item_budget = l.salary_rule_id.get_item_budget_id(emp_type)
                    # if not item_budget:
                    #     raise ValidationError(_('Employee type is not exit in salary structure: {}').format(emp_type.name))
                    print("###########################333",item_budget)

                    budget_lines = item_budget.crossovered_budget_line.filtered(
                        lambda bl: bl.crossovered_budget_id.state == 'done' and fields.Date.from_string(
                            bl.date_from) <= fields.Date.from_string(self.date_end) <= fields.Date.from_string(
                            bl.date_to))
                    if not budget_lines:
                        raise ValidationError(_('No budget for this service: {} - {}').format(
                            l.salary_rule_id.name, item_budget.name))

                    general_budget = item_budget.crossovered_budget_line.filtered(
                        lambda bl: bl.general_budget_id in self.env['account.budget.post'].search([]).filtered(
                            lambda post: account in post.account_ids))

                    if not general_budget:
                        raise ValidationError(_('No budget for this account: {}').format(account.name))
                    total_list.append({
                        'name': l.name,
                        'price_unit': amount_allow,
                        'account_id': account.id,
                        'item_budget_id':item_budget.id,
                    })

                    total_allow += amount_allow
                for ded in line.deduction_ids:
                    amount_ded = -ded.total
                    item_budget = ded.salary_rule_id.get_item_budget_id(emp_type)
                    account = ded.salary_rule_id.get_credit_account_id(emp_type)
                    # if not account:
                    #     raise ValidationError(_('Employee type is not exit in salary structure: {}').format(emp_type.name))
                    # if not item_budget:
                    #     raise ValidationError(_('Employee type is not exit in salary structure: {}').format(emp_type.name))
                    budget_lines = item_budget.crossovered_budget_line.filtered(
                        lambda bl: bl.crossovered_budget_id.state == 'done' and fields.Date.from_string(
                            bl.date_from) <= fields.Date.from_string(self.date_end) <= fields.Date.from_string(
                            bl.date_to))
                    if not budget_lines:
                        raise ValidationError(_('No budget for this service: {} - {}').format(
                            ded.salary_rule_id.name, item_budget.name))

                    general_budget = item_budget.crossovered_budget_line.filtered(
                        lambda bl: bl.general_budget_id in self.env['account.budget.post'].search([]).filtered(
                            lambda post: account in post.account_ids))
                    if not general_budget:
                        raise ValidationError(_('No budget for this account: {}').format(account.name))
                    total_list.append({
                        'name': ded.name,
                        'price_unit': amount_ded,
                        'account_id': account.id,
                        'item_budget_id': item_budget.id,

                    })
                    total_ded += amount_ded

                if not move_vals:
                    move_vals.update({'move': journal.id, 'list_ids': total_list})
                    list_of_vals.append(move_vals)
                else:
                    new_list = move_vals.get('list_ids')
                    new_list.extend(total_list)
                    move_vals.update({'list_ids': new_list})

            for record in list_of_vals:
                new_record_list = record.get('list_ids') + [d for d in total_of_list if
                                                            d['journal_id'] == record.get('move')]
                merged_list = self.new_merge_lists(new_record_list, 'name', 'account_id', 'item_budget_id')
                record_final_item = merged_list

                move = self.env['account.move'].create({
                    'state': 'draft',
                    'hr_operation': True,
                    'journal_id': record.get('move'),
                    'partner_id': self.company_id.partner_id.id,
                    'move_type': 'in_invoice',
                    'date': fields.Date.today(),
                    'invoice_date': fields.Date.today(),
                    'ref': self.name,
                    'invoice_line_ids': [(0, 0, item) for item in record_final_item]
                })
                self.move_id = move.id

        for line in self.slip_ids:
            payslip = self.env['hr.payslip'].search([('state', '=', line.state)])
            if payslip:
                line.write({'state': 'transfered'})
        self.write({'state': 'transfered'})

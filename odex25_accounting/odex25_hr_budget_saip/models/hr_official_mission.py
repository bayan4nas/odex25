# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime, date, timedelta
from odoo.exceptions import UserError, ValidationError


class HrOfficialMission(models.Model):
    _inherit = "hr.official.mission"

    def approve(self):
        # check if there is dealing with financial
        self.employee_ids.chick_not_overtime()
        if self.employee_ids:
            if self.mission_type.journal_id:
                if self.Training_cost > 0:
                    invoice = self.env['account.move'].create({
                        'partner_id': self.partner_id.id,
                        'journal_id': self.mission_type.journal_id.id,
                        'hr_operation': True,
                        'state': 'draft',
                        'move_type': 'in_invoice',
                        'date': self.date,
                        'ref': _('Training Cost for Course Name %s ') % self.course_name.name,
                        'invoice_line_ids': [(0, 0, {
                            'name': 'Training Cost for Course Name %s Training Center %s' % (
                                self.course_name.name, self.partner_id.name),
                            'account_id': self.partner_id.property_account_receivable_id.id,
                            'item_budget_id': self.mission_type.allowance_id.item_budget_id.id,
                            'quantity': 1.0,
                            'price_unit': self.Training_cost,
                        })],
                    })

                    self.Tra_cost_invo_id = invoice.id

                for item in self.employee_ids:
                    budget_lines = self.mission_type.allowance_id.item_budget_id.crossovered_budget_line.filtered(
                        lambda bl: bl.crossovered_budget_id.state == 'done' and fields.Date.from_string(
                            bl.date_from) <= fields.Date.from_string(self.date) <= fields.Date.from_string(
                            bl.date_to))
                    if not budget_lines:
                        raise ValidationError(_('No budget for this service: {} - {}').format(
                            self.mission_type.allowance_id.name, self.mission_type.allowance_id.item_budget_id.name))

                    # general_budget = self.official_mission.item_budget_id.crossovered_budget_line.filtered(
                    #     lambda bl: bl.general_budget_id in self.env['account.budget.post'].search([]).filtered(
                    #         lambda post: self.mission_type.allowance_id.rule_debit_account_id in post.account_ids))
                    # if not general_budget:
                    #     raise ValidationError(_('No budget for this account: {}').format(self.mission_type.allowance_id.rule_debit_account_id.name))
                    if item.amount > 0.0:
                        invoice_line_ids = [(0, 0, {
                            'name': self.official_mission.name,
                            'account_id': self.mission_type.allowance_id.rule_debit_account_id.id,
                            'analytic_account_id': self.mission_type.allowance_id.analytic_account_id.id,
                            'item_budget_id': self.mission_type.allowance_id.item_budget_id.id,
                            'quantity': 1.0,
                            'price_unit': item.amount,
                        })]
                        bill = self.env['account.move'].create({
                            'partner_id': item.employee_id.user_id.partner_id.id,
                            'journal_id': self.mission_type.journal_id.id,
                            'hr_operation': True,
                            'invoice_line_ids': invoice_line_ids,
                            'date': self.date,
                            'invoice_date': self.date,
                            'state': 'draft',
                            'move_type': 'in_invoice',
                            'ref': _("Official mission for employee %s") % item.employee_id.name,
                            # 'narration': "%s - %s" % (self.sudo().employee_id.name, rec.school),
                        })
                        item.account_move_id = bill.id

            else:
                raise ValidationError(
                    _('You do not have account or journal in mission type "%s" ') % self.mission_type.name)

        # for item in self:
            # create ticket request from all employee
        if self.issuing_ticket == 'yes':
            for emp in self.employee_ids:
                self.env['hr.ticket.request'].create({
                        'employee_id': emp.employee_id.id,
                        'mission_request_id': self.id,
                        'mission_check': True,
                        'request_for': self.ticket_cash_request_for,
                        'request_type': self.ticket_cash_request_type.id,
                        'cost_of_tickets': self.get_ticket_cost(emp.employee_id),
                        'destination': self.destination.id,
                })
            # move invoice  training cost our trining center


        self.state = "approve"
        if self.mission_type.work_state and self.mission_type.duration_type == 'days':
            for emp in self.employee_ids:
                if emp.date_to and emp.date_from:
                    if emp.date_to >= fields.Date.today() >= emp.date_from:
                        emp.employee_id.write({'work_state': self.mission_type.work_state, 'active_mission_id': emp.id})
        self.call_cron_function()

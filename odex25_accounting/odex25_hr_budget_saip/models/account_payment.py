# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
import ast
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from lxml import etree
import json


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    skip_budget = fields.Boolean()

    # def action_budget_management(self):
    #     super(AccountPayment, self).action_budget_management()
    #     if self.item_budget_ids and not self.skip_budget:
    #         # Check budget availability for each payment line
    #         for line in self.item_budget_ids:  # Assuming `payment_line_ids` relates to 'account.payment.line'
    #             if line.remaining_available_liquidity < line.amount:
    #                 raise ValidationError(
    #                     _("Insufficient budget for the line with item budget %s") % line.item_budget_id.name)
    #         # Proceed with the normal budget management logic if no validation error is raised
    #         self.state = 'head_accounting'


# class AccountPaymentLine(models.Model):
#     _inherit = 'account.payment.line'
#
#     remaining_item_budget = fields.Float("Available Liquidity", compute="_compute_budget")
#     remaining_available_liquidity = fields.Float("Remain Balance", compute="_compute_budget")
#
#     def _compute_budget(self):
#         budget_tracking = {}  # Dictionary to track remaining available liquidity per item_budget_id
#
#         for rec in self:
#             rec.remaining_item_budget = 0.00  # Reset to 0 initially
#             rec.remaining_available_liquidity = 0.00  # Reset to 0 initially
#
#             if rec.item_budget_id:
#                 budget_id = rec.item_budget_id.id
#
#                 budget_lines = rec.item_budget_id.crossovered_budget_line.filtered(
#                     lambda x: x.crossovered_budget_id.state == 'done'
#                               and x.date_from and x.date_to and rec.payment_id.date  # Ensure date_from and date_to are not None
#                               and fields.Date.from_string(
#                         x.date_from) <= rec.payment_id.date <= fields.Date.from_string(x.date_to)
#                 )
#                 if budget_lines:
#                     # Set remaining_item_budget once based on the first budget line's available liquidity
#                     rec.remaining_item_budget = abs(budget_lines[0].available_liquidity)
#                     # if rec.amount > rec.remaining_item_budget:
#                     #     r
#
#                     # Initialize tracking for the item_budget_id if not already tracked
#                     if budget_id not in budget_tracking:
#                         budget_tracking[budget_id] = rec.remaining_item_budget  # Start with the full available liquidity
#
#                     # Set the remaining available liquidity based on the cumulative tracked value minus the current amount
#                     rec.remaining_available_liquidity = budget_tracking[budget_id] - rec.amount
#
#                     # Update the cumulative tracking budget after subtracting the current amount
#                     budget_tracking[budget_id] -= rec.amount


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    product_id = fields.Many2one('product.product', string='Product', ondelete='restrict',)

    @api.onchange('move_id', 'product_id', 'move_id.product_category_ids')
    def _onchange_move_id_set_product_domain(self):
        move = self.move_id
        if not move:
            default_move_id = self.env.context.get('default_move_id')
            if default_move_id:
                move = self.env['account.move'].browse(default_move_id)
        categ_ids = []
        if move and move.product_category_ids:
            for c in move.product_category_ids:
                categ_ids.append(c._origin.id)
        if move.move_type == 'in_receipt' and categ_ids:
            return {
                'domain': {
                    'product_id': [('categ_id', 'in', categ_ids)]

                }
            }


class AccountMove(models.Model):
    _inherit = 'account.move'

    purpose = fields.Char()
    is_recipte  = fields.Boolean()
    journal_id = fields.Many2one('account.journal', string='Journal', required=False, readonly=True,  states={'draft': [('readonly', False)]},  check_company=True, domain="[('id', 'in', suitable_journal_ids)]", default=None)
    product_category_ids = fields.Many2many('product.category', string='Items Categories')
    note = fields.Text(string="Note")
    is_commite_expenses = fields.Selection(string=' Commitee Expenses?', selection=[('yes', 'Yes'), ('no', 'No')])
    employee_id = fields.Many2one('hr.employee',string='Employee',default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1), readonly=True,)
    department_id = fields.Many2one('hr.department',string='Department',compute='_compute_department_id',store=True,readonly=True,)
    state_history = fields.Text(string="State History", default='[]')  # Store the history as a JSON string

    @api.depends('employee_id')
    def _compute_department_id(self):
        for rec in self:
            rec.department_id = rec.employee_id.department_id.id if rec.employee_id and rec.employee_id.department_id else False

    @api.model
    def search(self, args, **kwargs):
        """
        Override the search method to restrict records based on user group and
        whether the journal is marked as a committee expense.
        """
        if   self.env.user.has_group('odex25_hr_budget_saip.group_account_expenses_user'):
            # Allow users to see only their own records related to committee expense journals
            args += [
                ('create_uid', '=', self.env.uid),
            ]
        elif  self.env.user.has_group('odex25_hr_budget_saip.group_account_expenses_manager'):
            # Find the employee record for the current user
            employee = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
            if employee and employee.department_id:
                # Allow managers to see records in their own department related to committee expense journals
                args += [
                    ('department_id', '=', employee.department_id.id)
                ]
        return super(AccountMove, self).search(args, **kwargs)

    # @api.model
    # def create(self, vals):
    #     if not vals.get('journal_id'):
    #         raise ValidationError(_("⚠️ Please note: You must select a journal."))
    #     return super().create(vals)



    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super().fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
        doc = etree.XML(res['arch'])
        current_action_id = self.env.context.get('params', {}).get('action')
        expected_action_id = self.env.ref('odex25_hr_budget_saip.action_account_move_commitee_expense').id
        if view_type == 'form' and current_action_id == expected_action_id:
            nodes = doc.xpath("//field[@name='journal_id']")
            for node in nodes:
                node.set('domain', "[('id', 'in', suitable_journal_ids),('commitee_expense','=',True)]")
                node.set('widget', '')

        for node in doc.xpath("//field[@name='invoice_payment_term_id']"):
                modifiers = json.loads(node.get("modifiers"))
                modifiers['readonly'] = [('state', 'not in', ['accounting_department','budget_management'])]
                node.set("modifiers", json.dumps(modifiers))
        for node in doc.xpath("//field[@name='date']"):
                modifiers = json.loads(node.get("modifiers"))
                modifiers['readonly'] = [('state', 'not in', ['accounting_department','budget_management'])]
                node.set("modifiers", json.dumps(modifiers))
        # for node in doc.xpath("//field[@name='journal_id']"):
        #     modifiers = json.loads(node.get("modifiers", '{}'))
        #     if 'required' in modifiers:
        #         del modifiers['required']
        #     node.set("modifiers", json.dumps(modifiers))
        res['arch'] = etree.tostring(doc)
        return res


    # old_state = fields.Selection(related="state", store=True)


    def action_open_return_state_wizard(self):
        return {
            "type": "ir.actions.act_window",
            "name": _("Open Return State Wizard"),
            "res_model": "return.state.account",
            "view_mode": "form",
            "target": "new",
            "context": {"default_account_id": self.id},
        }
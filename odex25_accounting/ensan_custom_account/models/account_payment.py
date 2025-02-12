# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields , api , _
from odoo.exceptions import UserError, ValidationError
from odoo.tools.misc import format_date, formatLang



class AccountPayment(models.Model):
    _inherit = "account.payment"

    partner_type = fields.Selection([
        ('customer', 'Customer'),
        ('supplier', 'Vendor'),
        ('GL', 'GL'),  
    ], default='customer', tracking=True, required=True)
    destination_account_id = fields.Many2one(
        comodel_name='account.account',
        string='Destination Account',
        compute='_compute_destination_account_id',
        check_company=True)

    def _prepare_payment_display_name(self):
        res = super()._prepare_payment_display_name()
        '''
        Hook method for inherit
        When you want to set a new name for payment, you can extend this method
        '''
        res['outbound-GL'] = _('Disbursement Directly GL')
        res['inbound-GL'] = _('Collect Directly GL')
        return res

    @api.onchange('partner_type','partner_id','payment_type')
    def get_destination_account_id(self):
        print('journal >>>>>>>>>>>>>>', self.journal_id.name)

        if self.partner_type == 'customer':
            domain = [('user_type_id.type', 'in', ('receivable', 'payable')), ('company_id', '=', self.company_id.id)]
        elif self.partner_type == 'supplier':
            domain = [('user_type_id.type', 'in', ('receivable', 'payable')), ('company_id', '=', self.company_id.id)]
        elif self.partner_type == 'GL':
            domain = [('user_type_id.type', 'not in', ('receivable', 'payable','view','liquidity')), ('company_id', '=', self.company_id.id)]
        else:
            domain = [('user_type_id.type', 'not in', ('receivable', 'payable')), ('company_id', '=', self.company_id.id)]
        return {'domain': {'destination_account_id': domain}}

    @api.onchange('journal_id', 'partner_id', 'partner_type', 'is_internal_transfer')
    @api.depends('journal_id', 'partner_id', 'partner_type', 'is_internal_transfer')
    def _compute_destination_account_id(self):
        for rec in self:
            if rec.destination_account_id and rec.partner_type == 'GL':
                return super()._compute_destination_account_id()
        print('self >>>>>>>>>>>>>>', self)
        for pay in self:
            if pay.partner_type == 'GL' and not pay.destination_account_id:
                domain = [('user_type_id.type', 'not in', ('receivable', 'payable','view','liquidity')), ('company_id', '=', self.company_id.id)]
                pay.destination_account_id = self.env['account.account'].search(domain, limit=1)

    def _synchronize_from_moves(self, changed_fields):
        ''' Update the account.payment regarding its related account.move.
        Also, check both models are still consistent.
        :param changed_fields: A set containing all modified fields on account.move.
        '''
        if self._context.get('skip_account_move_synchronization'):
            return

        for pay in self.with_context(skip_account_move_synchronization=True):

            # After the migration to 14.0, the journal entry could be shared between the account.payment and the
            # account.bank.statement.line. In that case, the synchronization will only be made with the statement line.
            if pay.move_id.statement_line_id:
                continue

            move = pay.move_id
            move_vals_to_write = {}
            payment_vals_to_write = {}

            if 'journal_id' in changed_fields:
                if pay.journal_id.type not in ('bank', 'cash'):
                    raise UserError(_("A payment must always belongs to a bank or cash journal."))

            if 'line_ids' in changed_fields:
                all_lines = move.line_ids
                liquidity_lines, counterpart_lines, writeoff_lines = pay._seek_for_lines()
                print("liquidity_lines >>>", liquidity_lines)
                print("counterpart_lines >>>", counterpart_lines)
                print("Journal ID:", self.journal_id)
                print("Journal Default Account:", self.journal_id.default_account_id)
                print("Journal Payment Debit Account:", self.journal_id.payment_debit_account_id)
                print("Journal Payment Credit Account:", self.journal_id.payment_credit_account_id)

                if len(liquidity_lines) != 1 or (len(counterpart_lines) != 1 and pay.partner_type not in ['GL']):
                    print('error >>>>>>>>>>>>>')
                    raise UserError(_(
                        "The journal entry %s reached an invalid state relative to its payment.\n"
                        "To be consistent, the journal entry must always contain:\n"
                        "- one journal item involving the outstanding payment/receipts account.\n"
                        "- one journal item involving a receivable/payable account.\n"
                        "- optional journal items, all sharing the same account.\n\n"
                    ) % move.display_name)

                if writeoff_lines and len(writeoff_lines.account_id) != 1:
                    raise UserError(_(
                        "The journal entry %s reached an invalid state relative to its payment.\n"
                        "To be consistent, all the write-off journal items must share the same account."
                    ) % move.display_name)

                if any(line.currency_id != all_lines[0].currency_id for line in all_lines):
                    raise UserError(_(
                        "The journal entry %s reached an invalid state relative to its payment.\n"
                        "To be consistent, the journal items must share the same currency."
                    ) % move.display_name)

                if any(line.partner_id != all_lines[0].partner_id for line in all_lines):
                    raise UserError(_(
                        "The journal entry %s reached an invalid state relative to its payment.\n"
                        "To be consistent, the journal items must share the same partner."
                    ) % move.display_name)

                print('payment_vals_to_write >>>>>>>>>>>', payment_vals_to_write)
                print('move_vals_to_write >>>>>>>>>>>', move_vals_to_write)

                if not pay.is_internal_transfer:
                    if counterpart_lines.account_id.user_type_id.type == 'receivable':
                        payment_vals_to_write['partner_type'] = 'customer'
                    elif counterpart_lines.account_id.user_type_id.type == 'payable':
                        payment_vals_to_write['partner_type'] = 'supplier'
                    else:
                        payment_vals_to_write['partner_type'] = 'GL'

                liquidity_amount = liquidity_lines.amount_currency

                move_vals_to_write.update({
                    'currency_id': liquidity_lines.currency_id.id,
                    'partner_id': liquidity_lines.partner_id.id,
                })
                payment_vals_to_write.update({
                    'amount': abs(liquidity_amount),
                    'currency_id': liquidity_lines.currency_id.id,
                    'destination_account_id': counterpart_lines.account_id.id,
                    'partner_id': liquidity_lines.partner_id.id,
                })
                if liquidity_amount > 0.0:
                    payment_vals_to_write.update({'payment_type': 'inbound'})
                elif liquidity_amount < 0.0:
                    payment_vals_to_write.update({'payment_type': 'outbound'})

            move.write(move._cleanup_write_orm_values(move, move_vals_to_write))
            pay.write(move._cleanup_write_orm_values(pay, payment_vals_to_write))

    def _seek_for_lines(self):
        self.ensure_one()

        liquidity_lines = self.env['account.move.line']
        counterpart_lines = self.env['account.move.line']
        writeoff_lines = self.env['account.move.line']

        print(">>>> Checking Move Lines for Payment:", self.move_id.name)
        print(">>>> Journal Default Account:", self.journal_id.default_account_id)
        print(">>>> Journal Payment Debit Account:", self.journal_id.payment_debit_account_id)
        print(">>>> Journal Payment Credit Account:", self.journal_id.payment_credit_account_id)

        for line in self.move_id.line_ids:
            print("Line:", line.name, "| Account:", line.account_id.name, "| Type:", line.account_id.internal_type)

            if line.account_id in (
                    self.journal_id.default_account_id,
                    self.journal_id.payment_debit_account_id,
                    self.journal_id.payment_credit_account_id,
            ):
                liquidity_lines += line
            elif line.account_id.internal_type in (
            'receivable', 'payable') or line.account_id == line.company_id.transfer_account_id:
                counterpart_lines += line
            else:
                writeoff_lines += line

        print("Final Liquidity Lines:", liquidity_lines)
        print("Final Counterpart Lines:", counterpart_lines)
        print("Final Writeoff Lines:", writeoff_lines)

        return liquidity_lines, counterpart_lines, writeoff_lines

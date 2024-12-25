# -*- coding: utf-8 -*-
from odoo import models, fields, api, _



class AccountVoucherInherit(models.Model):
    _inherit = "account.voucher"

    state = fields.Selection(selection_add=[('board representative','Board Representative'),('done','Done')])

    def board_representative_action(self):
        self.state = 'board representative'
    #
    def action_done(self):
        self.write({'state': 'done'})
    #
    def proforma_action(self):
        self.write({'state': 'proforma'})


    # @api.multi
    # @api.depends('tax_correction', 'line_ids.price_subtotal')
    # def _compute_total(self):
    #     tax_calculation_rounding_method = self.env.user.company_id.tax_calculation_rounding_method
    #     for voucher in self:
    #         total = 0
    #         tax_amount = 0
    #         tax_lines_vals_merged = {}
    #         for line in voucher.line_ids:
    #             if line.tax_ids:
    #                 tax_info = line.tax_ids.compute_all(line.price_unit, voucher.currency_id, line.quantity,
    #                                                     line.product_id, voucher.partner_id)
    #                 if tax_calculation_rounding_method == 'round_globally':
    #                     total += tax_info.get('total_excluded', 0.0)
    #                     for t in tax_info.get('taxes', False):
    #                         key = (
    #                             t['id'],
    #                             t['account_id'],
    #                         )
    #                         if key not in tax_lines_vals_merged:
    #                             tax_lines_vals_merged[key] = t.get('amount', 0.0)
    #                         else:
    #                             tax_lines_vals_merged[key] += t.get('amount', 0.0)
    #                 else:
    #                     total += tax_info.get('total_included', 0.0)
    #                     tax_amount += sum([t.get('amount', 0.0) for t in tax_info.get('taxes', False)])
    #             elif line.tax_ids_custom:
    #                 tax_info = line.tax_ids_custom.compute_all(line.price_unit, voucher.currency_id, line.quantity,
    #                                                     line.product_id, voucher.partner_id)
    #                 if tax_calculation_rounding_method == 'round_globally':
    #                     total += tax_info.get('total_excluded', 0.0)
    #                     for t in tax_info.get('taxes', False):
    #                         key = (
    #                             t['id'],
    #                             t['account_id'],
    #                         )
    #                         if key not in tax_lines_vals_merged:
    #                             tax_lines_vals_merged[key] = t.get('amount', 0.0)
    #                         else:
    #                             tax_lines_vals_merged[key] += t.get('amount', 0.0)
    #                 else:
    #                     total += tax_info.get('total_included', 0.0)
    #                     tax_amount += sum([t.get('amount', 0.0) for t in tax_info.get('taxes', False)])
    #         if tax_calculation_rounding_method == 'round_globally':
    #             tax_amount = sum([voucher.currency_id.round(t) for t in tax_lines_vals_merged.values()])
    #             voucher.amount = total + tax_amount + voucher.tax_correction
    #         else:
    #             voucher.amount = total + voucher.tax_correction
    #         voucher.tax_amount = tax_amount



class AccountVoucherLineInherit(models.Model):
    _inherit = "account.voucher.line"

    # tax_ids_custom = fields.Many2many('account.tax', string='Tax Custom', help="Only for tax excluded from price")

    # @api.one
    # @api.depends('price_unit', 'tax_ids','tax_ids_custom', 'quantity', 'product_id', 'voucher_id.currency_id')
    # def _compute_subtotal(self):
    #     self.price_subtotal = self.quantity * self.price_unit
    #     if self.tax_ids:
    #         taxes = self.tax_ids.compute_all(self.price_unit, self.voucher_id.currency_id, self.quantity,
    #                                          product=self.product_id, partner=self.voucher_id.partner_id)
    #         self.price_subtotal = taxes['total_excluded']
    #     elif self.tax_ids_custom:
    #         taxes_custom = self.tax_ids_custom.compute_all(self.price_unit, self.voucher_id.currency_id, self.quantity,
    #                                                        product=self.product_id, partner=self.voucher_id.partner_id)
    #         self.price_subtotal = taxes_custom['total_excluded']







# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class SaleOrder(models.Model):
    _inherit = "sale.order"

    project_invoice_count = fields.Integer(string='Project Invoices', compute='_compute_project_inv_ids')


    def _prepare_invoice(self):
        self.ensure_one()
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        if self.project_ids.type == 'revenue':
            invoice_vals['journal_id'] = self.env['account.move'].with_context(default_move_type='out_invoice')._get_default_journal().id
            invoice_vals['move_type'] =  'out_invoice'
        elif self.project_ids.type == 'expense':
            invoice_vals['journal_id'] = self.env['account.move'].with_context(default_move_type='in_invoice')._get_default_journal().id
            invoice_vals['move_type'] = 'in_invoice'
        invoice_vals['invoice_date_due'] = self._context.get('due_date')
        invoice_vals['sale_order_id'] = self.id
        return invoice_vals

    @api.depends('project_ids')
    def _compute_project_inv_ids(self):
        for order in self:
            project_invoice_count = self.env['project.invoice'].sudo().search([('project_id', 'in', order.project_ids.ids)])
            order.project_invoice_count = len(project_invoice_count)

    def action_view_project_invoice(self):
        self.ensure_one()
        action = {
            'type': 'ir.actions.act_window',
            'domain': [('project_id', 'in', self.project_ids.ids)],
            'context': {'create': False},
            'view_mode': 'tree,form',
            'name': _('Projects Invoices'),
            'res_model': 'project.invoice',
        }
        return action

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    phase_qty = fields.Float(string='Quantity', digits='Product Unit of Measure')

    project_invoiceline_ids = fields.One2many('project.invoice.line', 'order_line_id', 'Invoice Line')

    def _prepare_invoice_line(self, **optional_values):

        vals = super(SaleOrderLine, self)._prepare_invoice_line()
        vals['quantity'] = self.phase_qty if self.is_downpayment == False else self.qty_to_invoice
        vals['analytic_account_id'] = self._context.get('analytic_account_id')
        return vals

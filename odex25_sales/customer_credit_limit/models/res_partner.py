# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from datetime import datetime, timedelta


class ResPartner(models.Model):
    _inherit = "res.partner"

    
    credit_limit = fields.Float(string='Customer Credit Limit', tracking=True)

    
    block = fields.Boolean(string='Block From Sale', compute='_compute_sale_block')

    allow = fields.Boolean(string='Allow Sale',groups='sales_team.group_sale_manager', tracking=True)

    
    due_days = fields.Float(string='Days To Pay', default=30.0, tracking=True)

    @api.depends('due_days','invoice_ids')
    def _compute_sale_block(self):
        '''this functin search for partner related open inovices with due date,
        to determine whether to block customer from making sale or not'''

        for rec in self:
            rec.block = False

            if rec.due_days > 0 :
                today = datetime.now().date()
                date = today - timedelta(days=rec.due_days)
                invoices = rec.invoice_ids.filtered(lambda r: r.invoice_date_due and r.invoice_date_due <= date and r.move_type =='out_invoice' and r.state == 'posted')

                if invoices:
                    rec.block = True



# -*- coding: utf-8 -*-

from odoo import models, fields


class ProjectInvoice(models.Model):
    _inherit = "project.invoice"
    is_petty_paid = fields.Boolean(string='Paid by Petty Cash', default=False)

    def create_invoice(self):
        res = super(ProjectInvoice, self).create_invoice()
        self.invoice_id.is_petty_paid = self.is_petty_paid
        return res

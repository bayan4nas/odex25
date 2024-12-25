# -*- coding: utf-8 -*-
from odoo import models, fields, api,_

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    partner_type = fields.Selection(selection=[('cash','Cash'),('postpaid','Post Paid')])
    journal_id = fields.Many2one('account.journal', 'Partner Type')



    @api.onchange('journal_id')
    def onchange_journal_id(self):
        self.partner_type = self.journal_id.partner_type

    @api.onchange('partner_id')
    def onchange_partner_get_journal(self):
        self.journal_id = self.partner_id.journal_id.id


    def _prepare_invoice(self):

        res = super(SaleOrder, self)._prepare_invoice()

        res.update({'journal_id': self.journal_id.id})

        return res

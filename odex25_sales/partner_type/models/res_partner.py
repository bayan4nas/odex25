# -*- coding: utf-8 -*-

from odoo import models,fields,api,_
from odoo.exceptions import ValidationError

class Partner(models.Model):
    _inherit = 'res.partner'

    partner_type = fields.Selection(selection=[('cash','Cash'),('postpaid','Post Paid')])
    journal_id = fields.Many2one('account.journal', 'Partner Type')
    state = fields.Selection(selection=[('waiting','Waiting Approve'),('approved','Approved')],default='waiting')

    def action_approve(self):
        for rec in self:
            rec.write({'state':'approved'})


    def action_set_waiting(self):

        for rec in self:
            rec.write({'state': 'waiting'})


    @api.onchange('journal_id')
    def onchange_journal_id(self):
        self.partner_type = self.journal_id.partner_type





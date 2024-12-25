# -*- coding: utf-8 -*-
import base64
import re
import calendar

import logging
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import exception_to_unicode
from odoo import models, fields, api, exceptions, tools, _


_logger = logging.getLogger(__name__)

class TransferContract(models.Model):
    _name = 'transfer.contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Contract Transfer"
    _order = "id desc"

    name = fields.Char(string="No.", default="/")
    contract_id = fields.Many2one('rental.contract', string='Rental Contract')
    date = fields.Date(string='Transfer Date')
    current_partner_id = fields.Many2one('res.partner',related="contract_id.partner_id", string='Current Renter')
    partner_id = fields.Many2one('res.partner', string='Renter',domain=[('is_tenant', '=', True)])
    state = fields.Selection([('draft', 'Draft'),
                              ('submit', 'Submit'),
                              ('review', 'Review'),
                              ('confirm', 'Confirmed'),
                              ('cancel', 'Cancelled')], string='Status', default='draft')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    date_from = fields.Date(string='Contract Start Date', related='contract_id.date_from')
    date_to = fields.Date(string='Contract End Date', related='contract_id.date_to')
    property_id = fields.Many2one('internal.property', related="contract_id.property_id", string="Property")
    unit_ids = fields.Many2many('re.unit', related="contract_id.unit_ids", string="Unit")

    @api.constrains('date')
    def check_transfer_date(self):
        if self.date_from and self.date_to and self.date:
            start_date = datetime.strptime(datetime.strftime(self.date_from, '%Y-%m-%d'), '%Y-%m-%d').date()
            end_date = datetime.strptime(datetime.strftime(self.date_to, '%Y-%m-%d'), '%Y-%m-%d').date()
            date = datetime.strptime(datetime.strftime(self.date, '%Y-%m-%d') , '%Y-%m-%d').date()
            if date > end_date or date < start_date:
                raise exceptions.ValidationError(
                    _('Transfer Date should be greater than Start date and less Than End date of the contract'))

    def action_confirm(self):
        line_ids = []
        if self.date:
            line_id = self.env['rent.payment'].search(
                [('contract_id', '=', self.contract_id.id), ('due_date', '<=', self.date)],
                order="due_date desc", limit=1)
            if line_id.state == 'due':
                raise exceptions.ValidationError(
                    _("You cannot do this operation, there are payment for the old renter must be paid"))
        self.contract_id.write({'partner_id': self.partner_id.id})
        return self.write({'state': 'confirm'})

    def action_review(self):
        return self.write({'state': 'review'})

    def action_reset(self):
        return self.write({'state': 'draft'})

    def action_cancel(self):
        return self.write({'state': 'cancel'})

    def action_submit(self):
        if self.date:
            line_id = self.env['rent.payment'].search(
                [('contract_id', '=', self.contract_id.id), ('due_date', '<=', self.date)],
                order="due_date desc", limit=1)
            if line_id.state == 'due':
                raise exceptions.ValidationError(
                    _("You cannot do this operation, there are payment for the old renter must be paid"))
            self.name = self.env['ir.sequence'].next_by_code('transfer.contract') or '/'
        return self.write({'state': 'submit'})

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise exceptions.ValidationError(_("You can not delete record"))
        return super(TransferContract, self).unlink()

    @api.constrains('current_partner_id', 'partner_id')
    def check_renter(self):
        if self.partner_id and self.current_partner_id:
            if self.partner_id.id == self.current_partner_id.id:
                raise exceptions.ValidationError(_("The Current Renter is the same the new renter"))

# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.tools.translate import _
# from odoo.tools import SUPERUSER_ID
from datetime import datetime


class CompanyBank(models.Model):
    _inherit = 'res.partner.bank'

    bank_img = fields.Binary(attachment=True)


class BankPayment(models.Model):
    _name = 'takaful.bank.transfer.payment'
    _rec_name = 'number'
    _order = 'id desc'

    number = fields.Char(string='Number', defualt='/', readonly=True)
    name = fields.Char(string='Name', required=True)
    name_of = fields.Char(string='Name Of')
    amount = fields.Float(string='Amount')
    partner_id = fields.Many2one(comodel_name='res.partner', string='Customer', required=True)
    transfer_attachment = fields.Binary(attachment=True, string='Attachment')
    filename = fields.Char(string='Filename', size=256, readonly=True)
    state = fields.Selection(selection=[('draft', 'Draft'), ('pending', 'Pending'), ('reject', 'Rejected'),
                                        ('accept', 'Accepted'), ('cancel', 'Canceled')], string='State', default='draft')
    move_id = fields.Many2one(comodel_name='takaful.account.move', string='Invoice')
    transfer_date=fields.Date()

    @api.model
    def create(self, vals):
        res = super(BankPayment, self).create(vals)
        res.write({'number': self.env['ir.sequence'].sudo().next_by_code('bank.payment.transfer')})

        return res

    # @api.multi
    def action_pending(self):
        self.write({'state': 'pending'})

    # @api.multi
    def action_rejected(self):
        context = {'lang':self.partner_id.lang}
        val_msg = {
            'name': _("Bank Transfer State %s")%self.number,
            'body': _("Dear %s,<br/><br/>Your bank transfer has been rejected.")%self.partner_id.name,
            'partner_ids': [(6, 0, [self.partner_id.id])],
            # 'author_id': self.env['res.users'].sudo().browse(SUPERUSER_ID).partner_id.id,
            'author_id': self.env['res.users'].sudo()._is_admin().partner_id.id,
            'date': datetime.now(),
            'state': 'sent',
        }
        # val_mg
        self.write({'state': 'reject'})

    # @api.multi
    def action_accepted(self):
        if not self.move_id:
            vals = {
                'name':_("Bank Transfer State %s")%self.number,
                'partner_id': self.partner_id.id,
                'amount': self.amount,
                # 'operation_type': 'xxx',
                'type': 'transfert',
            }
            move = self.env['takaful.account.move'].sudo().create(vals)
            self.write({'move_id': move.id})
        context = {'lang': self.partner_id.lang}
        val_msg = {
            'name': _("Bank Transfer State %s")%self.number,
            'body': _("Dear %s,<br/<br/>Your bank transfer has been changed accepted. "
                      "Please check your balance")%self.partner_id.name,
            'partner_ids': [(6, 0, [self.partner_id.id])],
            # 'author_id': self.env['res.users'].sudo().browse(SUPERUSER_ID).partner_id.id,
            'author_id': self.env['res.users'].sudo()._is_admin().partner_id.id,
            'date': datetime.now(),
            'state': 'sent',
        }
        # val_msg
        self.move_id.write({'state': 'paid'})
        self.write({'state': 'accept'})

    # @api.multi
    def action_reset_to_draft(self):
        self.write({'state': 'draft'})

    # @api.multi
    def action_canceled(self):
        self.move_id.write({'state': 'rejected'})
        context = {'lang': self.partner_id.lang}
        val_msg = {
            'name': _("Bank Transfer State %s")%self.number,
            'body': _("Dear %s,<br/<br/>Your bank transfer has been changed to canceled. "
                      "Please check with your bank")%self.partner_id.name,
            'partner_ids': [(6, 0, [self.partner_id.id])],
            # 'author_id': self.env['res.users'].sudo().browse(SUPERUSER_ID).partner_id.id,
            'author_id': self.env['res.users'].sudo()._is_admin().partner_id.id,
            'date': datetime.now(),
            'state': 'sent',
        }
        # val_msg
        self.write({'state': 'cancel'})


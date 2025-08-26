# -*- coding: utf-8 -*-

from datetime import date, timedelta, datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re


class ContractInstallmentLine(models.Model):
    _inherit = 'line.contract.installment'

    coc_id = fields.Many2one(comodel_name='line.contract.installment.coc', string='CoC Ref')
    coc_ids = fields.One2many(comodel_name='line.contract.installment.coc', inverse_name='installment_id', string='CoCs')
    coc_bill_attachment_ids = fields.Many2many("ir.attachment", "install_bill_rel", "bill_installment_id", "attachment_id",
                                               string="Contractor Bill Attacment", copy=False)
    state = fields.Selection(selection_add=[
        ('coc', 'COC'),
        ('confirmed', 'Confirmed'),
        ('not_invoiced', 'Not Invoiced'),
        ('invoiced', 'Invoiced'),
        ('paid', 'Paid'), ('cancel', 'Cancel')],tracking=True, string="Status", default="coc")
    need_coc = fields.Selection([('yes', 'Yes'), ('no', 'No')], string="Need COC ?")
    coc_count = fields.Integer(string='Cocs', compute="_compute_coc_count")
    explanation = fields.Char(string='explanation')
    coc = fields.Boolean(string='CoC Created')
    coc_created = fields.Boolean('COC Created')
    is_in_progress = fields.Boolean(string="Is In Progress", compute="_compute_is_in_progress", store=True)
    payment_no = fields.Char('Payment No')
    contract_no = fields.Char(related='contract_id.name_seq', string='Contract No')
    state_history = fields.Text(string="State History", default='[]')
    note = fields.Text(string='Note')
    old_state = fields.Char(string="old_state")
    check = fields.Boolean(string='Check')



    @api.model
    def create(self, vals):
        vals['payment_no'] = self.env['ir.sequence'].next_by_code('line.contract.installment')
        return super(ContractInstallmentLine, self).create(vals)

    @api.depends('contract_id')
    def _compute_is_in_progress(self):
        for record in self:
            if record.contract_id.state == 'in_progress':
                record.is_in_progress = True
            else:
                record.is_in_progress = False

    def set_to_not_invoiced(self):
        return {
            'name': _('Reject Installment Payment'),
            'type': 'ir.actions.act_window',
            'res_model': 'installment.reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_reason': ''}
        }

    @api.depends('coc_ids')
    def _compute_coc_count(self):
        for rec in self:
            rec.coc_count = len(rec.coc_ids)

    def create_coc(self):
        if self.contract_id.state != 'in_progress':
            if not self.coc_bill_attachment_ids:
                raise ValidationError(_("You must attach Contractor Bill Attacment"))
            raise ValidationError(_("you can not send installment before approve contract"))

        if self.need_coc =='yes':
            self.action_create_coc()
        self.state = 'not_invoiced'

    def action_create_coc(self):
        coc = None
        coc = self.env['line.contract.installment.coc'].create({
            'vendor_id': self.contract_id.partner_id.id,
            'date': datetime.today(),
            'installment_id': self.id,
            'state': 'draft'
        })
        
    def action_view_coc(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('CertificateOf Completion'),
            'res_model': 'line.contract.installment.coc',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': [('installment_id', '=', self.id)],
            'context': {'create': False}
        }

    def action_open_return_installment_wizard(self):
        return {
            "type": "ir.actions.act_window",
            "name": _("Open Return State Wizard"),
            "res_model": "installment.return.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_installment_id": self.id},
        }

    def solve_note(self):
        self.note = False
        self.state = self.old_state or self.state

    def unlink(self):
        invoiced = self.filtered(lambda rec: rec.state != 'coc')
        if invoiced:
            raise ValidationError(_("Delete Operation Cannot be Done Because on or more installment has been invoiced") % ())
        else:
            return super(ContractInstallmentLine,  self).unlink()


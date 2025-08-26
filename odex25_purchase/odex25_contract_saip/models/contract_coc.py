# -*- coding: utf-8 -*-

from datetime import date, timedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ContractInstallmentLineCoC(models.Model):
    _name = 'line.contract.installment.coc'
    _description = 'Line Contract Installment CoC'

    name = fields.Char(string='Name')
    coc_stage = fields.Selection(string='CoC Stage', selection=[('before_bill', 'Before Bill'),
                                                                ('befor_bill_valid', 'Before Bill Validation'),
                                                                ('before_payment', 'Before Payment')],
                                 default='before_bill')
    installment_id = fields.Many2one(comodel_name='line.contract.installment', string='Payment Contract Ref.')
    vendor_id = fields.Many2one(comodel_name='res.partner', string='Vendor', related="installment_id.partner_id")
    date = fields.Date(string='Date')
    note = fields.Text(string='Note')
    state = fields.Selection(string='', selection=[('draft', 'Draft'), ('confirm', 'Confirm'), ('approve', 'Approveed'),
                                                   ('cancel', 'Reject')])
    reject_reason = fields.Char(string='Reject Reason')
    comptetion_date = fields.Date('Comptetion Date')
    requested_department = fields.Many2many('hr.department', string="Requested department",
                                            compute='_compute_requested_department')
    contract_id = fields.Many2one(string='Project Name', comodel_name='contract.contract',
                                  related='installment_id.contract_id')
    bill_date = fields.Date('Bill Date')
    bill_no = fields.Char('Bill No')
    total_amount = fields.Float('Due Amount', related='installment_id.total_amount')
    tax_amount = fields.Float('TAX Amount', related='installment_id.tax_amount')
    description_completed = fields.Html('Description Of Completed Work')
    coc_attachment_ids = fields.Many2many("ir.attachment", "coc_rel", "coc_id", "attachment_id",
                                          string="COC Attachment", copy=False)

    need_coc = fields.Selection(related='installment_id.need_coc')

    @api.depends('installment_id')
    def _compute_requested_department(self):
        for rec in self:
            rec.requested_department = [
                (6, 0, rec.installment_id.contract_id.contract_line_ids.mapped('department').ids)]

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code(self._name)
        return super(ContractInstallmentLineCoC, self).create(vals)

    def action_confirm(self):
        if not self.coc_attachment_ids:
            raise ValidationError(_("You must attach coc attachment"))
        self.write({'state': 'confirm'})

    def action_approve(self):
        self.write({'state': 'approve'})

    def action_cancel(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Specify Reject Reason'),
            'res_model': 'reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_origin': self.id, 'default_origin_name': self._name}
        }

    def cancel(self):
        self.write({
            'state': 'cancel',
            'reject_reason': self.env.context.get('reject_reason')
        })
        self.installment_id.message_post(body=_(
            'Coc Rejected By %s .  With Reject Reason : %s' % (str(self.env.user.name), str(self.reject_reason))))

    def action_draft(self):
        self.write({'state': 'draft'})

# -*- coding: utf-8 -*-
##############################################################################
#
#   Expert (LCT, Life Connection Technology)
#    Copyright (C) 2021-2022 LCT
#
##############################################################################

from datetime import date
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class SubcontractorWork(models.Model):
    _name = 'subcontractor.work'
    _description = "Subcontractor"
    _rec_name = 'subcontractor_id'

    subcontractor_id = fields.Many2one('res.partner', string="Subcontractor")
    work_item_id = fields.Many2one('work.item', string="Work Item")
    contract_amount = fields.Float(string="Contract Amount")
    balance = fields.Float(string="Balance", compute='_compute_balance')
    project_id = fields.Many2one('project.project', string="Project")
    installment_id = fields.Many2one('subcontractor.installment', string="Installment")

    @api.depends('installment_id')
    def _compute_balance(self):
        for record in self:
            total_paid = 0
            if record.installment_id:
                for line in record.installment_id.installment_line_ids:
                    if line.paid:
                        total_paid += line.amount
            record.balance = record.contract_amount - total_paid


    def open_installment_view(self):
        return {
            'name': _('Subcontractor Installment'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'subcontractor.installment',
            'target': 'current',
            'res_id': self.installment_id.id,
        }


class SubcontractorInstallment(models.Model):
    _name = "subcontractor.installment"

    name = fields.Char(string="Description")
    subcontractor_work_id = fields.Many2one('subcontractor.work', string="Subcontractor Work")
    delivery_date = fields.Date(string="Delivery Date")
    project_id = fields.Many2one('project.project', related="subcontractor_work_id.project_id", string="Project", store=True)
    subcontractor_id = fields.Many2one('res.partner', related="subcontractor_work_id.subcontractor_id", string="Subcontractor", store=True)
    work_item_id = fields.Many2one('work.item', related="subcontractor_work_id.work_item_id", store=True)
    contract_amount = fields.Float(related="subcontractor_work_id.contract_amount", string="Contract Amount", store=True)
    total_installment = fields.Float(string="Total Installment", compute="_get_installment_total", store=True)
    installment_line_ids = fields.One2many('subcontractor.work.line', 'subcontractor_installment_id', string="Installment Line")
    remain_amount = fields.Float(string="Remain Amount", compute="get_remain_amount")

    @api.depends('remain_amount')
    def get_remain_amount(self):
        for rec in self:
            rec.remain_amount = rec.contract_amount - rec.total_installment


    @api.constrains('total_installment')
    def check_total_installment(self):
        for rec in self:
            if rec.total_installment > rec.contract_amount:
                raise ValidationError(_("Total installment line is more than %s contract amount") % rec.contract_amount)

    @api.depends('installment_line_ids', 'installment_line_ids.amount')
    def _get_installment_total(self):
        for rec in self:
            rec.total_installment = sum([line.amount for line in rec.installment_line_ids])

    @api.model
    def default_get(self, fields):
        rec = super(SubcontractorInstallment, self).default_get(fields)
        if self._context.get('active_model'):
            active_id = self.env[self._context.get('active_model')].browse(self._context.get('active_id'))
            rec['subcontractor_work_id'] = active_id.id
            rec['delivery_date'] = date.today().strftime('%Y-%m-%d')
            if not active_id:
                raise ValidationError(_("Programming error: wizard action executed without active_id in context."))
        return rec

    @api.model
    def create(self, vals_list):
        res = super(SubcontractorInstallment, self).create(vals_list)
        res.subcontractor_work_id.write({'installment_id': res.id})
        return res


class SubContractorWorkLine(models.Model):
    _name = "subcontractor.work.line"

    subcontractor_installment_id = fields.Many2one('subcontractor.installment', string="Subcontract Installment")
    project_id = fields.Many2one('project.project', related="subcontractor_installment_id.project_id", string="Project", store=True)
    work_item_id = fields.Many2one('work.item', related="subcontractor_installment_id.work_item_id", string="Work Item", store=True)
    subcontractor_id = fields.Many2one('res.partner', related="subcontractor_installment_id.subcontractor_id", string="Subcontract", store=True)
    name = fields.Char(string="Description")
    type = fields.Selection([('fixed', 'Fixed'),
                             ('percentage', 'Percentage')], string="Payment Type", default='fixed')
    value = fields.Float(sting="Value")
    amount = fields.Float(strng="Amount", compute='get_amount',store=True)
    penalty_after = fields.Float(string="Penalty After")
    penalty_amount = fields.Float(string="Penalty Amount", compute='get_penalty_amount', store=True)
    penalty_percentage = fields.Float(string="Penalty Percentage")
    penalty_percentage_limit = fields.Float(string="Penalty Percentage Limit")
    last_installment = fields.Boolean(string="Last Installment")
    payment_id = fields.Many2one('project.payment.request', string="Payment")
    paid = fields.Boolean(string="Paid")
    paid_date = fields.Date(string="paid date")

    def unlink(self):
        for rec in self:
            if rec.paid:
                raise ValidationError(_("Cannot Delete line that already have payment"))
        return super(SubContractorWorkLine, self).unlink()

    def create_payment(self):
        vals = {}
        payment_obj = self.env['project.payment.request']
        for record in self:
            vals = {
                'sequence': '/',
                'name': record.name or '/',
                'project_id': record.subcontractor_installment_id.project_id.id,
                'date': record.subcontractor_installment_id.delivery_date,
                'penalty_amount': self.penalty_amount,
                'type': 'subcontractor',
                'state': 'draft',
                'partner_id': record.subcontractor_installment_id.subcontractor_work_id.subcontractor_id.id,
                'amount': record.amount,
                'subcontractor_line_id': self.id,
            }
            payment_id = payment_obj.create(vals)
            record.payment_id = payment_id.id
        return True

    @api.constrains('value', 'penalty_percentage', 'penalty_percentage_limit')
    def check_negative(self):
        message = _('%s Cannot Be Less than zero')
        for rec in self:
            if rec.value < 0.0:
                raise ValidationError(_(rec._fields['value'].string) + ' ' + message)
            if rec.penalty_percentage < 0.0:
                raise ValidationError(_(rec._fields['penalty_percentage'].string) + ' ' + message)
            if rec.penalty_percentage_limit < 0.0:
                raise ValidationError(_(rec._fields['penalty_percentage_limit'].string) + ' ' + message)

    @api.constrains('penalty_percentage')
    def penalty_percentage_check(self):
        for rec in self:
            if rec.penalty_percentage != 0.0:
                if rec.penalty_percentage > rec.penalty_percentage_limit:
                    raise ValidationError(_("Penalty Percentage Limit exceed !!"))

    @api.depends('type', 'value', 'subcontractor_installment_id.contract_amount')
    def get_amount(self):
        for rec in self:
            rec.amount = rec.value * rec.subcontractor_installment_id.contract_amount / 100.0 if rec.type == 'percentage' else rec.value

    @api.depends('penalty_percentage', 'amount')
    def get_penalty_amount(self):
        for rec in self:
            rec.penalty_amount = rec.penalty_percentage * rec.amount / 100.0

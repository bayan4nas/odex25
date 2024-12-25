# -*- coding: utf-8 -*-
##############################################################################
#
#   Expert (LCT, Life Connection Technology)
#    Copyright (C) 2021-2022 LCT
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class EngineeringOfficePayment(models.Model):
    _name = 'engineering.office.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Engineering Office Line"
    _order = 'project_id, id, name'
    _check_company_auto = True


    name = fields.Char(string="Description")
    project_id = fields.Many2one('project.project', string="project", ondelete='cascade', index=True, copy=False)
    engineering_office_id = fields.Many2one('res.partner', related='project_id.engineering_office_id',
                                            string="Engineering Office", store=True)
    percent = fields.Float(string="Percentage")
    amount = fields.Float(string="Amount", compute="get_amount", store=True)
    payment_id = fields.Many2one('project.payment.request', string="Eng Office Payment")
    paid = fields.Boolean(string="Paid")
    paid_date = fields.Date(string="Payment Date", )
    due_date = fields.Date(string="Due Date", )
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if values.get('display_type', self.default_get(['display_type'])['display_type']):
                values.update(percent=False, due_date=False, )
        return super(EngineeringOfficePayment, self).create(vals_list)

    def write(self, values):
        if 'display_type' in values and self.filtered(lambda line: line.display_type != values.get('display_type')):
            raise UserError(_(
                "You cannot change the type of a Engeerning Office line. Instead you should delete the current line and create a new line of the proper type."))
        return super(EngineeringOfficePayment, self).write(values)

    def create_office_payment(self):
        vals = {}
        payment_obj = self.env['project.payment.request']
        for record in self:
            vals = {
                'sequence': '/',
                'name': record.name or '/',
                'project_id': record.project_id.id,
                'delivery_date': record.due_date,
                'type': 'eng_office',
                'state': 'draft',
                'partner_id': record.engineering_office_id.id,
                'amount': record.amount,
                'eng_office_installment_id': self.id,
            }
            payment_id = payment_obj.create(vals)
            record.payment_id = payment_id.id
        return True

    @api.constrains('percent')
    def check_percent(self):
        for rec in self:
            if rec.percent < 0.0:
                raise ValidationError(_('Percentage Cannot be less than zero'))

    @api.depends('project_id', 'project_id.engineering_contract_amount', 'percent')
    def get_amount(self):
        for rec in self:
            if rec.project_id and rec.project_id.engineering_contract_amount > 0.0 and not rec.display_type:
                rec.amount = rec.project_id.engineering_contract_amount * (rec.percent / 100)


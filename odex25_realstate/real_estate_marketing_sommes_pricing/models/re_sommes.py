# -*- coding: utf-8 -*-
##############################################################################
#
#   Expert (LCT, Life Connection Technology)
#    Copyright (C) 2021-2022 LCT
#
##############################################################################

from odoo.exceptions import ValidationError, UserError
from odoo import models, fields, api, _

class ReSommes(models.Model):
    _name = "re.sommes"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Property somme"
    _order = "date desc, id desc"

    code = fields.Char(string="Code", default="/")
    property_id = fields.Many2one('internal.property', string="Property")
    unit_id = fields.Many2one('re.unit', string="unit")
    space = fields.Float(string="Property Space", related="property_id.property_space")
    district_id = fields.Many2one('district', string="District", related="property_id.district_id")
    last_somme = fields.Float(string="Last Somme",compute="get_last_somme", store=True )
    last_somme_meter = fields.Float(string="Last Somme Per Meter", compute="get_last_somme", store=True)
    name = fields.Char(string="Somme Owner")
    user_id = fields.Many2one('res.users', string="Responsible", default=lambda self: self.env.user)
    date = fields.Date(string="Date", default=fields.Date.context_today)
    amount = fields.Float(string="Value", tracking=True)
    amount_per_meter = fields.Float(string='Value per meter', tracking=True)
    notes = fields.Text('Notes')
    state = fields.Selection(
            [('draft', 'Draft'),
             ('confirm', 'Confirmed'),
             ('cancel', 'Canceled')], string="Status", default='draft',tracking=True)
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.user.company_id)

    def action_draft(self):
        for record in self:
            if record.state != 'confirm':
                record.write({'state': 'draft'})
            else:
                raise ValidationError(_('Cannot set to draft because somme already confirmed'))

    def action_confirm(self):
        for record in self:
            if record.code == '/' or False:
                record.code = record.env['ir.sequence'].next_by_code('re.sommes')
            record.write({'state': 'confirm'})

    def action_cancel(self):
        for record in self:
            if record.state != 'confirm':
                record.write({'state': 'cancel'})
            else:
                raise ValidationError(_("Cannot cancel confirmed somme"))

    @api.depends('property_id')
    def get_last_somme(self):
        for record in self:
            if record.property_id:
                if record.property_id.somme_ids:
                    last_id = self.env['re.sommes'].search(
                        [('id','!=',record._origin.id),('property_id', '=', record.property_id.id)], order='id desc', limit=1)
                    record.last_somme_meter = last_id and last_id.amount_per_meter or 0.0
                    record.last_somme = last_id and last_id.amount or 0.0


    @api.constrains('amount_per_meter', 'amount')
    def check_number(self):
        """
        If the number less than zero then raise error
        :return:
        """
        if self.amount < 0.0:
            raise ValidationError(_("Somme amount cannot be less than zero"))
        if self.amount_per_meter < 0.0:
            raise ValidationError(_("Somme per meter cannot be less than zero"))

    def unlink(self):
        state_description_values = {elem[0]: elem[1] for elem in self._fields['state']._description_selection(self.env)}
        for record in self.filtered(lambda record: record.state not in ['confirm']):
            raise UserError(_('You cannot delete an somme which is in %s state.') % (
            state_description_values.get(record.state),))
        return super(ReSommes, self).unlink()


# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError, UserError, Warning
from odoo import models, fields, api, exceptions, tools, _
from datetime import datetime, date


class ReClientRequirement(models.Model):
    _inherit = "re.clients.requirement"

    # action_type = fields.Selection([('rent', 'Rent'), ('sale', 'Sale')], string="Action Type", default='sale', readonly="True")
    client_type = fields.Selection([('serious', 'Serious'), ('possible', 'Possible'), ('not_serious', 'Not serious')], string="How serious is the client?", default='serious')
    state = fields.Selection([('draft', 'Open Request'),
                              ('register', 'Under Process'),
                              ('approve', 'Closed'),
                              ('cancel', 'Cancel'),
                              ], string="Status", default='draft')
    project_id = fields.Many2one('project.project', string='Project')
    marketer_user_id = fields.Many2one('res.users', string="Marketer", default=lambda self: self.env.user)

    def action_register(self):
        for rec in self:
            if rec.name == '/' or False:
                rec.name = self.env['ir.sequence'].next_by_code('re.clients.requirement')
            if rec.client_type != 'not_serious' and rec.client_line_ids:
                email_template = self.env.ref('khawald_real_estate_marketing.template_client_requirement_register')
                email_template.with_env(self.env).with_context(active_model=self._name).send_mail(rec.id)
                rec.write({'state': 'register'})
            elif rec.client_type != 'not_serious' and not rec.client_line_ids:
                raise exceptions.ValidationError(_("You must have Search Result"))
            else:
                rec.write({'state': 'approve'})

    def action_approve(self):
        for rec in self:
            if rec.client_type != 'not_serious':
                email_template = self.env.ref('khawald_real_estate_marketing.template_client_requirement_closed')
                email_template.with_env(self.env).with_context(active_model=self._name).send_mail(rec.id)
            rec.write({'state': 'approve'})


class ReClientRequirementProperty(models.Model):
    _inherit = "re.clients.requirement.property"

    reservation_id = fields.Many2one('property.reservation', string="Reservation")

    def create_reservation_record(self):
        vals = {}
        reservation_obj = self.env['property.reservation']
        for record in self:
            if record.state != 'register':
                raise exceptions.ValidationError(_("Please first Register Your Request"
                                                   "Then You can Proceed"))
            vals = {
                'name': '/',
                'search_type': self.search_type,
                'property_id': record.property_id and record.property_id.id or False,
                'state': 'draft',
                'unit_id': record.unit_id and record.unit_id.id or False,
                'partner_id': record.request_id.partner_id and record.request_id.partner_id.id or False,
            }
            reservation_id = reservation_obj.create(vals)
            if reservation_id:
                record.reservation_id = reservation_id.id
                record.flag = True
        return True



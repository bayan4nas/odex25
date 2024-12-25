# -*- coding: utf-8 -*-
##############################################################################
#
#   Expert (LCT, Life Connection Technology)
#    Copyright (C) 2021-2022 LCT
#
##############################################################################

import base64
import re
from odoo import models, fields, api, exceptions, _


class PropertyRole(models.Model):
    _name = 'property.role'
    _description = 'Property Role'

    name = fields.Char('Name')


class Unit(models.Model):
    _name = 're.unit'
    _description = 'Property Unit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id desc"

    unit_category = fields.Selection([
        ('residential', 'Residential'),
        ('commercial', 'Commercial'),
        ('lands', 'Lands')], string="Unit Category")
    tax_id = fields.Many2one(comodel_name='account.tax', string='Tax',domain=[('type_tax_use', '=', 'sale')],)
    attach_nbr = fields.Integer(compute='get_attachments')
    content_ids = fields.One2many(comodel_name='property.content.details', inverse_name='unit_id', string='')
    active = fields.Boolean(default=True)
    role_id = fields.Many2one('property.role', string='Role')
    unlock = fields.Boolean(default=True, string="Unlock")
    name = fields.Char(string="Unit Name")
    color = fields.Integer(string='Color Index', compute="set_color")
    property_id = fields.Many2one('internal.property', string="Property")
    seq = fields.Char(string="Unit Code", index=True)
    state = fields.Selection([('draft', 'Draft'),
                              ('available', 'Available'),
                              ('reserved', 'Reserved'),
                              ('rented', 'Rented'),
                              ('sold', 'Sold')], string="Status", default='draft')
    journal_id = fields.Many2one('account.journal', string='Journal')
    accrued_account_id = fields.Many2one('account.account', string='Accrued Account')
    debit_account_id = fields.Many2one('account.account', string='Debit Account')
    revenue_account_id = fields.Many2one('account.account', string='Revenue Account')
    unit_type_id = fields.Many2one('unit.type', string="Unit Type")
    management_type = fields.Selection(related='property_id.management_type', string="Management Type", store=True)
    market_type = fields.Selection(related="property_id.market_type", string="Market Type", store=True)
    unit_market_type = fields.Selection(related="property_id.market_type", string="Unit Market Type", store=True)
    other_type = fields.Char(related="property_id.other_type", string="Other Type")
    action_type = fields.Selection([('sale', 'Sale')], string="Action Type", default="sale")
    city_id = fields.Many2one('re.city', related="property_id.city_id", string="City", store=True)
    district_id = fields.Many2one('district', related="property_id.district_id", string="District", store=True)
    # length = fields.Float(string="Length")
    width = fields.Float(string="Width")
    space = fields.Float(string="Unit Space")
    external_space = fields.Float(string="External Space", tracking=True)
    external_price = fields.Float(string="External Meter Price", tracking=True)

    mezzanine = fields.Boolean(string="Mezzanine")
    mezzan_length = fields.Float(string="Mezzan Length")
    mezzan_width = fields.Float(string="Mezzan Width")
    meter_price = fields.Float(string="Meter Price", compute="get_rent_price", store=True, digits=(16, 2))
    rent_price = fields.Float(string="Total Price")
    limit_meter_price = fields.Float(string="Limit Meter Price", compute="get_limit_rent_price", store=True)
    limit_rent = fields.Float(string="Limit Rent", store=True)
    electric_meter = fields.Boolean(string="Electric Meter")
    electric_serial = fields.Char(string="Electric Serial")
    electric_subscription = fields.Char(string="Electric Subscription")
    electric_account = fields.Char(string="Electric Account")
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)
    user_id = fields.Many2one('res.users', string="Marketer", default=lambda self: self.env.user)
    room_no = fields.Integer(string="Room Count")
    bathroom_no = fields.Integer(string="Bathroom Count")
    hall_no = fields.Integer(string="Hall Count")
    kitchen_no = fields.Integer(string="kitchen Count")
    stamping_count = fields.Selection(string="Stamping Count", related='property_id.stamping_count')
    stamping = fields.Char(string="Stamping Number", related='property_id.stamping')
    stamping_date = fields.Date(string="Stamping Date", related='property_id.stamping_date')
    stamping_state = fields.Selection(related='property_id.stamping_state')
    stamping_attach = fields.Binary("Stamping Attach", attachment=True, related='property_id.stamping_attach')

    stamping_2 = fields.Char(string="Stamping Number", related='property_id.stamping_2')
    stamping_date_2 = fields.Date(string="Stamping Date", related='property_id.stamping_date_2')
    stamping_attach_2 = fields.Binary("Stamping Attach", attachment=True,store=True, related='property_id.stamping_attach_2')
    stamping_state_2 = fields.Selection([('updated', 'Updated'), ('not_updated', 'Not Updated')],
                                        related='property_id.stamping_state_2')

    stamping_3 = fields.Char(string="Stamping Number", related='property_id.stamping_3')
    stamping_date_3 = fields.Date(string="Stamping Date", related='property_id.stamping_date_3')
    stamping_attach_3 = fields.Binary("Stamping Attach", attachment=True,store=True, related='property_id.stamping_attach_3')
    stamping_state_3 = fields.Selection([('updated', 'Updated'), ('not_updated', 'Not Updated')],
                                        related='property_id.stamping_state_3')

    stamping_new = fields.Char(string="Stamping Number New")
    stamping_date_new = fields.Date(string="Stamping Date New")
    stamping_attach_new = fields.Binary("Stamping Attach New", attachment=True)

    _sql_constraints = [
        ('name', 'unique(name)', _('Name must be unique.')),
    ]
    # Smart button to count related maintenance records
    maintenance_count = fields.Integer(string="Maintenance Count", compute='_compute_maintenance_count')




    def get_attachments(self):
        action = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        action['domain'] = str([('res_model', '=', 're.unit'), ('res_id', 'in', self.ids)])
        action['context'] = "{'default_res_model': '%s','default_res_id': %d}" % (self._name, self.id)
        domain = [('res_model', '=', 're.unit'), ('res_id', '=', self.id)]
        self.attach_nbr = self.env['ir.attachment'].search_count(domain)
        return action

    def _compute_maintenance_count(self):
        for record in self:
            record.maintenance_count = self.env['property.management.maintenance'].search_count([
                ('unit_ids', 'in', record.id)
            ])

    def action_view_maintenance(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Maintenance',
            'view_mode': 'tree,form',
            'res_model': 'property.management.maintenance',
            'domain': [('unit_ids', 'in', self.id)],
            'context': dict(self.env.context),
        }

    @api.depends('state')
    def set_color(self):
        for record in self:
            color = 0
            if record.state == 'draft':
                color = 1
                record.color = color
            if record.state == 'reserved':
                color = 2
                record.color = color
            if record.state == 'rented':
                color = 3
                record.color = color

    @api.depends('limit_rent', 'space')
    def get_limit_rent_price(self):
        for rec in self:
            if rec.limit_rent != 0.0 and rec.space != 0.0:
                rec.limit_meter_price = rec.limit_rent / rec.space
            else:
                rec.limit_rent = 0.0

    def action_available(self):
        """
        after checking meter price and limit price meter
        Write the state of unit and make it available for rent or reserved
        :return:
        """
        if self.limit_meter_price > self.meter_price or self.limit_rent > self.rent_price:
            raise exceptions.ValidationError(_('Limit must be less than price per meter'))
        if self.property_id.state == 'rent':
            self.property_id.write({'state': 'approve'})
        self.write({'state': 'available'})

    def action_draft(self):
        """
        set unit to draft if it available only
        :return:
        """
        state = dict(self.fields_get(allfields=['state'])['state']['selection'])[self.state]
        if self.state == 'available':
            self.write({'state': 'draft'})
        else:
            raise exceptions.ValidationError(_("Unit cannot be draft because it in state %s") % state)

    # def name_get(self):
    #     result = []
    #     for rec in self:
    #         name = "%s,%s" % (rec.name, rec.seq)
    #         result.append((rec.id, name))
    #     return result

    @api.constrains('electric_serial', 'electric_subscription', 'electric_account')
    def fields_check(self):
        """
        Check if name field contain an invalid value
        :raise exception
        """
        num_pattern = re.compile(r'\d', re.I | re.M)
        white_space = re.compile(r'^\s')
        if self.electric_meter:
            if not num_pattern.search(self.electric_subscription):
                raise exceptions.ValidationError(
                    _("Electric subscription field accept numbers or special character only"))
            if not num_pattern.search(self.electric_account):
                raise exceptions.ValidationError(_("Electric account field accept numbers or special character only"))
            if not num_pattern.search(self.electric_serial):
                raise exceptions.ValidationError(_("Electric serial field accept numbers or special character only"))
            if white_space.search(self.electric_serial):
                raise exceptions.ValidationError(_("Electric serial (cannot accept white space)"))
            if white_space.search(self.electric_subscription):
                raise exceptions.ValidationError(_("Electric subscription (cannot accept white space)"))
            if white_space.search(self.electric_account):
                raise exceptions.ValidationError(_("Electric account (cannot accept white space)"))

    @api.constrains('limit_meter_price', 'space', 'meter_price', 'mezzan_width', 'mezzan_length')
    def check_number(self):
        """
        If the number less than zero then raise error
        :return:
        """
        for record in self:
            if record.limit_meter_price < 0.0:
                raise exceptions.ValidationError(_("Limit Meter space cannot be less than zero"))
            if record.space < 0.0:
                raise exceptions.ValidationError(_("Space cannot be less than zero"))
            if record.meter_price < 0.0:
                raise exceptions.ValidationError(_("Meter price cannot be less than zero"))

    @api.depends('rent_price', 'space')
    def get_rent_price(self):
        """
        Get rent Price Per Meter
        :return: total rent price
        """
        for record in self:
            if record.space != 0.0:
                record.meter_price = record.rent_price / record.space

    def action_toggle_is_locked(self):
        self.ensure_one()
        if self.unlock:
            self.write({'unlock': False})
        else:
            self.write({'unlock': True})

    @api.model
    def create_duplicate_server_action(self):
        # Create the server action to duplicate records
        action = self.env['ir.actions.server'].create({
            'name': 'Duplicate Selected Records',
            'model_id': self.env['ir.model'].search([('model', '=', 're.unit')], limit=1).id,
            'state': 'code',
            'code': """
                for record in records:
                    record.copy()
            """,
        })

        # Create the action in the contextual action dropdown menu
        self.env['ir.actions.actions'].create({
            'name': 'Duplicate Selected Records',
            'binding_model_id': self.env['ir.model'].search([('model', '=', 're.unit')], limit=1).id,
            'type': 'ir.actions.server',
            'binding_type': 'action',
            'binding_view_types': 'list',
            'server_action_ids': [(4, action.id)],
        })

class PropertyContentDetails(models.Model):
    _name = 'property.content.details'
    _description = 'Property Unit Details'

    unit_id = fields.Many2one('re.unit', string='Property', required=True, ondelete='cascade')
    content_id = fields.Many2one('property.contents', 'Property Content')
    qty = fields.Integer('QTY')
    desc = fields.Char('Description')
    attachment = fields.Binary(string="Property Docs")








# -*- coding: utf-8 -*-
##############################################################################
#
#   Expert (LCT, Life Connection Technology)
#    Copyright (C) 2021-2022 LCT
#
##############################################################################

from odoo.exceptions import ValidationError
from odoo import models, fields, api, _

class ReClientRequirement(models.Model):
    _name = "re.clients.requirement"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "clients requirement"

    name = fields.Char(string='Reference', default='/')
    request_date = fields.Date('Date', index=True, default=fields.Date.context_today)
    action_type = fields.Selection([('sale', 'Sale')], string="Action Type", default='sale')
    search_type = fields.Selection([('property', 'Property'), ('unit', 'Unit')], string="Search Type", default='unit')
    unit_type_id = fields.Many2one('unit.type', string="Unit Type")
    property_type_ids = fields.Many2many('internal.property.type', string="Type")
    city_id = fields.Many2one('re.city', string="City")
    user_id = fields.Many2one('res.users', string="Responsible", default=lambda self: self.env.user)
    district = fields.Many2many('district', 'client_requisition_district_rel', 'client_requisition_id', 'district_id', string='Districts')
    region = fields.Selection([('north', 'North'), ('south', 'South'), ('east', 'East'), ('west', 'West')], string='Region')
    size_from = fields.Float(string='Size from', digits=(16, 2))
    size_to = fields.Float(string='Size to', digits=(16, 2))
    value_from = fields.Float(string='Value from', digits=(16, 2))
    value_to = fields.Float(string='Value to', digits=(16, 2))
    partner_id = fields.Many2one('res.partner', string="Client")
    phone = fields.Char(string='Phone', related='partner_id.phone')
    mobile = fields.Char(string='Mobile', related='partner_id.mobile')
    request_from = fields.Date(string="Request From")
    request_to = fields.Date(string="Request To")
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.user.company_id)
    room_from = fields.Integer(string='Room from')
    room_to= fields.Integer(string='Room to')
    bath_room_from = fields.Integer(string='Number of BathRooms')
    bath_room_to = fields.Integer(string='Number of BathRooms')
    kitchen_number_from = fields.Integer(string='Number Of Kitchen ')
    kitchen_number_to = fields.Integer(string='Number Of Kitchen ')
    client_line_ids = fields.One2many('re.clients.requirement.property', 'request_id', string="Attachment")
    state = fields.Selection([('draft', 'Draft'),
                              ('register', 'Registered'),
                              ('approve', 'Approved'),
                              ('cancel', 'Cancel'),
                              ], string="Status", default='draft')

    def get_satisfied_property(self):
        property_pool = self.env['internal.property']
        unit_pool = self.env['re.unit']
        prop_recects = []
        line_ids = []
        prop_ids = []
        unit_ids = []
        for rec in self:
            if rec.search_type == 'property':
                domain = [('state', '=', 'approve'),
                          ('property_type_id', 'in', rec.property_type_ids.ids)
                ]
            else:
                domain = [('state', '=', 'available'),
                          ('unit_type_id', '=', rec.unit_type_id.id)
                ]
            domain.append(('action_type', '=', rec.action_type))
            if rec.client_line_ids:
                rec.client_line_ids = False
            if rec.city_id:
                domain.append(('city_id', '=', rec.city_id.id))
            if rec.district:
                domain.append(('district_id', 'in', [dis.id for dis in rec.district]))
            if rec.size_from or rec.size_to:
                if rec.search_type == 'property':
                    domain.append(('property_space', '>=', rec.size_from))
                    domain.append(('property_space', '<=', rec.size_to))
                else:
                    domain.append(('space', '>=', rec.size_from))
                    domain.append(('space', '<=', rec.size_to))
            if rec.value_from or rec.value_to:
                domain.append(('rent_price', '>=', rec.value_from))
                domain.append(('rent_price', '<=', rec.value_to))
            if rec.room_from or rec.room_to and rec.search_type != 'property':
                domain.append(('room_no', '>=', rec.room_from))
                domain.append(('room_no', '<=', rec.room_to))
            if rec.bath_room_from or rec.bath_room_to and rec.search_type != 'property':
                domain.append(('bathroom_no', '>=', rec.bath_room_from))
                domain.append(('bathroom_no', '<=', rec.bath_room_to))
            if rec.kitchen_number_from or rec.kitchen_number_to and rec.search_type != 'property':
                domain.append(('kitchen_no', '>=', rec.kitchen_number_from))
                domain.append(('kitchen_no', '<=', rec.kitchen_number_to))
            if rec.search_type == 'property':
                prop_ids = property_pool.search(domain)
            else:
                unit_ids = unit_pool.search(domain)
        if prop_ids:
            for property_record in prop_ids:
                self.env['re.clients.requirement.property'].create({'request_id': rec.id,
                                                                    'property_id': property_record and property_record.id or False,
                                                                    'property_city': property_record.city_id and property_record.city_id.id or False,
                                                                    'property_district': property_record.district_id and property_record.district_id.id,
                                                                    'price': property_record.total_price,
                                                                    'size': property_record.property_space,
                                                                    'room': property_record and property_record.room_no,})

        if unit_ids:
            for unit_record in unit_ids:
                self.env['re.clients.requirement.property'].create({'request_id': rec.id,
                                                                    'unit_id': unit_record and unit_record.id or False,
                                                                    'property_id': unit_record and unit_record.property_id and unit_record.property_id.id or False,
                                                                    'property_city': unit_record and unit_record.city_id and unit_record.city_id.id or False,
                                                                    'property_district': unit_record and unit_record.district_id and unit_record.district_id.id or False,
                                                                    'price': unit_record and unit_record.rent_price,
                                                                    'room': unit_record and unit_record.room_no,
                                                                    'size': unit_record and unit_record.space})
        return True

    def action_register(self):
        for rec in self:
            if not rec.client_line_ids:
                raise ValidationError(_("You must have Search Result"))
            if rec.name == '/' or False:
                rec.name = self.env['ir.sequence'].next_by_code('re.clients.requirement')
            rec.write({'state': 'register'})

    def action_approve(self):
        for rec in self:
            sale_ids = rec.client_line_ids.mapped('sale_contract_id')
            if not sale_ids:
                raise ValidationError(_("You Cannot Close the Request"
                                                   "Because you must have either Sale or Rent Request"))
        self.write({'state': 'approve'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_cancel(self):
        self.write({'state': 'cancel'})


    @api.onchange('search_type')
    def onchange_search_type(self):
        self.room_from = 0
        self.room_to = 0
        self.bath_room_from = 0
        self.bath_room_to = 0
        self.kitchen_number_from = 0
        self.kitchen_number_to = 0


class ReClientRequirementProperty(models.Model):
    _name = "re.clients.requirement.property"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "clients requirement Property"
    _rec_name = 'request_id'

    def create_sale_request(self):
        vals = {}
        sale_obj = self.env['re.sale']
        for record in self:
            if record.state != 'register':
                raise ValidationError(_("Please first Register Your Request"
                                                   "Then You can Proceed"))
            vals = {
                'name': '/',
                'sell_method': self.search_type,
                'property_id': record.property_id and record.property_id.id or False,
                'state': 'draft',
                'total_property_size': record.size,
                'amount': record.price,
                'unit_id': record.unit_id and record.unit_id.id or False,
                'partner_id': record.request_id.partner_id and record.request_id.partner_id.id or False,
            }
            sale_id = sale_obj.create(vals)
            if sale_id:
                sale_id.action_register()
                record.sale_contract_id = sale_id.id
                record.flag = True
        return True


    request_id = fields.Many2one('re.clients.requirement', string="Client Requirement")
    search_type = fields.Selection([('property', 'Property'), ('unit', 'Unit')], string="Search Type", related='request_id.search_type')
    property_id = fields.Many2one('internal.property', string="Property")
    unit_id = fields.Many2one('re.unit', string="Unit")
    property_city = fields.Many2one('re.city', string="City")
    property_district = fields.Many2one('district', string="District")
    price = fields.Float(string='Price', digits=(16, 2))
    size = fields.Float(string='Size', digits=(16, 2))
    room = fields.Float(string='Room', digits=(16, 2))
    sale_contract_id = fields.Many2one('re.sale', string="Sale Request")
    flag = fields.Boolean(string='Selected')
    state = fields.Selection([('draft', 'Draft'),
                              ('register', 'Registered'),
                              ('approve', 'Approved'),
                              ('cancel', 'Cancel'),
                              ], string="Status", related='request_id.state')
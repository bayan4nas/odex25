# -*- coding: utf-8 -*-
##############################################################################
#
#   Expert (LCT, Life Connection Technology)
#    Copyright (C) 2021-2022 LCT
#
##############################################################################

import base64
import json
from lxml import etree
import re
from odoo import models, fields, api, exceptions, _
from odoo.modules.module import get_module_resource


class Property(models.Model):
    _name = 'internal.property'
    _description = 'Property'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id desc"

    # Smart button to count related maintenance records
    maintenance_count = fields.Integer(string="Maintenance Count", compute='_compute_maintenance_count')
    is_unit_count_fixed = fields.Boolean(string="Is Unit Count Fixed in Floor")
    floor_ids = fields.One2many(comodel_name='floor.unit.details', inverse_name='property_id', string='')
    account_analy_id = fields.Many2one('account.analytic.account', string='Analytic Account')
    is_new = fields.Boolean(string="Is New Property?", default=False)
    suitability_for_residence = fields.Selection([
        ('residential', 'Residential'),
        ('non_residential', 'Non-Residential'),
    ], string="Property Suitability for Residence")
    contract_counts = fields.Integer(string='Contracts', compute='count_contracts_number')

    def count_contracts_number(self):
        contract_count = self.env['rental.contract'].sudo().search([('property_id', '=', self.id)])
        self.contract_counts = len(contract_count)

    def get_contract(self):
        contract_id = self.env['rental.contract'].sudo().search(
            [('property_id', '=', self.id)])
        form_id = self.env.ref('property_management.rental_contract_form_view').id
        list_id = self.env.ref('property_management.rental_contract_list_view').id
        domain = [('id', 'in', contract_id.ids)]
        return {
            'name': _('Rental Contract'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'rental.contract',
            'views': [(list_id, 'tree'), (form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': domain,
        }

    # @api.model
    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     res = super(Property, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
    #                                                            submenu=submenu)
    #     doc = etree.XML(res['arch'])
    #     if (view_type == 'form'):
    #         for node in doc.xpath("//field"):
    #             modifiers = json.loads(node.get("modifiers"))
    #             modifiers['readonly'] = [('state', 'in', ['approve'])]
    #             node.set("modifiers", json.dumps(modifiers))
    #             res['arch'] = etree.tostring(doc, encoding='unicode')
    #     return res

    @api.onchange('floors_count')
    def _onchange_no_of_floor(self):
        if self.floors_count > 0:
            # Clear existing lines
            self.floor_ids = [(5, 0, 0)]
            # Create floor records based on the number of floors
            floors = []
            for i in range(1, self.floors_count + 1):

                floor_name = _('Floor') + ' ' + str(i)  # Construct the floor name

                # Search for the role with the given floor name
                role_record = self.env['property.role'].search([('name', '=', floor_name)], limit=1)

                if not role_record:
                    # If not found, create a new role with the corresponding name
                    role_record = self.env['property.role'].create({
                        'name': floor_name,
                    })
                # Append the record to One2many field
                floors.append((0, 0, {'role_id': role_record.id}))
            self.floor_ids = floors

    def _compute_maintenance_count(self):
        for record in self:
            record.maintenance_count = self.env['property.management.maintenance'].search_count([
                ('property_id', '=', record.id)
            ])

    def action_view_maintenance(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Maintenance',
            'view_mode': 'tree,form',
            'res_model': 'property.management.maintenance',
            'domain': [('property_id', '=', self.id)],
            'context': dict(self.env.context),
        }

    # Inherit the form view and add the button

    @api.model
    def _default_image(self):
        image_path = get_module_resource('real_estate', 'static/src/img', 'default_logo.png')
        return base64.b64encode(open(image_path, 'rb').read())

    active = fields.Boolean(default=True)
    unlock = fields.Boolean(default=True, string="Unlock")
    seq = fields.Char(string="Sequence", index=True)
    name = fields.Char(string="Name")
    state = fields.Selection([('draft', 'Draft'),
                              ('register', 'Registered'),
                              ('approve', 'Approved'),
                              ('reserve', 'Reserved'),
                              ('rent', 'Rented'),
                              ('sold', 'Sold')], string="Status", default='draft')
    logo = fields.Binary("Property Logo", default=_default_image, attachment=True,
                         help="This field holds the image used as photo for the Property, limited to 1024x1024px.")
    property_type_id = fields.Many2one('internal.property.type', string="Type")
    property_state_id = fields.Many2one('re.property.state', string="Property State")
    ownership_type = fields.Selection(
        [('full', 'Full Ownership'), ('share', 'Share Ownership'), ('inclusion', 'Inclusion')], string='Ownership Type',
        default='full', required=True, tracking=True)
    company_profit = fields.Selection([('percentage', 'Percentage'),
                                       ('number', 'Fixed amount')],
                                      string='Company Profit')
    company_profit_amount = fields.Float(string='Company Profit Amount')

    management_type = fields.Selection([('internal_investment', 'Internal Investment'),
                                        ('external_investment', 'External Investment'),
                                        ('include', 'Include')], string="Management Type",
                                       default="internal_investment")
    market_type = fields.Selection([('residential', 'Residential'),
                                    ('commercial', 'Commercial'),
                                    ('residential_commercial', 'Residential and Commercial'),
                                    ('industrial', 'Industrial'),
                                    ('other', 'Other')], string="Market Type", default="commercial")
    other_type = fields.Char(string="Other Type")
    action_type = fields.Selection([('sale', 'Sale')], string="Action Type", default="sale")
    no_units = fields.Integer(string="Number of units", compute="count_unit_number", store=True)
    no_rented_units = fields.Integer(string='Number of rented units', compute='count_unit_number', store=True)
    no_available_units = fields.Integer(string='Number of available units', compute='count_unit_number', store=True)
    no_reserved_units = fields.Integer(string='Number of reserved units', compute='count_unit_number', store=True)
    # no_sold_units = fields.Integer(_('Number Of Sold Units'), compute='count_unit_number')
    city_id = fields.Many2one('re.city', string="City")
    district_id = fields.Many2one('district', string="District")
    street = fields.Char(string="Street Name")
    property_no = fields.Integer(string="Property Number")
    # Building coordinates x and y and it location
    # coordinate_x = fields.Float(string="Coordinate X")
    # coordinate_y = fields.Float(string="Coordinate Y")
    location = fields.Char(string="Location")
    note = fields.Text(string="Note")
    # Building length
    north = fields.Char(string="North Length")
    south = fields.Char(string="South Length")
    east = fields.Char(string="East Length")
    west = fields.Char(string="West Length")
    # Building opening street
    north_street = fields.Char(string="North Street")
    south_street = fields.Char(string="South Street")
    east_street = fields.Char(string="East Street")
    west_street = fields.Char(string="West Street")
    property_face_ids = fields.Many2many('property.faces', string="Property Face")
    user_id = fields.Many2one('res.users', string="Responsible", default=lambda self: self.env.user)
    block_no = fields.Char(string="Block Number")
    licence_no = fields.Char(string="Licence Number")
    plate_no = fields.Char(string="Plate Number")
    plot_no = fields.Char(string="Plot Number")
    planned_no = fields.Char(string="Planned Number")
    planned_id = sketch = fields.Many2one('sketchs.sketchs', string='Planned Name')
    # Stamping information
    stamping_count = fields.Selection(string="Stamping Count", selection=[('1', '1'),
                                                                          ('2', '2'),
                                                                          ('3', '3')], default="1")
    stamping = fields.Char(string="Stamping Number")
    stamping_state = fields.Selection([('updated', 'Updated'), ('not_updated', 'Not Updated')])
    stamping_date = fields.Date(string="Stamping Date")
    stamping_attach = fields.Binary("Stamping Attach", attachment=True)

    stamping_2 = fields.Char(string="Stamping Number")
    stamping_date_2 = fields.Date(string="Stamping Date")
    stamping_attach_2 = fields.Binary("Stamping Attach", attachment=True)
    stamping_state_2 = fields.Selection([('updated', 'Updated'), ('not_updated', 'Not Updated')])

    stamping_3 = fields.Char(string="Stamping Number")
    stamping_date_3 = fields.Date(string="Stamping Date")
    stamping_attach_3 = fields.Binary("Stamping Attach", attachment=True)
    stamping_state_3 = fields.Selection([('updated', 'Updated'), ('not_updated', 'Not Updated')])

    # Water Meter information
    water_count = fields.Selection([('1', '1'),
                                    ('2', '2'),
                                    ('3', '3')], string="Meter Count", default="1")
    water_serial = fields.Char(string="Serial Number")
    water_subscription = fields.Char(string="Subscription Number")
    water_account = fields.Char(string="Water Account")
    water_serial2 = fields.Char(string="Serial Number")
    water_subscription2 = fields.Char(string="Subscription Number")
    water_account2 = fields.Char(string="Water Account")
    water_serial3 = fields.Char(string="Serial Number")
    water_subscription3 = fields.Char(string="Subscription Number")
    water_account3 = fields.Char(string="Water Account")
    unit_ids = fields.One2many('re.unit', 'property_id', string="Property Unit")
    property_space = fields.Float(string="Property Space", digits=(16, 2))
    property_unit_space = fields.Float(string="Unit's Space", compute="get_property_space", store=True)

    uexternal_space = fields.Float(string="Unit External Space", compute="get_unit_info", store=True)
    uspace = fields.Float(string="Unit Total Space", compute="get_unit_info", store=True)

    rent_price = fields.Float(string="Rent Price", compute="get_rent_price", store=True, digits=(16, 2))
    meter_price = fields.Float(string="Meter Price")
    pur_price = fields.Float(string="Purchase Price")
    pur_meter_price = fields.Float(string="Purchase Price for Meter")
    curr_price = fields.Float(string="Current Purchase Price")

    property_age = fields.Char(string="Property Age")
    total_price = fields.Float(string="Total Price", compute="get_total_price")
    floors_count = fields.Integer(string="Floors Count")
    appendices = fields.Selection([('yes', 'Yes'),
                                   ('no', 'No')], string="Appendices", default="no")
    separated = fields.Selection([('yes', 'Yes'),
                                  ('no', 'No')], string="Separated", default="no")
    internal_staircase = fields.Selection([('yes', 'Yes'),
                                           ('no', 'No')], string="Internal Staircase", default="no")
    shops_no = fields.Integer(string="Shops Number")
    tree_no = fields.Integer(string="Tree Number")
    apartment_no = fields.Integer(string="Apartment Number")
    buildings_no = fields.Integer(string="Buildings Number")
    well_no = fields.Integer(string="Well Numbers")
    rent_status = fields.Selection([('rented', 'Rented'),
                                    ('not', 'Not Rented')], string="Rent Status", default="not")

    property_cost = fields.Float(string="Property Cost")
    company_id = fields.Many2one('res.company', string='Company', required=True,
                                 default=lambda self: self.env.user.company_id)
    # attachment_ids = fields.One2many('ir.attachment', 'property_id', string="Attachment")
    owner_id = fields.Many2one('res.partner', string="Owner")
    faseh = fields.Char('faseh')
    proceedings = fields.Char('Proceedings')
    Areal_decision = fields.Char('Areal Decision')
    offered = fields.Boolean(string="Offered")
    branch_manager_id = fields.Many2one('res.users', string="Branch Manager", default=lambda self: self.env.user)
    marketer_id = fields.Many2one('res.users', string="Marketer")
    unit_counts = fields.Integer('Unit Count', compute="compute_unit_count")
    unit_floor_count = fields.Integer(string="Unit in floor count")

    room_no = fields.Integer(string="Room Count", compute="get_unit_info", store=True)
    bathroom_no = fields.Integer(string="Bathroom Count", compute="get_unit_info", store=True)
    hall_no = fields.Integer(string="Hall Count", compute="get_unit_info", store=True)
    kitchen_no = fields.Integer(string="kitchen Count", compute="get_unit_info", store=True)

    # _sql_constraints = [
    #     ('stamping', 'unique(stamping)', _('Stamping must be unique.')),
    # ]

    @api.depends('unit_ids', 'unit_ids.room_no', 'unit_ids.bathroom_no', 'unit_ids.hall_no', 'unit_ids.kitchen_no',
                 'unit_ids.space', 'unit_ids.external_space')
    def get_unit_info(self):
        for rec in self:
            rec.room_no = sum([unit.room_no for unit in rec.unit_ids])
            rec.bathroom_no = sum([unit.bathroom_no for unit in rec.unit_ids])
            rec.hall_no = sum([unit.hall_no for unit in rec.unit_ids])
            rec.kitchen_no = sum([unit.kitchen_no for unit in rec.unit_ids])
            rec.uexternal_space = sum([unit.external_space for unit in rec.unit_ids])
            uspace = rec.uexternal_space + rec.property_unit_space
            rec.uspace = uspace

    @api.depends('property_space', 'meter_price')
    def get_total_price(self):
        for rec in self:
            rec.total_price = rec.meter_price * rec.property_space

    def get_unit(self):
        form_id = self.env.ref('real_estate.unit_form_view').id
        domain = [('id', 'in', self.unit_ids.ids)]
        return {
            'name': _('Units'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 're.unit',
            'views': [(False, 'tree'), (form_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': domain,
        }

    def get_attachments(self):
        action = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        action['domain'] = str([('res_model', '=', 'internal.property'), ('res_id', 'in', self.ids)])
        action['context'] = "{'default_res_model': '%s','default_res_id': %d}" % (self._name, self.id)
        return action

    def compute_unit_count(self):
        self.unit_counts = len(self.unit_ids)

    @api.onchange('ownership_type')
    def set_owner(self):
        if self.ownership_type == 'full':
            self.owner = self.company_id.partner_id
        else:
            self.owner = False

    def get_location(self):
        url = "http://maps.google.com/maps"
        return {
            'type': 'ir.actions.act_url',
            'url': url,
            'target': 'new'
        }

    @api.depends('unit_ids', 'unit_ids.space')
    def get_property_space(self):
        """
        Get total property space from related unit space
        :return:
        """
        for rec in self:
            rec.property_unit_space = sum([unit.space for unit in rec.unit_ids])

    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise exceptions.ValidationError(_('You cannot delete an approved property.'))
            for unit in record.unit_ids:
                state = dict(unit.fields_get(allfields=['state'])['state']['selection'])[unit.state]
                if unit.state != 'draft':
                    raise exceptions.ValidationError(
                        _("You cannot delete this property because he have a unit with the following state %s unit "
                          "code %s") % state % unit.seq)
            record.unit_ids.unlink()
        return super(Property, self).unlink()

    def action_register(self):
        """
        Set Property To register
        :return:
        """
        self.write({'state': 'register'})

    def action_approve(self):
        """
        set Property to approve
        :return:
        """
        self.write({'state': 'approve'})

    def action_draft(self):
        """
        set property state to draft if its not reserved or rented
        :return:
        """
        state = dict(self.fields_get(allfields=['state'])['state']['selection'])[self.state]
        if self.state not in ('reserve', 'rent'):
            self.write({'state': 'draft'})
        else:
            raise exceptions.ValidationError(
                _("You Cannot set the state of property to draft because it in state %s") % state)

    @api.model
    def create(self, values):
        """
        Inherit create operation to set a sequence for a property
        :param values: values while creating a record
        :return: record set
        """
        values['seq'] = self.env['ir.sequence'].next_by_code('res.property')
        return super(Property, self).create(values)

    @api.constrains('water_serial', 'water_subscription', 'water_account')
    def fields_check(self):
        """
        Check if name field contain an invalid value
        :raise exception
        """
        num_pattern = re.compile(r'\d', re.I | re.M)
        white_space = re.compile(r'^\s')
        if self.water_subscription:
            if not num_pattern.search(self.water_subscription):
                raise exceptions.ValidationError(_("Water subscription field accept numbers or special character only"))
            if white_space.search(self.water_subscription):
                raise exceptions.ValidationError(_("Water subscription (cannot accept white space)"))
        if self.water_account:
            if not num_pattern.search(self.water_account):
                raise exceptions.ValidationError(_("Water account field accept numbers or special character only"))
            if white_space.search(self.water_account):
                raise exceptions.ValidationError(_("Water account (cannot accept white space)"))
        if self.water_serial:
            if not num_pattern.search(self.water_serial):
                raise exceptions.ValidationError(_("Water serial field accept numbers or special character only"))
            if white_space.search(self.water_serial):
                raise exceptions.ValidationError(_("Water serial (cannot accept white space)"))

    @api.constrains('meter_price', 'property_space', 'floors_count', 'property_cost')
    def check_number(self):
        """
        If the number less than zero then raise error
        :return:
        """
        if self.property_space < 0.0:
            raise exceptions.ValidationError(_("Property space cannot be less than zero"))
        if self.meter_price < 0.0:
            raise exceptions.ValidationError(_("Meter price cannot be less than zero"))
        if self.property_cost < 0.0:
            raise exceptions.ValidationError(_("Property cost cannot be less than zero"))
        if self.floors_count < 0:
            raise exceptions.ValidationError(_("Floors count cannot be less than zero"))

    @api.depends('unit_ids', 'unit_ids.state')
    def count_unit_number(self):
        for rec in self:
            rec.no_units = len(rec.unit_ids)
            rec.no_available_units = len([unit for unit in rec.unit_ids if unit.state in ['available', 'draft']])
            rec.no_reserved_units = len([unit for unit in rec.unit_ids if unit.state == 'reserved'])
            rec.no_rented_units = len([unit for unit in rec.unit_ids if unit.state == 'rented'])

    @api.depends('meter_price', 'property_space')
    def get_rent_price(self):
        """
        Get rent Price Per Meter
        :return: total rent price
        """
        for record in self:
            record.rent_price = record.meter_price * record.property_space

    def action_toggle_is_locked(self):
        self.ensure_one()
        if self.unlock:
            self.write({'unlock': False})
        else:
            self.write({'unlock': True})


class PropertyUnitDetails(models.Model):
    _name = 'floor.unit.details'
    _description = 'Floor Unit Details'

    role_id = fields.Many2one(comodel_name='property.role', string='Roles', )
    property_id = fields.Many2one('internal.property', string='Property', required=True, ondelete='cascade')
    no_of_house = fields.Integer(string='No of Housees')
    no_of_shop = fields.Integer(string='No of Shops')
    no_of_other_unit = fields.Integer(string='No of Other Units')
    description = fields.Char(string='Description')
    total = fields.Integer(string='Total', compute='_compute_total', store=True, readonly=True)

    @api.depends('no_of_house', 'no_of_shop', 'no_of_other_unit')
    def _compute_total(self):
        for record in self:
            record.total = record.no_of_house + record.no_of_shop + record.no_of_other_unit

# -*- coding: utf-8 -*-
##############################################################################
#
#   Expert (LCT, Life Connection Technology)
#    Copyright (C) 2021-2022 LCT
#
##############################################################################

from odoo.exceptions import ValidationError
from odoo import models, fields, api, _

class RePricing(models.Model):
    _name = "re.pricing"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Pricing"

    name = fields.Char(string="Description")
    property_id = fields.Many2one('internal.property', string="Property")
    city = fields.Many2one(related='property_id.city_id', string='City')
    district = fields.Many2one(related='property_id.district_id',
                               string='District')
    type = fields.Many2one('internal.property.type', related='property_id.property_type_id',
                           string='Property Type')
    size = fields.Float(related='property_id.property_space', string='Property Size')
    date = fields.Date(string='Date', required=True, default=lambda self: fields.Date.context_today(self))
    value = fields.Float(string='Value', )
    value_per_meter = fields.Float(string='Value per meter', )
    notes = fields.Text('Notes')
    offered = fields.Boolean('Offered', default=True)
    company_id = fields.Many2one('res.company', 'Company', required=True, select=1,
                                 help="Company related to this journal", default=lambda self: self.env.user.company_id.id)

    @api.constrains('value')
    def check_non_zero_value_from(self):
        for record in self:
            if record.value <= 0:
                raise  ValidationError(_("Value cannot be less than zero or equal"))

    @api.onchange('value')
    def onchange_value(self):
        if self.value and self.size:
            self.value_per_meter = self.value / self.size

    @api.onchange('property')
    def onchange_property(self):
        if self.property_id:
            self.city = self.property_id.city_id.id
            self.district = self.property_id.district_id.id
            self.type = self.property_id.property_type_id.id
            self.size = self.property_id.property_space





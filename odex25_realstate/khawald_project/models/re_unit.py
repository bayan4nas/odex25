# -*- coding: utf-8 -*-
##############################################################################
#
#   Expert (LCT, Life Connection Technology)
#    Copyright (C) 2021-2022 LCT
#
##############################################################################

from odoo import models, fields, api, _

class ReUnit(models.Model):
    _inherit = "re.unit"

    project_id = fields.Many2one('project.project', string="Project")
    change_price = fields.Boolean(string="Change Meter Price", tracking=True)
    new_price = fields.Float(string="New Price", tracking=True)
    meter_price = fields.Float(string="Meter Price", store=True, digits=(16, 2), tracking=True)
    rent_price = fields.Float(string="Total Price", compute="get_rent_price", tracking=True, store=True)
    advantage_ids = fields.Many2many('project.advantage', related="project_id.advantage_ids", string="Advantage",
                                     ondelete="cascade")

    @api.depends('external_space', 'change_price', 'meter_price', 'new_price', 'advantage_ids', 'advantage_ids.price')
    def get_rent_price(self):
        rent_price = 0.0
        advantage_price = 0.0
        for rec in self:
            if rec.advantage_ids:
                advantage_price = sum([rec.price for rec in self.advantage_ids])
            if rec.meter_price:
                rent_price = rec.meter_price * rec.space
            if rec.external_price and rec.external_space:
                rent_price += rec.external_space * rec.external_price
            if rec.change_price:
                rent_price = rec.new_price
            rec.rent_price = rent_price + advantage_price

# -*- coding: utf-8 -*-
##############################################################################
#
#   Expert (LCT, Life Connection Technology)
#    Copyright (C) 2021-2022 LCT
#
##############################################################################

from odoo import models, fields, api, _

class InternalProperty(models.Model):
    _inherit = "internal.property"

    project_id = fields.Many2one('project.project', string="Project")
    advantage_ids = fields.Many2many('project.advantage', related="project_id.advantage_ids", string="Advantage",
                                     ondelete="cascade")
    advantage_price = fields.Float(string="Advantage Price", compute="get_advantage_price")
    electric_service = fields.Selection([('issued', 'Issued'),
                                         ('not', 'Not Issued')], string="Electric Service", default='not')
    water_service = fields.Selection([('issued', 'Issued'),
                                      ('not', 'Not Issued')], string="Water Service", default='not')
    stamp_service = fields.Selection([('issued', 'Issued'),
                                      ('not', 'Not Issued')], string="Stamp Service", default='not')
    building_service = fields.Selection([('issued', 'Issued'),
                                         ('not', 'Not Issued')], string="Building Certificate", default='not')

    @api.depends('property_space', 'meter_price', 'advantage_price')
    def get_total_price(self):
        for rec in self:
            rec.total_price = rec.advantage_price + (rec.meter_price * rec.property_space)

    @api.depends('advantage_ids', 'advantage_ids.price')
    def get_advantage_price(self):
        price = 0.0
        for rec in self:
            if rec.advantage_ids:
                price = sum([line.price for line in rec.advantage_ids])
            rec.advantage_price = price

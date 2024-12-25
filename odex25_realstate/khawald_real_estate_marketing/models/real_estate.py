# -*- coding: utf-8 -*-
##############################################################################
#
#   Expert (LCT, Life Connection Technology)
#    Copyright (C) 2021-2022 LCT
#
##############################################################################

from odoo import models, fields, api, _
from datetime import date


class Property(models.Model):
    _inherit = 'internal.property'
    
    # contract_id = fields.Many2one('contract.contract', string="Contract")


class Unit(models.Model):
    _inherit = 're.unit'

    state = fields.Selection([('draft', 'Draft'),
                              ('available', 'Available'),
                              ('reserved', 'Reserved'),
                              ('with', 'With Down Payment'),
                              ('without', 'Without Down Payment'),
                              ('handover', 'Handover to client'),
                              ('emptied', 'Emptied'),
                              ('sold', 'Sold')], string="Status", default='draft')
    waiting_ids = fields.One2many('re.unit.waiting', 'unit_id', string="Waiting List")
    handover_to_client_date = fields.Date('Handover to Client Date', index=True)
    emptied_date = fields.Date('Emptied Date', index=True)
    # sale_contract_id = fields.Many2one('contract.contract', string="Contract")
    sale_contract_counts = fields.Integer(compute="compute_sale_contract_count")

    # def get_related_contract(self):
    #     self.ensure_one()
    #     contracts = (self.env['contract.contract'].search([('unit_id', '=', self.id)]))
    #     return contracts

    # def compute_sale_contract_count(self):
    #     for item in self:
    #         item.sale_contract_counts = len(item.get_related_contract())

    def action_unit_emptied(self):
        for record in self:
            record.state = 'emptied'
            record.emptied_date = date.today()

    # def action_view_contract(self):
    #     contract_ids = self.env['contract.contract'].search([('unit_id', '=', self.id)])
    #     form_id = self.env.ref('contract.contract_contract_form_view').id
    #     tree_id = self.env.ref('contract.contract_contract_tree_view').id
    #     domain = [('id', 'in', contract_ids.ids)]
    #     return {
    #         'name': _('Contractor Contract'),
    #         'view_type': 'form',
    #         'view_mode': 'form',
    #         'res_model': 'contract.contract',
    #         'views': [(tree_id, 'tree'), (form_id, 'form')],
    #         'type': 'ir.actions.act_window',
    #         'target': 'current',
    #         'domain': domain,
    #     }


class UnitWaiting(models.Model):
    _name = 're.unit.waiting'
    _rec_name = 'unit_id'

    unit_id = fields.Many2one('re.unit', string="Units", tracking=True)
    partner_id = fields.Many2one('res.partner', string="Client")


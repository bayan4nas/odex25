# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class PurcahseRefues(models.TransientModel):
    _name = "purchase.request_picking.wizard"
    _description = "purchase Checking Options wizard"

    request_id = fields.Many2one('purchase.request')
    request_line_ids = fields.Many2many('purchase.request.line')
    is_available = fields.Boolean("Available")
    show_purchase_only = fields.Boolean("Show Purchase Only", compute='_compute_show_purchase_only')

    @api.depends('request_line_ids', 'request_id')
    def _compute_show_purchase_only(self):
        self.show_purchase_only = all(line.available_qty <= 0 for line in self.request_line_ids)

    def delivery_close(self):
        picking_id = self.env.ref('purchase_custom_stock.stock_picking_type_stock')
        picking_vals = {
            "picking_type_id": self.env.ref('purchase_custom_stock.stock_picking_type_stock').id,
            "origin": self.request_id.name,
            "location_id": self.request_id.location_id.id,
            "location_dest_id": picking_id.default_location_dest_id.id
        }

        move_vals = []
        for line in self.request_line_ids:
            move_vals.append((0, 0, {
                "product_id": line.product_id.id,
                "name": line.product_id.name,
                "product_uom": line.product_id.uom_id.id,
                'product_uom_qty': line.qty,
            }))
        picking_vals.update({'move_lines': move_vals})
        picking_id = self.env['stock.picking'].create(picking_vals)
        self.request_id.picking_id = picking_id.id
        self.request_id.write({'state': 'employee'})

    def delivery_purchase(self):
        if self.request_line_ids.filtered(
                lambda line: line.product_id.type == 'product') or self.request_line_ids.filtered(
                lambda line: line.product_id.type == 'consu' and not line.product_id.asset_ok):
            picking_id = self.env.ref('purchase_custom_stock.stock_picking_type_stock')
            picking_vals = {
                "picking_type_id": self.env.ref('purchase_custom_stock.stock_picking_type_stock').id,
                "origin": self.request_id.name,
                "location_id": self.request_id.location_id.id,
                "location_dest_id": picking_id.default_location_dest_id.id
            }

            move_vals = []
            for line in self.request_line_ids.filtered(lambda line: line.product_id.type in ['product', 'consu']):
                if not line.product_id.asset_ok:
                    if line.qty < line.available_qty:
                        move_vals.append((0, 0, {
                            "product_id": line.product_id.id,
                            "name": line.product_id.name,
                            "product_uom": line.product_id.uom_id.id,
                            'product_uom_qty': line.qty,
                        }))
                        line.qty_purchased = 0
                    else:
                        if line.available_qty > 0:
                            move_vals.append((0, 0, {
                                "product_id": line.product_id.id,
                                "name": line.product_id.name,
                                "product_uom": line.product_id.uom_id.id,
                                'product_uom_qty': line.qty,
                            }))
                        line.qty_purchased = line.qty - line.available_qty
            picking_vals.update({'move_lines': move_vals})
            picking_id = self.env['stock.picking'].create(picking_vals)
            self.request_id.picking_id = picking_id.id
        init_active = self.env['ir.module.module'].sudo().search(
            [('name', '=', 'initial_engagement_budget'), ('state', '=', 'installed')], limit=1)
        init_budget = True if init_active else False
        for line in self.request_line_ids.filtered(lambda line: line.product_id.type not in ['product', 'consu']):
            line.qty_purchased = line.qty
        self.request_id.write({'state': 'wait_for_send' if init_budget else 'waiting'})

    def convert_purchase(self):
        if self.request_line_ids.filtered(
                lambda line: line.product_id.type == 'product') or self.request_line_ids.filtered(
            lambda line: line.product_id.type == 'consu' and not line.product_id.asset_ok):
            picking_id = self.env.ref('purchase_custom_stock.stock_picking_type_stock')
            picking_vals = {
                "picking_type_id": self.env.ref('purchase_custom_stock.stock_picking_type_stock').id,
                "origin": self.request_id.name,
                "location_id": self.request_id.location_id.id,
                "location_dest_id": picking_id.default_location_dest_id.id
            }
            move_vals = []

            for line in self.request_line_ids.filtered(lambda line: line.product_id.type in ['product', 'consu']):
                if not line.product_id.asset_ok:
                    move_vals.append((0, 0, {
                        "product_id": line.product_id.id,
                        "name": line.product_id.name,
                        "product_uom": line.product_id.uom_id.id,
                        'product_uom_qty': line.qty,
                    }))
            picking_vals.update({'move_lines': move_vals})
            picking_id = self.env['stock.picking'].create(picking_vals)
            self.request_id.picking_id = picking_id.id
        init_active = self.env['ir.module.module'].sudo().search(
            [('name', '=', 'initial_engagement_budget'), ('state', '=', 'installed')], limit=1)
        init_budget = True if init_active else False
        for line in self.request_line_ids:
            line.qty_purchased = line.qty - line.available_qty
        self.request_id.write({'state': 'wait_for_send' if init_budget else 'waiting'})

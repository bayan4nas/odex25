# -*- coding: utf-8 -*-
##############################################################################
#
#   Expert (LCT, Life Connection Technology)
#    Copyright (C) 2021-2022 LCT
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ProjectEstimatedQuantities(models.Model):
    _name = 'project.estimated.quantities'
    _description = "Project Estimated Quantities"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if values.get('display_type', self.default_get(['display_type'])['display_type']):
                values.update(quantity=False, uom_id=False, unit_price=False, )
        return super(ProjectEstimatedQuantities, self).create(vals_list)

    def write(self, values):
        if 'display_type' in values and self.filtered(lambda line: line.display_type != values.get('display_type')):
            raise UserError(_(
                "You cannot change the type of a Project Estimated Quantities. Instead you should delete the current line and create a new line of the proper type."))
        return super(ProjectEstimatedQuantities, self).write(values)

    work_item_id = fields.Many2one('work.item', string="Work item")
    name = fields.Char(string='Description')
    sub_work_item_id = fields.Many2one('sub.work.item', string='Sub work item')
    work_detail_id = fields.Many2one('detailed.work.item', string="Detailed Work item")
    work_attached_id = fields.Many2one('work.attached', string="Work Attached")
    quantity = fields.Float(string="Quantity", default=1, digits=(16, 2))
    uom_id = fields.Many2one('uom.uom', string="Unit of measure")
    unit_price = fields.Float(string="Unit Price", digits=(16, 2))
    total_estimated_qty = fields.Float(string="Total estimated quantity", compute='compute_total', digits=(16, 2))
    project_id = fields.Many2one("project.project", string="Project")
    subcontractor_id = fields.Many2one("subcontractor.work", sgtring="Subcontractor ")
    from_subcontractor = fields.Boolean(string="Line Created From Subcontractor Work")
    duplicated = fields.Boolean(string="Duplicated")
    description = fields.Char(string="Work Description")
    work_amount = fields.Float(string="Subcontractor Work Amount")
    display_type = fields.Selection([
        ('line_section', "Section"),
        ('line_note', "Note")], default=False, help="Technical field for UX purpose.")

    @api.onchange('work_item_id')
    def onchange_work_item(self):
        for record in self:
            record.sub_work_item_id = False
            record.work_detail_id = False

    @api.onchange('sub_work_item_id')
    def onchange_sub_work_item(self):
        for record in self:
            record.work_detail_id = False

    @api.depends('quantity', 'unit_price')
    def compute_total(self):
        price_unit = 0.0
        for record in self:
            record.total_estimated_qty = round(record.quantity * record.unit_price, 2)

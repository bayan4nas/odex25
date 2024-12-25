# -*- coding: utf-8 -*-
##############################################################################
#
#   Expert (LCT, Life Connection Technology)
#    Copyright (C) 2021-2022 LCT
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class WorkItem(models.Model):
    _name = 'work.item'

    name = fields.Char(string="Name")
    sequence = fields.Char(string="Sequence")
    # work_ids = fields.One2many('sub.work.item', 'work_id', string="Works")
    type = fields.Selection([('item', 'Work Item'),
                             ('sub', 'Sub work'),
                             ('detailed', 'Detailed work')], string="Type")

    def unlink(self):
        for record in self:
            estimated_quantities_ids = self.env['project.estimated.quantities'].search(
                [('work_item_id', '=', record.id)])
            if estimated_quantities_ids:
                raise ValidationError(_("This Record Cannot Be Deleted"))
            # if record.work_ids:
            #    raise ValidationError(_("This Record Cannot Be Deleted"))
        return super(WorkItem, self).unlink()


class SubWorkItem(models.Model):
    _name = 'sub.work.item'
    _description = "Sub Work Items"

    name = fields.Char(string="Name")
    sequence = fields.Char(string="Sequence")
    work_id = fields.Many2one('work.item', string="Work Item")
    detailed_work_item_ids = fields.One2many('detailed.work.item', 'sub_work_item_id', string="Detailed Item")
    type = fields.Selection([('item', 'Work Item'),
                             ('sub', 'Sub Work'),
                             ('detailed', 'Detailed Work')], string='Type')

    def unlink(self):
        for record in self:
            search_ids = self.env['project.estimated.quantities'].search([('sub_work_item_id', '=', record.id)])
            if search_ids:
                raise ValidationError(_("This Record Cannot Be Deleted"))
            if record.detailed_work_item_ids:
                raise ValidationError(_("This Record Cannot Be Deleted"))
        return super(SubWorkItem, self).unlink()


class DetailedWorkItem(models.Model):
    _name = 'detailed.work.item'
    _description = "DetailedWorkItem"

    name = fields.Char(string="Name")
    sequence = fields.Char(string="Sequence")
    sub_work_item_id = fields.Many2one('sub.work.item', string="Sub Work Item")
    type = fields.Selection([('item', 'Work Item'),
                             ('sub', 'Sub Work'),
                             ('detailed', 'Detailed Work')], string="Type")

    def unlink(self):
        for record in self:
            search_ids = self.env['project.estimated.quantities'].search([('work_detail_id', '=', record.id)])
            if search_ids:
                raise ValidationError(_("This Record Cannot Be Deleted"))
        return super(DetailedWorkItem, self).unlink()


class WorkAttached(models.Model):
    _name = 'work.attached'
    _description = "Work Attached"

    name = fields.Char(string="Description")
    work_attached_ids = fields.One2many('work.attached.line', 'work_attached_id', string='Work Attached')
    total_work = fields.Float(_string="Total", compute='compute_total')
    estimated_quantities_id = fields.Many2one('project.estimated.quantities', string="Estimated Quantity")
    project_id = fields.Many2one('project.project', string="Project")
    work_item_id = fields.Many2one('work.item', string="Work Item", related='estimated_quantities_id.work_item_id')
    work_description = fields.Many2one('detailed.work.item', string="Detailed Work",
                                       related='estimated_quantities_id.work_detail_id')
    sub_work_item_id = fields.Many2one('sub.work.item', string="Sub Work",
                                       related='estimated_quantities_id.sub_work_item_id')

    @api.depends('work_attached_ids')
    def compute_total(self):
        for record in self:
            record.total_work_attached = 0
            for line in record.work_attached_ids:
                record.total_work_attached += line.total_work_attached_line

    @api.model
    def create(self, vals):
        # default_project_estimated_quantities_id
        project_estimated = False
        if self._context.has_key('default_estimated_quantities_id'):
            project_estimated = self.env['project.estimated.quantities'].browse(self._context[
                                                                                    'default_estimated_quantities_id'])
            project_id = project_estimated.project_id.id or False
            vals.update({
                'estimated_quantities_id': self._context.get('default_estimated_quantities_id'),
                'project_id': project_id,
            })
        res = super(WorkAttached, self).create(vals)
        if project_estimated:
            project_estimated.write({'work_attached_id': res.id})
        return res


class WorkAttachedLine(models.Model):
    _name = 'work.attached.line'
    _description = "Work Attached Line"
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.template', string="Product")
    work_description = fields.Text(string="Work Description")
    work_attached_id = fields.Many2one('work.attached', string="Work Attached")
    estimated_quantities_id = fields.Many2one('project.estimated.quantities', string="Project Estimated Quantity",
                                              related='work_attached_id.estimated_quantities_id')
    project_id = fields.Many2one('project.project', string="Project", related='work_attached_id.project_id')
    quantity = fields.Float(string="Quantity")
    uom_id = fields.Many2one('product.uom', string="Product UOM")
    unit_price = fields.Float(string="Unit Price")
    total_work_attached_line = fields.Float(string="Total", compute='compute_total')

    @api.onchange('product_id')
    def onchange_product(self):
        for record in self:
            record.uom_id = record.product_id.uom_id.id or False

    @api.depends('quantity', 'unit_price')
    def compute_total(self):
        for record in self:
            record.total_work_attached_line = record.unit_price * record.qty

# -*- coding: utf-8 -*-

from odoo import models, fields,api,_, exceptions
from odoo.exceptions import ValidationError
import re


class odex25_budget_saip(models.Model):
    _name = 'item.budget'
    _inherit = ['mail.thread']
    _description = 'Budget Item'

    name = fields.Char()
    item_no = fields.Char()
    item_type = fields.Selection([("cabex", "Cabex"), ("operational", "Operational")], string="Item Type")
    period = fields.Selection([("annually", "Annually"), ("not_annually", "Not Annually")], string="Period")
    crossovered_budget_line = fields.One2many('crossovered.budget.lines', 'item_budget_id', 'Budget Lines')

    @api.constrains('item_no')
    def _check_unique_item_no(self):
        for record in self:
            if record.item_no:
                existing_records = self.search([('item_no', '=', record.item_no), ('id', '!=', record.id)])
                if existing_records:
                    raise ValidationError(_('The item number must be unique!'))

    @api.constrains('item_no')
    def _check_item_no_is_integer(self):
        for record in self:
            if record.item_no and not record.item_no.isdigit():
                raise ValidationError(_("The item budget Number must contain digits only"))

    @api.constrains('name')
    def _check_name_is_arabic_only(self):
        allowed_regex = re.compile(r'^[\u0600-\u06FFA-Za-z\s]+$')
        for record in self:
            if record.name and not allowed_regex.match(record.name):
                pass
                # raise ValidationError(_("item budget Name must contain letters only (no digits or special characters)."))

    def name_get(self):
        result = []
        for rec in self:
            result.append((rec.id, '%s - %s' % (rec.item_no, rec.name)))
        return result

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('item_no', operator, name), ('name', operator, name)]
        records = self.search(domain + args, limit=limit)
        return records.name_get()

    # todo start
    def unlink(self):
        for item in self:
            if len(item.crossovered_budget_line)>0:
                raise exceptions.Warning(_('You cannot delete an item budget which is related budget.'))
        return super(odex25_budget_saip, self).unlink()
    # todo end
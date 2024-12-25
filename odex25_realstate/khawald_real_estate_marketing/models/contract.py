# -*- coding: utf-8 -*-

from odoo.exceptions import ValidationError, UserError, Warning
from odoo import models, fields, api, exceptions, tools, _
from datetime import datetime, date


class ContractContract(models.Model):
    _inherit = "contract.contract"

    sale_id = fields.Many2one('re.sale', string="Sale Order")
    property_id = fields.Many2one('internal.property', string="Property")
    unit_id = fields.Many2one('re.unit', string="Unit")
    total_sale_amount = fields.Float(string='Total Sale Amount', digits=(16, 2))
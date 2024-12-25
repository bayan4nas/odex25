# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class PurchaseRequisition(models.Model):
    _inherit = 'purchase.requisition'

    agreement_name = fields.Char()
    agreement_number = fields.Char()
    agreement_date = fields.Date()
    # oveeride purchase_cost field to set default value
    purchase_cost = fields.Selection([('department', 'Department'), ('default', 'Default Cost Center'),('product_line', 'Product Line'), ('project', 'Project')],default='department',string='Purchase Cost')
    # end
    city = fields.Char()

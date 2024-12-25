# -*- coding: utf-8 -*-
##############################################################################
#
#    (Odex - Extending the base module).
#    Copyright (C) 2024 Expert Co. Ltd. (<http://exp-sa.com>).
#
##############################################################################

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class kpi_category(models.Model):

    _inherit = "kpi.category"

    code = fields.Char(string="Code")
    weight = fields.Float(string="Weight")
    type = fields.Selection([
        ("pillar", "Pillar"), 
        ("st_goal", "Strategic Goal"),
        ("op_goal", "Operational Goal"),
        ("other", "Other")],string="Type", default="op_goal")

    def name_get(self):
        return super(models.Model, self).name_get()
        
        
    def write(self, data):
        res = super(kpi_category, self).write(data)
        if data.get('weight'):
            self.env["kpi.item"].compute_automated_weight(self)
        return res



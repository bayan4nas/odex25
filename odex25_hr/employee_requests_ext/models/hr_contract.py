# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class HRContractExt(models.Model):
    _inherit = 'hr.contract'


    field_allowance_custom = fields.Float(store=True)
    other_allowance_custom  = fields.Float(store=True)



    @api.depends('field_allowance_custom', 'other_allowance_custom')
    def compute_function(self):
        super(HRContractExt, self).compute_function()
        for i in self:
            # if i.field_allowance_custom > 0 or i.other_allowance_custom > 0:
            i.total_allowance += i.field_allowance_custom + i.other_allowance_custom
            i.total_net = i.total_allowance + i.total_deduction

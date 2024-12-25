# -*- coding: utf-8 -*-
##############################################################################
#
#   Expert (LCT, Life Connection Technology)
#    Copyright (C) 2021-2022 LCT
#
##############################################################################

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ResPartner(models.Model):
    _inherit = 'res.partner'

    date_of_birth = fields.Date(string='Date Of Birth')

    @api.constrains('mobile')
    def check_unique_phone(self):
        for rec in self:
            if rec.mobile:
                exists_phone = self.env['res.partner'].sudo().search([('id', '!=', rec.id), ('mobile', '=', rec.mobile)])
                if exists_phone:
                    raise ValidationError(_('Mobile number must be unique'))
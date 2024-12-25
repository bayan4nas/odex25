# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class ResSetting(models.TransientModel):
    _inherit = 'res.config.settings'

    attachment_booklet_exp = fields.Binary(string='file', readonly=False, related="company_id.attachment_booklet_exp",
                                           attachment=True, help='Upload Booklet file')


class Company(models.Model):
    _inherit = 'res.company'

    attachment_booklet_exp = fields.Binary(
        string='file', readonly=False, attachment=True, help='Upload Booklet file')

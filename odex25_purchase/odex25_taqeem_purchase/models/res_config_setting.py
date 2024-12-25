# -*- coding: utf-8 -*-
import base64
import ast

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from ast import literal_eval


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    attachment_scop = fields.Binary(related="company_id.attachment_scop",string='Application brochure',readonly=False)
    day = fields.Integer(
        string='Day', related="company_id.day", readonly=False)
    month = fields.Integer(
        string='Month', related="company_id.month", readonly=False)
    year = fields.Integer(
        string='Year', related="company_id.year", readonly=False)

    # @api.model
    # def get_values(self):
    #     res = super(ResConfigSettings, self).get_values()
    #     res['day'] = int(
    #         self.env['ir.config_parameter'].sudo().get_param('odex25_taqeem_purchase.day', default=14))
    #     res['month'] = int(
    #         self.env['ir.config_parameter'].sudo().get_param('odex25_taqeem_purchase.month', default=0))
    #     res['year'] = int(
    #         self.env['ir.config_parameter'].sudo().get_param('odex25_taqeem_purchase.year', default=0))
    #     # res['attachment_scop'] = self.env['ir.config_parameter'].sudo().get_param('odex25_taqeem_purchase.attachment_scop', default=0)

    #     return res

    # @api.model
    # def set_values(self):
    #     self.env['ir.config_parameter'].sudo().set_param('odex25_taqeem_purchase.day', self.day)
    #     self.env['ir.config_parameter'].sudo().set_param('odex25_taqeem_purchase.month', self.month)
    #     self.env['ir.config_parameter'].sudo().set_param('odex25_taqeem_purchase.year', self.year)
    #     self.env['ir.config_parameter'].sudo().set_param('odex25_taqeem_purchase.attachment_scop', self.attachment_scop)

    #     super(ResConfigSettings, self).set_values()

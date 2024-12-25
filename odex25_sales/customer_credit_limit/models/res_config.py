# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    percent_limit_a = fields.Float(string='First Level Percent Limit ',)
    amount_limit_a = fields.Float(string='First Level Amount Limit',)
    percent_limit_b = fields.Float(string='Second Level Percent Limit ',)
    amount_limit_b = fields.Float(string='Second Level Amount Limit',)
    percent_limit_c = fields.Float(string='Third Level Percent Limit ',)
    amount_limit_c = fields.Float(string='Third Level Amount Limit',)
    percent_limit_d = fields.Float(string='Fourth Level Percent Limit ',)
    amount_limit_d = fields.Float(string='Fourth Level Amount Limit',)
    
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            percent_limit_a=float(self.env['ir.config_parameter'].
                                             get_param('percent_limit_a')),
            amount_limit_a=float(self.env['ir.config_parameter'].
                                             get_param('amount_limit_a')),

            percent_limit_b=float(self.env['ir.config_parameter'].
                                             get_param('percent_limit_b')),
            amount_limit_b=float(self.env['ir.config_parameter'].
                                             get_param('amount_limit_b')),

            percent_limit_c=float(self.env['ir.config_parameter'].
                                             get_param('percent_limit_c')),
            amount_limit_c=float(self.env['ir.config_parameter'].
                                             get_param('amount_limit_c')),

            percent_limit_d=float(self.env['ir.config_parameter'].
                                             get_param('percent_limit_d')),
            amount_limit_d=float(self.env['ir.config_parameter'].
                                             get_param('amount_limit_d')),

        )
        return res

    def set_values(self):
         super(ResConfigSettings, self).set_values()
         # self.env['ir.config_parameter'].set_param('ks_enable_discount', self.ks_enable_discount)
         # if self.ks_enable_discount:
         self.env['ir.config_parameter'].set_param('percent_limit_a', self.percent_limit_a)
         self.env['ir.config_parameter'].set_param('amount_limit_a', self.amount_limit_a)
         self.env['ir.config_parameter'].set_param('percent_limit_b', self.percent_limit_b)
         self.env['ir.config_parameter'].set_param('amount_limit_b', self.amount_limit_b)
         self.env['ir.config_parameter'].set_param('percent_limit_c', self.percent_limit_c)
         self.env['ir.config_parameter'].set_param('amount_limit_c', self.amount_limit_c)
         self.env['ir.config_parameter'].set_param('percent_limit_d', self.percent_limit_d)
         self.env['ir.config_parameter'].set_param('amount_limit_d', self.amount_limit_d)

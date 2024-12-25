# -*- coding: utf-8 -*-
##############################################################################
#
#   Expert (LCT, Life Connection Technology)
#    Copyright (C) 2021-2022 LCT
#
##############################################################################

from odoo import models, api, fields, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    commission_account_id = fields.Many2one('account.account', string='Commission account')
    commission_journal_id = fields.Many2one('account.journal', string='Commission Journal')
    re_sale_journal_id = fields.Many2one('account.journal', string='Sales Journal')
    intermediary_commission_account_id = fields.Many2one('account.account', string='Intermediary Commission account')
    included_by_commission_account_id = fields.Many2one('account.account', string='Included By Commission account')

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res['re_sale_journal_id'] = int(self.env['ir.config_parameter'].sudo().get_param('real_estate_marketing.re_sale_journal_id'))
        res['commission_account_id'] = int(self.env['ir.config_parameter'].sudo().get_param('real_estate_marketing.commission_account_id'))
        res['commission_journal_id'] = int(self.env['ir.config_parameter'].sudo().get_param('real_estate_marketing.commission_journal_id'))
        res['intermediary_commission_account_id'] = int(self.env['ir.config_parameter'].sudo().get_param('real_estate_marketing.intermediary_commission_account_id'))
        res['included_by_commission_account_id'] = int(self.env['ir.config_parameter'].sudo().get_param('real_estate_marketing.included_by_commission_account_id'))

        return res

    def set_values(self):
        self.env['ir.config_parameter'].sudo().set_param("real_estate_marketing.re_sale_journal_id", self.re_sale_journal_id.id or False)
        self.env['ir.config_parameter'].sudo().set_param("real_estate_marketing.commission_account_id", self.commission_account_id.id or False)
        self.env['ir.config_parameter'].sudo().set_param("real_estate_marketing.commission_journal_id", self.commission_journal_id.id or False)
        self.env['ir.config_parameter'].sudo().set_param("real_estate_marketing.intermediary_commission_account_id", self.intermediary_commission_account_id.id or False)
        self.env['ir.config_parameter'].sudo().set_param("real_estate_marketing.included_by_commission_account_id", self.included_by_commission_account_id.id or False)

        super(ResConfigSettings, self).set_values()

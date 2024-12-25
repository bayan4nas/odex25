from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    benefit_partner_id = fields.Many2one('res.partner')
    ##### receive zkat alfert ########
    receive_zkat_bank_account_id = fields.Many2one('account.account', string="Bank Account For zkat")
    receive_zkat_journal_id = fields.Many2one('account.journal', string="Journal For zkat")
    receive_zkat_picking_type_id = fields.Many2one('stock.picking.type', 'Picking Type For Receive zkat')
    #####  zkat alfert ########
    zkat_picking_type_id = fields.Many2one('stock.picking.type', 'Picking Type For zkat')
    ########استلامات الاضاحي###########
    receive_Adha_bank_account_id = fields.Many2one('account.account', string="Bank Account For Adha")
    receive_Adha_journal_id = fields.Many2one('account.journal', string="Journal For Adha")
    receive_Adha_picking_type_id = fields.Many2one('stock.picking.type', "Picking Type For Receive Adha")
    #####  الاضاحي ########
    Adha_picking_type_id = fields.Many2one('stock.picking.type', "Picking Type For Adha")
    ############## receive.appliances.furniture#######
    receive_af_picking_type_id = fields.Many2one('stock.picking.type', "Picking Type For Receive af")
    ############## appliances.furniture#######
    Af_picking_type_id = fields.Many2one('stock.picking.type', "Picking Type For  af")
    ###############R lons#############
    receive_loan_bank_account_id = fields.Many2one('account.account', string="Bank Account For Receive loan")
    receive_loan_journal_id = fields.Many2one('account.journal', string="Journal For Receive loan")
    ###############lons#############
    loan_bank_account_id = fields.Many2one('account.account', string="Bank Account For loan")
    loan_journal_id = fields.Many2one('account.journal', string="Journal  For Receive loan")

    # @api.multi
    def set_values(self):
        res = super(ResConfigSettings, self).set_values()
        param = self.env['ir.config_parameter'].sudo()
        benefit_partner_id = self.benefit_partner_id or False
        receive_zkat_bank_account_id = self.receive_zkat_bank_account_id.id or False
        receive_zkat_journal_id = self.receive_zkat_journal_id or False
        receive_zkat_picking_type_id = self.receive_zkat_picking_type_id or False
        zkat_picking_type_id = self.zkat_picking_type_id or False
        receive_Adha_bank_account_id = self.receive_Adha_bank_account_id or False
        receive_Adha_journal_id = self.receive_Adha_journal_id or False
        Adha_picking_type_id = self.Adha_picking_type_id or False
        receive_af_picking_type_id = self.Adha_picking_type_id or False
        Af_picking_type_id = self.Af_picking_type_id or False
        receive_loan_bank_account_id = self.receive_loan_bank_account_id or False
        receive_loan_journal_id = self.receive_loan_journal_id or False
        loan_bank_account_id = self.loan_bank_account_id or False
        loan_journal_id = self.loan_bank_account_id or False
        param.set_param('odex_benefit.benefit_partner_id', benefit_partner_id)  # 1
        param.set_param('odex_benefit.receive_zkat_bank_account_id', receive_zkat_bank_account_id)  # 2
        param.set_param('odex_benefit.receive_zkat_journal_id', receive_zkat_journal_id)  # 3
        param.set_param('odex_benefit.receive_zkat_picking_type_id', receive_zkat_picking_type_id)  # 4
        param.set_param('odex_benefit.zkat_picking_type_id', zkat_picking_type_id)  # 5
        param.set_param('odex_benefit.receive_Adha_bank_account_id', receive_Adha_bank_account_id)  # 6
        param.set_param('odex_benefit.receive_Adha_journal_id', receive_Adha_journal_id)  # 7
        param.set_param('odex_benefit.Adha_picking_type_id', Adha_picking_type_id)  # 8
        param.set_param('odex_benefit.receive_af_picking_type_id', receive_af_picking_type_id)  # 9
        param.set_param('odex_benefit.Af_picking_type_id', Af_picking_type_id)  # 10
        param.set_param('odex_benefit.receive_loan_bank_account_id', receive_loan_bank_account_id)  # 11
        param.set_param('odex_benefit.receive_loan_journal_id', receive_loan_journal_id)  # 12
        param.set_param('odex_benefit.loan_bank_account_id', loan_bank_account_id)  # 13
        param.set_param('odex_benefit.loan_journal_id', loan_journal_id)  # 14
        return res

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        res.update(
            benefit_partner_id=params.sudo().get_param('odex_benefit.benefit_partner_id', default=""),
            receive_zkat_bank_account_id=params.sudo().get_param('odex_benefit.receive_zkat_bank_account_id',
                                                                 default=""),
            receive_zkat_journal_id=params.sudo().get_param('odex_benefit.receive_zkat_journal_id', default=""),
            receive_zkat_picking_type_id=params.sudo().get_param('odex_benefit.receive_zkat_picking_type_id',
                                                                 default=""),
            zkat_picking_type_id=params.sudo().get_param('odex_benefit.zkat_picking_type_id', default=""),
            receive_Adha_bank_account_id=params.sudo().get_param('odex_benefit.receive_Adha_bank_account_id',
                                                                 default=""),
            receive_Adha_journal_id=params.sudo().get_param('odex_benefit.receive_Adha_journal_id', default=""),
            Adha_picking_type_id=params.sudo().get_param('odex_benefit.Adha_picking_type_id', default=""),
            receive_af_picking_type_id=params.sudo().get_param('odex_benefit.receive_af_picking_type_id', default=""),
            Af_picking_type_id=params.sudo().get_param('odex_benefit.Af_picking_type_id', default=""),
            receive_loan_bank_account_id=params.sudo().get_param('odex_benefit.receive_loan_bank_account_id',
                                                                 default=""),
            receive_loan_journal_id=params.sudo().get_param('odex_benefit.receive_loan_journal_id', default=""),
            loan_bank_account_id=params.sudo().get_param('odex_benefit.loan_bank_account_id', default=""),
            loan_journal_id=params.sudo().get_param('odex_benefit.loan_journal_id', default=""),
        )
        return res

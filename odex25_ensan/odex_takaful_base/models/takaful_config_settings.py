# Customize settings for Takaful configrations.

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from ast import literal_eval

class ResCompany(models.Model):
    _inherit = 'res.company'

    kafala_benefit_account_id = fields.Many2one('account.account', string="From Account")
    kafala_benefit_bank_account_id = fields.Many2one('account.account', string="To Bank Account")
    kafala_benefit_journal_id = fields.Many2one('account.journal', string="Payment Journal")

    orphan_account_id = fields.Many2one('account.account', string="Orphans Account")
    widow_account_id = fields.Many2one('account.account', string="Widows Account")
    gift_account_id = fields.Many2one('account.account', string="Gifts Account")
    need_account_id = fields.Many2one('account.account', string="Needs Account")


class TakafulConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    min_kafala = fields.Integer(string='Minimum Kafala Value')
    cancel_kafala = fields.Integer(string='Kafala Cancellation After')
    new_kafala = fields.Selection([
        ('first', 'Show Only First Name'),
        ('always', 'Show Name Always')],
        string='New Kafala'
    )
    notification_ids = fields.Many2many(
        'takaful.notification',
        string='Notifications'
    )
    allowed_pay_days = fields.Integer(string='Delayed Kafala After')

    kafala_journal_id = fields.Many2one(
        'account.journal',
        string="Sponsorships Account Journal",
    )
    # Payment for benefit
    kafala_benefit_account_id = fields.Many2one(related='company_id.kafala_benefit_account_id', string="From Account",readonly=False)
    kafala_benefit_bank_account_id = fields.Many2one(related='company_id.kafala_benefit_bank_account_id', string="To Bank Account",readonly=False)
    kafala_benefit_journal_id = fields.Many2one(related='company_id.kafala_benefit_journal_id', string="Payment Journal",readonly=False)
    
    # Takaful Recivable Accounts
    orphan_account_id = fields.Many2one(related='company_id.orphan_account_id', string="Orphans Account", readonly=False)
    widow_account_id = fields.Many2one(related='company_id.widow_account_id', string="Widows Account",readonly=False)
    gift_account_id = fields.Many2one(related='company_id.gift_account_id', string="Gifts Account",readonly=False)
    need_account_id = fields.Many2one(related='company_id.need_account_id', string="Needs Account",readonly=False)

    @api.constrains('notification_ids')
    def check_notification_ids(self):
        if self.notification_ids:
            only_allowed = []
            for rec in self.notification_ids:
                if rec.notification_type in only_allowed:
                    raise ValidationError(_(u'There Are Repeatations in Notification Type'))

                only_allowed.append(rec.notification_type)

    # @api.multi
    def set_values(self):
        super(TakafulConfigSettings, self).set_values()
        sudoConf = self.env['ir.config_parameter'].sudo()
        
        sudoConf.set_param('odex_takaful_base.min_kafala', self.min_kafala)
        sudoConf.set_param('odex_takaful_base.allowed_pay_days', self.allowed_pay_days)
        sudoConf.set_param('odex_takaful_base.kafala_journal_id', self.kafala_journal_id.id)
        sudoConf.set_param('odex_takaful_base.cancel_kafala', self.cancel_kafala)
        sudoConf.set_param('odex_takaful_base.new_kafala', self.new_kafala)
        sudoConf.set_param('odex_takaful_base.notification_ids', self.notification_ids.ids)

    @api.model
    def get_values(self):
        res = super(TakafulConfigSettings, self).get_values()
        sudoConf = self.env['ir.config_parameter'].sudo()

        min_kafala = sudoConf.get_param('odex_takaful_base.min_kafala')
        allowed_pay_days = sudoConf.get_param('odex_takaful_base.allowed_pay_days')
        kafala_journal_id = sudoConf.get_param('odex_takaful_base.kafala_journal_id', default=False)

        new_kafala = sudoConf.get_param('odex_takaful_base.new_kafala')
        cancel_kafala = sudoConf.get_param('odex_takaful_base.cancel_kafala')
        notifications = sudoConf.get_param('odex_takaful_base.notification_ids')

        if notifications:
            notification_ids = [(6, 0, literal_eval(notifications))]
        else:
            notification_ids = None

        res.update(
            {
            'min_kafala': int(min_kafala),
            'allowed_pay_days': int(allowed_pay_days),
            'cancel_kafala': int(cancel_kafala),
            'new_kafala': new_kafala,
            'kafala_journal_id': int(kafala_journal_id) if kafala_journal_id else False,
            'notification_ids': notification_ids
            }
        )

        return res

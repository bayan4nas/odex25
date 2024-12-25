from odoo import _, api, fields, models, tools


class MailComposer(models.TransientModel):
    _inherit = 'mail.compose.message'

    # def send_mail(self, auto_commit=False):
    #     res = super(MailComposer, self).send_mail(auto_commit=auto_commit)
    #     context = self._context
    #     if self.model == 'purchase.order':
    #         x = self.env['purchase.order'].search([
    #             ('id', 'in', context.get('active_ids')),
    #         ])
    #         print(x.is_purchase_budget, 'is_purchase_budget')
    #         self.env['purchase.order'].search([
    #             ('id', 'in', context.get('active_ids')),('state','not in',["purchase"]),
    #         ]).write({'state': 'sent'})
    #
    #     return res

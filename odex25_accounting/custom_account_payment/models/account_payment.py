from odoo import fields, models, api, _

class AccountPayment(models.Model):
    _inherit = 'account.payment'
    destination_journal_id = fields.Many2one(comodel_name='account.journal')
    paired_internal_transfer_payment_id = fields.Many2one('account.payment',help="When an internal transfer is posted, a paired payment is created. " "They are cross referenced trough this field",copy=False)

    def action_post(self):
        res = super(AccountPayment, self).action_post()
        for payment in self:
            if payment.is_internal_transfer:
                paired_payment = payment.copy({
                    'journal_id': payment.destination_journal_id.id,
                    'destination_journal_id': payment.journal_id.id,
                    'payment_type': payment.payment_type == 'outbound' and 'inbound' or 'outbound',
                    'move_id': None,
                    'ref': payment.ref,
                    'paired_internal_transfer_payment_id': payment.id,
                    'date': payment.date,
                })
                paired_payment.move_id._post(soft=False)
                payment.paired_internal_transfer_payment_id = paired_payment

                body = _(
                    'This payment has been created from <a href=# data-oe-model=account.payment data-oe-id=%d>%s</a>') % (
                           payment.id, payment.name)
                paired_payment.message_post(body=body)
                body = _(
                    'A second payment has been created: <a href=# data-oe-model=account.payment data-oe-id=%d>%s</a>') % (
                           paired_payment.id, paired_payment.name)
                payment.message_post(body=body)
                paired_payment.state='posted'
                lines = (payment.move_id.line_ids + paired_payment.move_id.line_ids).filtered(
                    lambda l: l.account_id == payment.destination_account_id and not l.reconciled)
                lines.reconcile()

        return res

class AccountMove(models.Model):
    _inherit = 'account.move'

    payment_count = fields.Integer(string='Payments', compute='_compute_payment_count')

    @api.depends('payment_state')
    def _compute_payment_count(self):
        for rec in self:
            payments = self.env['account.payment'].search([('ref', '=', rec.name)])
            rec.payment_count = len(payments)

    def action_view_payments(self):
        self.ensure_one()

        search_part = '/'.join(self.name.split('/')[-3:])

        payments = self.env['account.payment'].search([
            ('partner_id.id', '=', self.partner_id.id),
            '|',
            ('ref', '=', self.name),
            ('name', 'ilike', search_part)
        ])

        action = self.env.ref('account.action_account_payments').read()[0]
        action['domain'] = [('id', 'in', payments.ids)]
        action['context'] = {'create': False}
        self.payment_count = len(payments)
        return action




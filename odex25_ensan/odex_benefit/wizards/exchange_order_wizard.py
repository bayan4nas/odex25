from odoo import models, fields, api

class ExchangeOrderWizard(models.TransientModel):
    _name = 'exchange.order.wizard'
    _description = 'Wizard to Assign Accounting that Exchange Orders'

    accountant_id = fields.Many2one('res.users',string='Accountant')

    def create_payment_order(self):
        active_ids = self.env.context.get('default_service_ids')
        service_requests = self.env['service.request'].browse(active_ids)
        for service in service_requests:
            service.is_payment_order_done = True
        self.env['payment.orders'].create({
            'state':'draft',
            'accountant_id':self.accountant_id.id,
            'service_requests_ids' : service_requests.ids
        })

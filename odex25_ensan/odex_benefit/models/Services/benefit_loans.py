import datetime

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError


class benefitLoans(models.Model):
    _name = 'receive.benefit.loans'
    _description = 'benefit Loans'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char()
    donation_type = fields.Many2many('donations.type',
                                     string='')
    number_of_installments = fields.Integer(
        string='Number of installments',
        required=False)
    installment_value = fields.Float(
        string='Installment Value',
        compute="_get_installment_value",
        required=False)
    receive_date = fields.Date(
        string='Receive Date',
        required=False)
    account_payment_id = fields.Many2one('account.payment')
    loan_amount = fields.Monetary(
        related='account_payment_id.amount',
        string='Loan Amount',
        required=False)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('announced', 'announced'),
        ('booked_up', 'booked up'),
        ('approve', 'Approved'),
        ('refused', 'Refused'),
        ('done', 'Done')
    ], string='state', default="draft", tracking=True)

    def action_submit(self):
        self.state = 'announced'

    def action_booked_up(self):
        self.state = 'booked_up'

    def action_approve(self):
        self.state = 'approve'

    def action_refused(self):
        self.state = 'refused'

    def action_done(self):
        self.state = 'done'

    @api.onchange('loan_amount', 'number_of_installments')
    def _get_installment_value(self):
        self.installment_value = 0.0
        if self.number_of_installments > 0:
            self.installment_value = (self.loan_amount / self.number_of_installments)


class benefitLoans(models.Model):
    _name = 'benefit.loans'
    _description = 'benefit Loans'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char()
    family_id = fields.Many2one('benefit.family')
    responsible_id = fields.Many2one('grant.benefit', related='family_id.responsible_benefit_id',
                                     string='responsible',
                                     required=False)
    benefits_total = fields.Integer(string="Benefit Total", related="family_id.benefits_total")
    description = fields.Char()
    donation_type = fields.Many2many('donations.type', string='')
    loan_amount = fields.Float(
        string='Loan Amount',
        required=False)
    number_of_installments = fields.Integer(
        string='Number of installments',
        required=False)
    account_payment_id = fields.Many2one('account.payment')
    journal_id = fields.Many2one('account.journal')
    installment_value = fields.Float(
        string='Installment Value',
        compute="_get_installment_value",
        required=False)
    purchase_product_ids = fields.One2many('purchase.product.loan', 'loan_id')
    purchase_order_id = fields.Many2one('purchase.order', string='Order Reference', index=True,
                                        ondelete='cascade')
    payment_method_id = fields.Many2one('account.payment.method', string='Payment Type', required=True)
    currency_id = fields.Many2one('res.currency', string='Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id)

    stock_picking_id = fields.Many2one('stock.picking', string='Stock Picking', ondelete='cascade', copy=False,
                                       required=False)
    picking_type_id = fields.Many2one('stock.picking.type')
    delivery_date = fields.Date(string='Delivery Date', required=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('announced', 'announced'),
        ('booked_up', 'booked up'),
        ('approve', 'Approved'),
        ('refused', 'Refused'),
        ('done', 'Done')
    ], string='state', default="draft", tracking=True)

    @api.onchange('purchase_product_ids')
    def _onchange_product_ids(self):
        for rec in self:
            if rec.id:
                products_total = 0.0
                for product in rec.purchase_product_ids:
                    products_total += product.price
                if products_total >= self.loan_amount:
                    print(self.loan_amount)
                    print(products_total)
                    raise ValidationError(_(u'The specified quantities exceed the specified price of the loan'))

    def action_purchase(self):
        po = self.env['purchase.order'].create({
            'partner_id': self.responsible_id.partner_id.id,  # todo
            'date_planned': datetime.date.today(),
            'state': 'draft',
        })
        for product in self.purchase_product_ids:
            pol = self.env['purchase.order.line'].create({
                'order_id': po.id,
                'product_id': product.product_id.id,
                'name': product.product_id.name,
                'product_qty': product.quantity,
                'date_planned': datetime.date.today(),
                'product_uom': product.product_id.uom_id.id,
                'price_unit': product.product_id.list_price,
            })
        self.purchase_order_id = po.id

    def action_compute(self):
        customerloc, location_id = self.env['stock.warehouse']._get_partner_locations()
        stock_picking = self.env['stock.picking'].create({
            'picking_type_id': self.picking_type_id.id,
            'location_id': location_id.id if self.picking_type_id.code == 'incoming' else self.picking_type_id.default_location_src_id.id,
            # 'product_uom_qty': self.quantity,
            'location_dest_id': self.picking_type_id.default_location_dest_id.id if self.picking_type_id.code == 'incoming' else customerloc.id,
        })
        for product in self.purchase_product_ids:
            stock_move = self.env['stock.move'].create({
                'picking_id': stock_picking.id,
                'product_id': product.product_id.id,
                'name': product.product_id.name,
                'product_uom_qty': product.quantity,
                'product_uom': product.product_id.uom_id.id,
                'location_id': location_id.id if self.picking_type_id.code == 'incoming' else self.picking_type_id.default_location_src_id.id,
                'location_dest_id': self.picking_type_id.default_location_dest_id.id if self.picking_type_id.code == 'incoming' else customerloc.id,
            })
        self.stock_picking_id = stock_picking.id

    def action_submit(self):
        self.state = 'announced'

    def action_booked_up(self):
        self.state = 'booked_up'

    def action_draft(self):
        self.state = 'draft'

    def action_approve(self):
        # self.action_compute()
        self.action_purchase()
        account_payment = self.env['account.payment'].create({
            'name': '/',
            'partner_type': 'customer',
            'partner_id': self.responsible_id.partner_id.id,
            'payment_type': 'outbound',
            'journal_id': self.journal_id.id,
            'payment_method_id': self.payment_method_id.id,
            'currency_id': self.currency_id.id,
            'amount': self.loan_amount,
            # 'payment_date': datetime.datetime.now(),
            'benefit_loan_id': self.id,
        })
        self.account_payment_id = account_payment
        self.state = 'approve'

    def action_refused(self):
        self.state = 'refused'

    def action_done(self):
        self.state = 'done'

    @api.onchange('loan_amount', 'number_of_installments')
    def _get_installment_value(self):
        self.installment_value = 0.0
        if self.number_of_installments > 0:
            self.installment_value = (self.loan_amount / self.number_of_installments)


class purchaseProductLoan(models.Model):
    _name = 'purchase.product.loan'
    _description = 'Purchase Benefit Loans'

    loan_id = fields.Many2one('benefit.loans')
    product_id = fields.Many2one('product.product')
    list_price = fields.Float(
        related='product_id.list_price',
        string='',
        required=False)
    quantity = fields.Float()
    price = fields.Float(compute='_compute_price')

    @api.onchange('quantity')
    def _compute_price(self):
        for rec in self:
            rec.price = rec.list_price * rec.quantity

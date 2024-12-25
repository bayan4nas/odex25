import base64
from io import BytesIO
from random import randint
import qrcode
from odoo import models, fields, api, _
from datetime import datetime, date, timedelta
from odoo.exceptions import UserError, ValidationError


# receive
class ReceiveFoodBasket(models.Model):
    _name = 'receive.food.basket'
    _description = 'receive food basket'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # TODO
    # barcode
    # sms notification

    name = fields.Char()
    date_start = fields.Date(
        string='',
        required=False)
    date_end = fields.Date(
        string='',
        required=False)
    donation_method = fields.Selection(
        string='Donation Method',
        selection=[('inside', 'inside the assembly'),
                   ('outside', 'outside the assembly'),
                   ('both', 'Both'),
                   ],
        required=False, )
    donation_type = fields.Selection(
        string='',
        selection=[('material', 'Material'),
                   ('cash', 'cash'),
                   ('both', 'Both'),
                   ],
        required=False, )
    amount = fields.Float(string="Amount", compute='_compute_amount_quantity')
    quantity = fields.Float(compute='_compute_amount_quantity', string='Quantity',
                            required=False)
    # Payment
    code = fields.Char(string="Code", copy=False, readonly=True, default=lambda x: _('New'))
    journal_id = fields.Many2one('account.journal')
    account_id = fields.Many2one('account.account', )
    entry_id = fields.Many2one('account.move', string="Entry")
    product_id = fields.Many2one('product.product', string='Product', ondelete='cascade', copy=False, required=False)
    qty_available = fields.Float(related='product_id.qty_available')
    stock_picking_id = fields.Many2one('stock.picking', string='Stock Picking', ondelete='cascade', copy=False,
                                       required=False)
    picking_type_id = fields.Many2one('stock.picking.type', string='', required=False)
    purchase_order_id = fields.Many2one('purchase.order', string='Order Reference', index=True,
                                        ondelete='cascade')
    description = fields.Char(
        string='',
        required=False)
    # donation_type = cash
    donation_amount = fields.Float(
        compute='_get_total_donation',
        string='',
        required=False)
    amount_ids = fields.One2many(
        'food.basket.line',
        inverse_name='food_basket_id',
        string='',
        required=False)

    donation_type = fields.Many2many('donations.type',
                                     string='')
    delivery_date = fields.Date(
        string='Delivery Date',
        required=False)

    @api.onchange('amount_ids')
    def _compute_amount_quantity(self):
        for rec in self:
            rec.amount = 0.0
            rec.quantity = 0.0
            if rec.amount_ids:
                for payment in rec.amount_ids:
                    rec.amount += payment.amount
                    rec.quantity += payment.qty

    def _get_total_donation(self):
        total_donation = 0.0
        for i in self.amount_ids:
            total_donation += i.amount
        self.donation_amount = total_donation

        # barcode

    state = fields.Selection([
        ('draft', 'Draft'),
        ('approve', 'Approved'),
        ('receiving', ' Receiving'),
        ('piking', 'Piking'),
        ('done', 'Done'),
        ('refused', 'Refused'),
        ('cancel', 'Cancel'),
    ], string='state', default="draft", tracking=True)

    def action_open_quants(self):
        products = self.mapped('product_id')
        action = self.env.ref('stock.product_open_quants').read()[0]
        action['domain'] = [('product_id', 'in', products.ids)]
        action['context'] = {'search_default_internal_loc': 1}
        return action

    def action_submit(self):
        self.state = 'submit'

    def action_approve(self):
        self.state = 'approve'

    def action_receiving(self):
        self.state = 'receiving'

    def action_restriction(self):
        self.state = 'restriction'

    def action_done(self):
        self.state = 'done'

    def action_cancel(self):
        self.state = 'cancel'

    def action_compute(self):
        print(self.amount < 0)
        print(self.purchase_order_id.id)
        if (self.amount < 0 and not self.purchase_order_id.id) or self.amount == 0:
            raise ValidationError(_(u' No pay'))
        customerloc, location_id = self.env['stock.warehouse']._get_partner_locations()
        stock_picking = self.env['stock.picking'].create({
            'picking_type_id': self.picking_type_id.id,
            'location_id': location_id.id,
            # 'product_uom_qty': self.quantity,
            'location_dest_id': self.picking_type_id.default_location_dest_id.id,
        })
        stock_move = self.env['stock.move'].create({
            'picking_id': stock_picking.id,
            'product_id': self.product_id.id,
            'name': self.product_id.name,
            'product_uom_qty': self.quantity,
            'product_uom': self.product_id.uom_id.id,
            'location_id': location_id.id,
            'location_dest_id': self.picking_type_id.default_location_dest_id.id,
        })
        self.stock_picking_id = stock_picking.id
        self.state = 'piking'

    def action_compute_purchase_order(self):

        move_id = self.env['account.move'].sudo().create({
            'journal_id': self.journal_id.id,
            'ref': self.code})
        move_line = []
        move_line.append({
            'debit': self.amount,
            'credit': 0.0,
            'account_id': self.account_id.id,
        })
        move_line.append({
            'debit': 0.0,
            'credit': self.amount,
            'account_id': self.account_id.id,
        })
        move_id.write({'line_ids': [(0, 0, line) for line in move_line]})
        move_id.post()
        self.entry_id = move_id.id
        po = self.env['purchase.order'].create({
            'partner_id':self.amount_ids.donor_parnter.id,
            'date_planned': date.today(),
            'state': 'draft',

        })
        pol = self.env['purchase.order.line'].create({
            'order_id': po.id,
            'product_id': self.product_id.id,
            'name': self.product_id.name,
            'product_qty': self.amount / self.product_id.standard_price,
            'date_planned': date.today(),
            'product_uom': self.product_id.uom_id.id,
            'price_unit': self.product_id.standard_price,
        })
        self.purchase_order_id = po.id


class RFoodBasket(models.Model):
    _name = 'food.basket.line'
    _description = 'food basket'

    food_basket_id = fields.Many2one(
        'receive.food.basket',
        string='',
        required=False)
    name = fields.Char(
        string='Donor name',
        required=False)

    def _get_default_color(self):
        return randint(1, 11)

    color = fields.Integer(string='Color Index', default=_get_default_color)
    donation_method = fields.Selection(
        string='Donation Method',
        selection=[('inside', 'inside the assembly'),
                   ('outside', 'outside the assembly'),
                   ],
        required=False, )
    donor_partner = fields.Many2one('res.partner')
    phone_number = fields.Char()
    donation_type = fields.Selection(
        string='',
        selection=[('material', 'Material'),
                   ('cash', 'cash'),
                   ('both', 'Both'),
                   ],
        required=False, )
    payment_id = fields.Many2one('account.payment')
    currency_id = fields.Many2one('res.currency', string='Currency', related='payment_id.currency_id', readonly=True)
    # amount = fields.Monetary(
    #     related='payment_id.amount',
    #     string='Amount',
    #     required=False)
    amount = fields.Monetary(string='Amount',
        required=False)
    qty = fields.Float(
        string='',
        required=False)


##########################################################################
class benefitFoodBasket(models.Model):
    _name = 'benefit.food.basket'
    _description = 'benefit food basket'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # TODO
    # barcode
    # sms notification

    name = fields.Char()
    date_start = fields.Date(
        string='',
        required=False)
    date_end = fields.Date(
        string='',
        required=False)
    # donation_type = cash
    donation_amount = fields.Float(
        string='',
        required=False)

    donation_type = fields.Many2many('donations.type',
                                     string='')
    benefit_ids = fields.One2many(
        'food.basket.benefits.line',
        'food_basket_id',
        string='')
    delivery_date = fields.Date(
        string='Delivery Date',
        required=False)
    product_id = fields.Many2one('product.product', string='Product', ondelete='cascade', copy=False, required=False)
    qty_available = fields.Float(related='product_id.qty_available')
    quantity = fields.Float(
        compute='onchange_quantity',
        string='Quantity',
        required=False)
    stock_picking_id = fields.Many2one('stock.picking', string='Stock Picking', ondelete='cascade', copy=False,
                                       required=False)
    picking_type_id = fields.Many2one('stock.picking.type')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approve', 'Waiting Approved'),
        ('approve', 'Approved'),
        ('calculation', 'calculation'),
        ('waiting_delivery', 'Waiting delivery'),
        ('refused', 'Refused'),
        ('done', 'Done')
    ], string='state', default="draft", tracking=True)

    def action_open_quants(self):
        products = self.mapped('product_id')
        action = self.env.ref('stock.product_open_quants').read()[0]
        action['domain'] = [('product_id', 'in', products.ids)]
        action['context'] = {'search_default_internal_loc': 1}
        return action

    @api.onchange('benefit_ids')
    def onchange_quantity(self):
        for rec in self.benefit_ids:
            self.quantity += rec.qty
        self.quantity = 0

    def action_submit(self):
        self.state = 'waiting_approve'

    def action_approve(self):
        self.state = 'approve'

    def action_calculation(self):
        self.action_compute()
        self.state = 'calculation'

    def action_compute(self):
        customerloc, location_id = self.env['stock.warehouse']._get_partner_locations()
        stock_picking = self.env['stock.picking'].create({
            'picking_type_id': self.picking_type_id.id,
            'location_id': location_id.id if self.picking_type_id.code == 'incoming' else self.picking_type_id.default_location_src_id.id,
            # 'product_uom_qty': self.quantity,
            'location_dest_id': self.picking_type_id.default_location_dest_id.id if self.picking_type_id.code == 'incoming' else customerloc.id,
        })
        stock_move = self.env['stock.move'].create({
            'picking_id': stock_picking.id,
            'product_id': self.product_id.id,
            'name': self.product_id.name,
            'product_uom_qty': self.quantity,
            'product_uom': self.product_id.uom_id.id,
            'location_id': location_id.id if self.picking_type_id.code == 'incoming' else self.picking_type_id.default_location_src_id.id,
            'location_dest_id': self.picking_type_id.default_location_dest_id.id if self.picking_type_id.code == 'incoming' else customerloc.id,
        })
        self.stock_picking_id = stock_picking.id

    def action_refused(self):
        self.state = 'refused'

    def action_delivery(self):
        self.state = 'waiting_delivery'

    def action_done(self):
        self.state = 'done'


class FoodBasketBenefits(models.Model):
    _name = 'food.basket.benefits.line'
    _description = 'food basket'

    food_basket_id = fields.Many2one(
        'benefit.food.basket',
        string='food Basket id',
        required=False)
    family_id = fields.Many2one('benefit.family', string='Benefit Family')
    family_member = fields.Integer(related='family_id.benefits_total')
    qty = fields.Float(
        string='',
        required=False)
    date = fields.Datetime(
        string='',
        required=False)
    qr_code = fields.Binary("QR Code", attachment=True, store=True)
    is_receive = fields.Boolean(
        string='',
        required=False)

    @api.onchange('family_id', 'qr_code', 'date')
    def generate_qr_code(self):
        if self.family_id and self.qty and self.date:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=15,
                border=4,
            )
            name = "name:" + self.family_id.name + " amount:" + str(self.qty) + "date:" + str(self.date)
            qr.add_data(name)
            qr.make(fit=True)
            img = qr.make_image()
            temp = BytesIO()
            img.save(temp, format="PNG")
            qr_image = base64.b64encode(temp.getvalue())
            self.qr_code = qr_image

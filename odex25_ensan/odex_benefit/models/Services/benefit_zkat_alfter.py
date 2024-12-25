from odoo import models, fields, api, _
from datetime import datetime, date, timedelta
from odoo.exceptions import UserError, ValidationError


# receiving zakat
class ReceiveZkat(models.Model):
    _name = 'receive.benefit.zkat'
    _description = 'receive of zkat al-feter of benefit'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name")
    description = fields.Char(string="Name")
    code = fields.Char(string="Code", copy=False, readonly=True, default=lambda x: _('New'))
    journal_id = fields.Many2one('account.journal')
    account_id = fields.Many2one('account.account', )
    date_from = fields.Date(string="Date start")
    date_to = fields.Date(string="Date end")
    entry_id = fields.Many2one('account.move', string="Entry")
    # Payment collection
    payment_collection_ids = fields.One2many('payment.collection.line', 'receive_zkat_id')
    donation_method = fields.Selection(
        string='Donation Method',
        selection=[('inside', 'inside the assembly'),
                   ('outside', 'outside the assembly'), ], required=False, )
    uint = fields.Float()
    uint_price = fields.Float()
    amount = fields.Float(string="Amount", compute='_compute_amount_quantity')
    quantity = fields.Float(compute='_compute_amount_quantity', string='Quantity',
                            required=False)
    purchase_order_id = fields.Many2one('purchase.order', string='Order Reference', index=True,
                                        ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', ondelete='cascade', copy=False, required=False)
    qty_available = fields.Float(related='product_id.qty_available')
    stock_picking_id = fields.Many2one('stock.picking', string='Stock Picking', ondelete='cascade', copy=False,
                                       required=False)
    picking_type_id = fields.Many2one('stock.picking.type', string='', required=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approve', 'Approved'),
        ('receiving', ' Receiving'),
        ('piking', 'Piking'),
        ('done', 'Done'),
        ('refused', 'Refused'),
        ('cancel', 'Cancel'),
    ], string='state', default="draft", tracking=True)

    @api.model
    def create(self, vals):
        res = super(ReceiveZkat, self).create(vals)
        if not res.code or res.code == _('New'):
            res.code = self.env['ir.sequence'].sudo().next_by_code('benefit.receive.zkat.sequence') or _('New')
        return res

    def action_open_quants(self):
        products = self.mapped('product_id')
        action = self.env.ref('stock.product_open_quants').read()[0]
        action['domain'] = [('product_id', 'in', products.ids)]
        action['context'] = {'search_default_internal_loc': 1}
        return action

    def action_compute(self):
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
            'partner_id': self.payment_collection_ids.donor_partner.id,
            'date_planned': date.today(),
            'state': 'draft',

        })
        pol = self.env['purchase.order.line'].create({
            'order_id': po.id,
            'product_id': self.product_id.id,
            'name': self.product_id.name,
            'product_qty': self.amount / self.product_id.standard_price if self.product_id.standard_price > 0 else 0 ,
            'date_planned': date.today(),
            'product_uom': self.product_id.uom_id.id,
            'price_unit': self.product_id.standard_price,
        })
        self.purchase_order_id = po.id

    def action_approve(self):
        self.state = 'approve'

    def action_draft(self):
        self.state = 'draft'
        self.purchase_order_id.unlink()

    @api.onchange('payment_collection_ids')
    def _compute_amount_quantity(self):
        for rec in self:
            rec.amount = 0.0
            rec.quantity = 0.0
            if rec.payment_collection_ids:
                for payment in rec.payment_collection_ids:
                    rec.amount += payment.amount
                    rec.quantity += payment.quantity

    def action_refuse(self):
        self.state = 'refused'

    def action_receiving(self):
        self.state = 'receiving'

    def action_submit(self):
        self.state = 'submit'

    def action_restriction(self):
        self.state = 'restriction'

    # def action_paid(self):
    #     self.state = 'paid'

    def action_done(self):
        self.state = 'done'

    def action_cancel(self):
        self.state = 'cancel'

    def create_entry(self):
        move_id = self.env['account.move'].sudo().create({
            'journal_id': self.company_id.benefit_journal_id.id,
            'ref': self.code})
        move_line = []
        move_line.append({
            'debit': self.amount,
            'credit': 0.0,
            'account_id': self.company_id.benefit_account_id.id,
        })
        move_line.append({
            'debit': 0.0,
            'credit': self.amount,
            'account_id': self.company_id.benefit_bank_account_id.id,
        })

        move_id.write({'line_ids': [(0, 0, line) for line in move_line]})
        move_id.post()
        self.entry_id = move_id.id


class zkat(models.Model):
    _name = 'benefit.zkat'
    _description = 'percentage of zkat al-feter of benefit '
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name")
    code = fields.Char(string="Code", copy=False, readonly=True, default=lambda x: _('New'))
    journal_id = fields.Many2one('account.journal')
    account_id = fields.Many2one('account.account', )

    date_from = fields.Date(string="Date start")
    date_to = fields.Date(string="Date end")
    delivery_date = fields.Date(
        string='Delivery Date',
        required=False)

    donation_method = fields.Selection(
        string='Donation Method',
        selection=[('inside', 'inside the assembly'),
                   ('outside', 'outside the assembly'),
                   ],
        required=False, )
    uint = fields.Float(
        string='',
        required=False)
    uint_amount = fields.Float(
        string='',
        required=False)
    product_id = fields.Many2one('product.product', string='Product', ondelete='cascade', copy=False, required=False)
    qty_available = fields.Float(related='product_id.qty_available')
    quantity = fields.Float(
        compute='onchange_quantity',
        string='Quantity',
        required=False)
    benefit_ids = fields.Many2many(
        'grant.benefit',
        string='')
    zkat_ids = fields.One2many(
        comodel_name='zkat.line',
        inverse_name='zkat_id',
        string='',
        required=False)
    external_ids = fields.Many2many(
        'external.benefits',
        string='External Benefits')
    user_id = fields.Many2one('res.users', string="User", default=lambda self: self.env.user)
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.user.company_id)
    parent_id = fields.Many2one('benefit.zkat', string="Parent")
    line_ids = fields.One2many('benefit.zkat.line', 'year_id', string="Lines")
    is_appendix = fields.Boolean(
        string='is appendix',
        required=False)
    housing_id = fields.Many2one(
        'benefit.housing',
        string='',
        required=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('restriction', 'restriction'),
        ('approve', 'Approved'),
        ('piking', 'Piking'),
        ('delivery', 'Delivery'),
        ('done', 'Done'),
        ('refused', 'Refused'),
        ('cancel', 'Cancel'),
    ], string='state', default="draft", tracking=True)
    entry_id = fields.Many2one('account.move', string="Entry")
    is_benefits = fields.Boolean(
        string='is benefits',
        required=False)
    requests_total = fields.Integer(string="Requests Total", compute="get_total")
    stock_picking_id = fields.Many2one('stock.picking', string='Stock Picking', ondelete='cascade', copy=False,
                                       required=False)
    picking_type_id = fields.Many2one('stock.picking.type')

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
        self.state = 'piking'

    def action_open_quants(self):
        products = self.mapped('product_id')
        action = self.env.ref('stock.product_open_quants').read()[0]
        action['domain'] = [('product_id', 'in', products.ids)]
        action['context'] = {'search_default_internal_loc': 1}
        return action

    @api.onchange('zkat_ids')
    def onchange_quantity(self):
        for rec in self.zkat_ids:
            self.quantity += rec.net
        self.quantity = 0

    def action_draft(self):
        for rec in self:
            rec.state = 'draft'

    @api.onchange('zkat_ids')
    def compute_uint_amount(self):
        if self.state in ['draft', 'restriction']:
            quantity = 0.0
            for rec in self.zkat_ids:
                quantity += rec.quantity
            try:
                uint_amount = (self.qty_available / quantity) * 100
                self.uint_amount = 100 if uint_amount > 100 else uint_amount
            except:
                pass

    def get_total(self):
        for request in self:
            if request.id:
                requests = request.env['external.request'].sudo().search(
                    [('zkat_id', '=', request.id), ('state', '=', 'draft')])
                self.requests_total = len(requests)

    def open_external_request(self):
        context = {}
        context['default_zkat_id'] = self.id
        return {
            'name': _('External Request'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(self.env.ref(
                'odex_benefit.external_request_tree').id, 'tree'),
                      (self.env.ref('odex_benefit.external_request_form').id, 'form')],
            'res_model': 'external.request',
            'type': 'ir.actions.act_window',
            'context': context,
            'domain': "[('zkat_id','=',%s)]" % (self.id),
            'target': 'current',
        }

    @api.model
    def create(self, vals):
        res = super(zkat, self).create(vals)
        if not res.code or res.code == _('New'):
            res.code = self.env['ir.sequence'].sudo().next_by_code('benefit.zkat.sequence') or _('New')
        return res

    @api.model
    def payment_cron(self):
        payment = self.env['benefit.zkat'].search([('state', '=', 'approve'), ('date', '=', str(datetime.now().date())),
                                                   ('line_ids', '=', False)], limit=1)
        if payment:
            payment.action_create_lines()

    def open_payments(self):
        return {
            'name': "Payments",
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(self.env.ref(
                'odex_benefit.benefit_year_payment_line_tree').id, 'tree'),
                      (self.env.ref('odex_benefit.benefit_year_payment_line_form').id, 'form')],
            'res_model': 'benefit.zkat.line',
            'type': 'ir.actions.act_window',
            'domain': "[('year_id','=',%s)]" % (self.id),
            'target': 'current',
        }

    def compute_benefit(self):
        benefits = self.env['grant.benefit'].sudo().search([]).mapped('family_id')
        for rec in benefits:
            self.env['zkat.line'].create({
                'zkat_id': self.id,
                'family_id': rec.id,
            })

    def action_approve(self):
        self.state = 'approve'

    def action_pay(self):
        if self.is_benefits == True:
            self.sudo().create_entry()
            self.state = 'paid'
        else:
            raise ValidationError(
                _(u' No benefits for pay'))

    def action_refuse(self):
        self.state = 'refused'

    def action_receiving(self):
        self.state = 'receiving'

    def action_submit(self):
        self.state = 'submit'

    def action_restriction(self):
        self.compute_benefit()
        self.compute_uint_amount()
        self.state = 'restriction'

    def action_paid(self):
        self.state = 'paid'

    def action_delivery(self):
        self.state = 'delivery'

    def action_done(self):
        self.state = 'done'

    def action_cancel(self):
        self.state = 'cancel'


class YearPaymentLine(models.Model):
    _name = 'benefit.zkat.line'
    _rec_name = 'year_id'

    year_id = fields.Many2one('benefit.zkat')
    benefit_id = fields.Many2one('grant.benefit', string="Benefit")
    responsible_id = fields.Many2one('grant.benefit', string="Responsible Benefit")
    partner_id = fields.Many2one('res.partner', string="Responsible Partner")
    category_id = fields.Many2one('benefit.category', string="Category")
    date = fields.Datetime(string="Date")
    state = fields.Selection(related="year_id.state", store=True)
    amount = fields.Char(string="Amount")


# Payment collection
class PaymentCollection(models.Model):
    _name = 'payment.collection.line'

    receive_zkat_id = fields.Many2one(
        'receive.benefit.zkat',
        string='',
        required=False)
    donor_name = fields.Char(
        string='Donor name',
        required=False)
    donor_partner = fields.Many2one('res.partner')
    phone_number = fields.Char(
        string='',
        required=False)
    payment_id = fields.Many2one('account.payment',
                                 string='',
                                 required=False)
    donation_type = fields.Selection(
        string='',
        selection=[('material', 'Material'),
                   ('cash', 'cash'),
                   ('both', 'Both'),
                   ],
        required=False, )
    currency_id = fields.Many2one('res.currency', string='Currency', related='payment_id.currency_id', readonly=True)
    amount = fields.Monetary(
        related='payment_id.amount',
        string='Amount',
        required=False)
    quantity = fields.Float(
        string='Quantity',
        required=False)


class ZkatLine(models.Model):
    _name = 'zkat.line'

    zkat_id = fields.Many2one(
        'benefit.zkat',
        string='',
        required=False)
    family_id = fields.Many2one(
        'benefit.family',
        string='Family',
        required=False)
    benefits_total = fields.Integer(
        related='family_id.benefits_total',
        string='members',
        required=False)
    uint = fields.Float(
        related='zkat_id.uint',
        string='year amount',
        required=False)
    quantity = fields.Float(
        compute='total_quantity',
        string='Quantity',
        required=False)
    rate = fields.Float(
        related='zkat_id.uint_amount',
        string='Rate of zkat',
        required=False)
    net = fields.Float(
        compute='total_net',
        string='net of zkat',
        required=False)

    @api.onchange('uint')
    def total_quantity(self):
        for rec in self:
            if rec.uint and rec.benefits_total:
                rec.quantity = rec.uint * rec.benefits_total
        self.quantity = 0

    @api.onchange('quantity', 'rate')
    def total_net(self):
        for rec in self:
            if rec.quantity and rec.rate:
                if rec.rate < 100.00:
                    rec.net = rec.quantity * (rec.rate / 100)
                else:
                    rec.net = rec.quantity * (100 / 100)
            self.net = 0
        self.net = 0

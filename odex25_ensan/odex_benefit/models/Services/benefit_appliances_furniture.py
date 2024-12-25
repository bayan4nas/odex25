from odoo import fields, models, api
import qrcode
import base64
from io import BytesIO


class ReceiveAppliancesFurniture(models.Model):
    _name = 'receive.appliances.furniture'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    # _inherits = {'product.template': 'product_id'}
    _description = 'Receive appliances and furniture need of benefit '

    name = fields.Char()
    donation_type = fields.Many2many('donations.type', string='')
    donor_name = fields.Char()
    address = fields.Char(
        string='',
        required=False)
    lat = fields.Char(
        string='',
        required=False)
    lon = fields.Char(
        string='',
        required=False)
    description = fields.Char(
        string='',
        required=False)
    phone_number = fields.Char()
    product_status = fields.Many2one('item.status')
    donation_method = fields.Selection(string='Donation Method', selection=[('platform', 'Platform'),
                                                                            ('communication', 'Communication'),
                                                                            ('delivery', 'Delivery'),
                                                                            ], required=False, )
    donation_number = fields.Integer()
    product_qty = fields.Integer()
    image = fields.Binary(string="", )
    image_1 = fields.Binary(string="", )
    image_2 = fields.Binary(string="", )
    image_3 = fields.Binary(string="", )
    image_4 = fields.Binary(string="", )
    date_receipt = fields.Date(string='Date of Receipt', required=False)
    product_qty = fields.Float()
    prod_id = fields.Many2one('product.product', string='Product', ondelete='cascade', copy=False, required=False)
    uom_id = fields.Many2one('uom.uom')
    stock_picking_id = fields.Many2one('stock.picking', string='Stock Picking', ondelete='cascade', copy=False,
                                       required=False)
    picking_type_id = fields.Many2one('stock.picking.type', string='', required=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('receipt', 'Waiting Receipt'),
        ('approve', 'Approved'),
        ('storage', 'storage'),
        ('refused', 'Refused'),
        ('done', 'Done')
    ], string='state', default="draft", tracking=True)

    def action_submit(self):
        self.state = 'receipt'

    def action_done(self):
        self.state = 'done'

    def action_receipt(self):
        self.state = 'receipt'

    def action_storage(self):
        customerloc, location_id = self.env['stock.warehouse']._get_partner_locations()
        stock_picking = self.env['stock.picking'].create({
            'picking_type_id': self.picking_type_id.id,
            'location_id': location_id.id,
            'location_dest_id': self.picking_type_id.default_location_dest_id.id,
        })
        stock_move = self.env['stock.move'].create({
            'picking_id': stock_picking.id,
            'product_id': self.prod_id.id,
            'name': self.prod_id.name,
            'product_uom_qty': self.product_qty,
            'product_uom': self.prod_id.uom_id.id,
            'location_id': location_id.id,
            'location_dest_id': self.picking_type_id.default_location_dest_id.id,
        })
        self.stock_picking_id = stock_picking.id
        self.state = 'storage'

    def action_refused(self):
        self.state = 'refused'

    def action_draft(self):
        self.state = 'draft'

    def action_approve(self):
        product = self.env['product.product'].create({
            'name': self.name,
            'type': 'product',
            'uom_id': self.uom_id.id,
            'uom_po_id': self.uom_id.id
        })
        self.prod_id = product
        self.state = 'approve'


class AppliancesFurniture(models.Model):
    _name = 'appliances.furniture'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'appliances and furniture need of benefit '

    name = fields.Char()
    benefit_id = fields.Many2one(
        'grant.benefit',
        string='',
        required=False)
    benefit_ids = fields.Many2many('grant.benefit', compute='_get_benefit')
    appliances_furniture_need = fields.One2many('appliances.furniture.need', 'ap_id', tracking=True)
    donation_number = fields.Integer()
    delivery_date = fields.Date()
    # barcode TODO
    prod_id = fields.Many2one('product.product', string='Product', ondelete='cascade', copy=False, required=False)
    quantity = fields.Float(compute='onchange_qty')

    @api.onchange('quantity')
    def onchange_qty(self):
        for rec in self:
            rec.quantity = 0
            for i in rec.appliances_furniture_need:
                rec.quantity += i.qty

    qty_available = fields.Float(related='prod_id.qty_available')
    stock_picking_id = fields.Many2one('stock.picking', string='Stock Picking', ondelete='cascade', copy=False,
                                       required=False)
    picking_type_id = fields.Many2one('stock.picking.type')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approve', 'Waiting Approved'),
        ('approve', 'Approved'),
        ('waiting_delivery', 'Waiting delivery'),
        ('refused', 'Refused'),
        ('done', 'Done')
    ], string='state', default="draft", tracking=True)

    def action_open_quants(self):
        products = self.mapped('prod_id')
        action = self.env.ref('stock.product_open_quants').read()[0]
        action['domain'] = [('product_id', 'in', products.ids)]
        action['context'] = {'search_default_internal_loc': 1}
        return action

    @api.depends('prod_id')
    def _get_benefit(self):
        if self.state == 'approve':
            for rec in self:
                rooms = rec.env['benefit.housing.rooms'].sudo().search(
                    [('items.item.name', '=', rec.prod_id.name)])
                room_list = []
                need_list = []
                for room in rooms:
                    needs = {}
                    needs["ap_id"] = self.id
                    needs["housing_id"] = room.housing_id.id
                    needs["room_id"] = room.id
                    # needs["benefit_id"] = self.id
                    for test in room.items:
                        if test.item.name == rec.prod_id.name:
                            needs["status"] = test.status
                            needs["name"] = test.item.name
                    room_list.append(room.housing_id.id)
                    need_list.append(needs)
                if rooms:
                    benefit = []
                    for room in rooms:
                        print(room)
                        benefits = rec.env['grant.benefit'].sudo().search(
                            [('housing_id', '=', room.housing_id.id), ('benefit_type', '=', 'benefit')])
                        for i in benefits:
                            benefit.append(i.id)
                        print(benefit)
                        # print(needs)
                    for r in rec:
                        r.benefit_ids = [(6, 0, benefit)]
                    # print(needs)
                for ap in self.appliances_furniture_need:
                    for i in range(len(need_list)):
                        if need_list[i]['housing_id'] == ap.housing_id:
                            del need_list[i]
                            break
                if not self.appliances_furniture_need:
                    for need_item in need_list:
                        test = self.sudo().write({'appliances_furniture_need': [(0, 0, need_item)]})
                        print(test)

    def action_submit(self):
        self.state = 'waiting_approve'

    def action_delivery(self):
        self.state = 'waiting_delivery'

    def action_done(self):
        self.state = 'done'

    def action_draft(self):
        self.state = 'draft'

    def action_approve(self):
        customerloc, location_id = self.env['stock.warehouse']._get_partner_locations()
        stock_picking = self.env['stock.picking'].create({
            'picking_type_id': self.picking_type_id.id,
            'location_id': location_id.id if self.picking_type_id.code == 'incoming' else self.picking_type_id.default_location_src_id.id,
            'location_dest_id': self.picking_type_id.default_location_dest_id.id if self.picking_type_id.code == 'incoming' else customerloc.id,
        })
        stock_move = self.env['stock.move'].create({
            'picking_id': stock_picking.id,
            'product_id': self.prod_id.id,
            'name': self.prod_id.name,
            'product_uom_qty': self.quantity,
            'product_uom': self.prod_id.uom_id.id,
            'location_id': location_id.id if self.picking_type_id.code == 'incoming' else self.picking_type_id.default_location_src_id.id,
            'location_dest_id': self.picking_type_id.default_location_dest_id.id if self.picking_type_id.code == 'incoming' else customerloc.id,
        })
        self.stock_picking_id = stock_picking.id
        self.state = 'approve'


class DonationsType(models.Model):
    _name = 'donations.type'
    _description = 'appliances and furniture need of benefits'

    name = fields.Char(
        string='',
        required=False)


class AppliancesFurnitureNeed(models.Model):
    _name = 'appliances.furniture.need'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'appliances and furniture needs'

    name = fields.Char(
        string='',
        required=False)
    ap_id = fields.Many2one(
        'appliances.furniture',
        string='',
        required=False)
    report_id = fields.Many2one(
        'generate.reports.log',
        string='',
        required=False)
    housing_id = fields.Many2one(
        'benefit.housing',
        string='',
        required=False)
    room_id = fields.Many2one(
        'benefit.housing.rooms',
        string='',
        required=False)
    benefit_id = fields.Many2one(
        'grant.benefit',
        domain="[('housing_id','=',housing_id)]",
        string='',
        required=False)
    percentage = fields.Float()
    qty = fields.Integer(
        string='',
        required=False)
    status = fields.Many2one('item.status')
    qr_code = fields.Binary("QR Code", attachment=True, store=True)
    is_receive = fields.Boolean(tracking=True)

    @api.onchange('housing_id', 'benefit_id', 'qr_code', 'ap_id')
    def generate_qr_code(self):
        if self.housing_id and self.ap_id:
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=15,
                border=4,
            )
            name = "name:" + self.housing_id.name + " amount:" + str(self.ap_id.prod_id.name) + "date:" + str(
                self.ap_id.delivery_date)
            qr.add_data(name)
            qr.make(fit=True)
            img = qr.make_image()
            temp = BytesIO()
            img.save(temp, format="PNG")
            qr_image = base64.b64encode(temp.getvalue())
            self.qr_code = qr_image

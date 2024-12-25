from random import randint
from odoo import fields, models, api, _


class City(models.Model):
    _name = 'res.country.city'
    _description = "Benefits - City"

    @api.depends('code', 'name')
    def _load_country_id(self):
        for r in self:
            r.country_id = self.env.ref('base.sa')

    code = fields.Char(string='Code')
    name = fields.Char(string='Name')

    state_id = fields.Many2one('res.country.state', string='State')
    country_id = fields.Many2one('res.country', string='Country', compute='_load_country_id', store=True)


class housing(models.Model):
    _name = 'benefit.housing'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Benefits - housing"

    name = fields.Char(compute='_compute_get_name')
    city_id = fields.Many2one('res.country.city', string='City')
    block = fields.Char(string='block')
    street = fields.Char(string='street')
    url = fields.Char(compute="open_map")
    url_html = fields.Html(
        sanitize=False,
        compute="get_html")
    lat = fields.Char()
    lon = fields.Char()
    house_number = fields.Char(string='house number')
    floor = fields.Char(string='floor')
    housing_number = fields.Char(string='housing number')
    image = fields.Binary(string="", )
    image_1 = fields.Binary(string="", )
    image_2 = fields.Binary(string="", )
    image_3 = fields.Binary(string="", )
    image_4 = fields.Binary(string="", )
    nearby_mosque = fields.Char(string='Nearby mosque')
    housing_note = fields.Char(string='housing note')
    note_neighborhood = fields.Char()
    rent_amount = fields.Integer()
    housing_type = fields.Selection([
        ('apartment', 'apartment'),
        ('villa', 'villa'),
        ('popular_house', 'popular house'),
        ('tent', 'tent'),
        ('Appendix', 'Appendix'), ], default='apartment')
    housing_cat =  fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('bad', 'Bad'),
        ('collapsible', 'Collapsible')])
    property_type = fields.Selection([
        ('ownership', 'ownership'),
        ('rent', 'rent'),
        ('charitable', 'charitable'),
        ('ownership_shared', 'Ownership Shared'),
        ('rent_shared', 'Rent Shared')])
    rooms_number = fields.Integer('Rooms Number', compute="get_rooms_total", required=True)
    room_ids = fields.One2many('benefit.housing.rooms', inverse_name='housing_id')
    water_bill_account_number = fields.Char(string='water Bill Account Number')
    electricity_bill_account_number = fields.Char(string='Electricity Bill Account Number')
    water_bill_account_attach = fields.Many2many('ir.attachment',
                                                 relation="ir_water_bill_account_number_rel",
                                                 column1="water_bill_account_number",
                                                 column2="name",
                                                 string="water Bill")
    electricity_bill_account_attach = fields.Many2many('ir.attachment',
                                                       relation="ir_electricity_bill_account_attach_rel",
                                                       column1="electricity_bill_account_number",
                                                       column2="name",
                                                       string="Electricity Bill ")
    benefits_total = fields.Integer(string="Benefit Total", compute="get_benefits_total")
    benefit_ids = fields.One2many('grant.benefit', 'housing_id', string="Benefits")
    family_ids = fields.One2many('benefit.family', 'housing_id', string="Benefits")
    total_income = fields.Float(compute='get_total')
    total_expenses = fields.Float(compute='get_total')
    total_net = fields.Float(compute='get_total')
    financial_aid = fields.Float(compute='get_total')
    domestic_labor_ids = fields.Many2many('domestic.labor')

    def get_html(self):
        for rec in self:
            print(f'<iframe id="custom_src" height="500" width="500" src="{rec.url}"></iframe>')
            rec.url_html = f'<iframe id="custom_src" height="500" width="500" src="{rec.url}"/>'

    # @api.multi
    def open_map(self):
        for Location in self:
            url = "http://maps.google.com/maps?oi=map&q="
            if Location.street:
                url += Location.street.replace(' ', '+')
            if Location.city_id:
                url += '+' + Location.city_id.name.replace(' ', '+')
                url += '+' + Location.city_id.state_id.name.replace(' ', '+')
                url += '+' + Location.city_id.country_id.name.replace(' ', '+')
            if Location.nearby_mosque:
                url += Location.nearby_mosque.replace(' ', '+')
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': url
        }

    @api.onchange('url')
    def onchange_image_url(self):
        if self.image_url:
            self.img_attach = '<img id="img" src="%s"/>' % self.url

    @api.depends('benefit_ids')
    def get_benefits_total(self):
        for rec in self:
            rec.benefits_total = len(rec.benefit_ids)

    def get_total(self):
        for rec in self:
            for total in rec.benefit_ids:
                rec.total_income += total.total_income
                rec.total_expenses += total.total_expenses
            # rec.total_net = rec.total_expenses - rec.total_income
            if rec.total_expenses >= rec.total_income:
                rec.total_net = rec.total_expenses - rec.total_income
            else:
                rec.total_net = rec.total_income - rec.total_expenses
            if rec.total_net > 0:
                rec.financial_aid = (abs(rec.total_net) * .5)
            else:
                rec.financial_aid = 0

    @api.depends('room_ids')
    def get_rooms_total(self):
        for rec in self:
            if rec.id:
                rooms = rec.env['benefit.housing.rooms'].sudo().search([('housing_id', '=', rec.id)])
                rec.rooms_number = len(rooms)

    @api.onchange('block', 'city_id', 'housing_number', 'house_number')
    def _compute_get_name(self):
        for rec in self:
            if rec.block and rec.city_id and rec.housing_number and rec.house_number:
                rec.name = str(rec.housing_number + "-" + rec.house_number + "-" + rec.block + "-" + str(
                    rec.city_id.code) + "-" + rec.street)

    def open_benefits(self):
        return {
            'name': _("Benefits"),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(self.env.ref(
                'odex_benefit.grant_benefit_tree').id, 'tree'),
                      (self.env.ref('odex_benefit.grant_benefit_form').id, 'form')],
            'res_model': 'grant.benefit',
            'type': 'ir.actions.act_window',
            'domain': "[('housing_id','=',%s)]" % (self.id),
            'target': 'current',
        }

    def open_rooms(self):
        context = {}
        context['default_housing_id'] = self.id
        return {
            'name': _("Rooms"),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(self.env.ref(
                'odex_benefit.housing_rooms_tree').id, 'tree'),
                      (self.env.ref('odex_benefit.housing_rooms_form').id, 'form')],
            'res_model': 'benefit.housing.rooms',
            'type': 'ir.actions.act_window',
            'context': context,
            'domain': "[('housing_id','=',%s)]" % (self.id),
            'target': 'current',
        }

    @api.onchange('room_ids')
    def onchange_room_ids(self):
        res = {}
        items_ids = []
        for record in self:
            items_ids.append(record.id)
        res['domain'] = {'items': [('room_id', 'in', items_ids)]}
        return res


class housingRooms(models.Model):
    _name = 'benefit.housing.rooms'
    _rec_name = 'rooms_type'
    _description = "Benefits - housing rooms"

    name = fields.Char(related='rooms_type.name')
    housing_id = fields.Many2one(
        'benefit.housing')
    rooms_type = fields.Many2one(
        'housing.rooms.type',
        string='room',
        required=False)
    rooms_categories_id = fields.Many2one(
        'rooms.categories')
    family_members = fields.Integer(
        string='',
        required=False)
    # male_members = fields.Integer(
    #     string='',
    #     required=False)
    # female_members = fields.Integer(
    #     string='',
    #     required=False)
    members_ids = fields.One2many(
        'housing.rooms.members',
        'room_id',
        string='')
    items = fields.One2many(
        comodel_name='benefit.housing.rooms.items',
        inverse_name='room_id',
        string='items',
        required=False)
    room_ribs = fields.Char(
        compute='_compute_space')
    width = fields.Selection(
        string='',
        selection=[('1', '1'),
                   ('2', '2'),
                   ('3', '3'),
                   ('4', '4'),
                   ('5', '5'),
                   ('6', '6'),
                   ('7', '7'),
                   ('8', '8'),
                   ('9', '9'), ],
        required=False, )
    length = fields.Selection(
        string='',
        selection=[('1', '1'),
                   ('2', '2'),
                   ('3', '3'),
                   ('4', '4'),
                   ('5', '5'),
                   ('6', '6'),
                   ('7', '7'),
                   ('8', '8'),
                   ('9', '9'), ],
        required=False, )
    room_space = fields.Char(
        compute='_compute_space')
    room_condition = fields.Char(
        string='',
        required=False)

    @api.onchange('width', 'length')
    def _compute_space(self):
        for i in self:
            if i.width and i.length:
                i.room_ribs = i.width + "*" + i.length
                i.room_space = int(i.width) * int(i.length)

    @api.onchange('rooms_type')
    def _load_items(self):
        items_list = []
        for r in self.rooms_type.mapped('items'):
            for item in r:
                items_list.append(item)
        for i in self.items:
            if i.item in items_list:
                items_list.remove(i.item)
        for room in items_list:
            self.sudo().update({'items': [(0, 0, {'item': room.id})]})


class HousingRoomsItems(models.Model):
    _name = 'benefit.housing.rooms.items'
    _description = "Benefits - housing items"

    name = fields.Char(
        string='',
        required=False)
    room_id = fields.Many2one(
        comodel_name='benefit.housing.rooms')
    item = fields.Many2one(
        'rooms.items',
        string='item',
        required=False)
    status = fields.Many2one(
        'item.status', )
    # compute='set_status')
    percentage = fields.Float(
        string='',
        # related="status.percentage",
        required=False)

    # @api.onchange('percentage')
    # def set_status(self):
    #     for rec in self:
    #         if rec.percentage:
    #             print(rec.percentage)
    #             status = rec.env['item.status'].sudo().search(
    #                 [('minimum_percentage', '<=', rec.percentage)('maximum_percentage', '>=', rec.percentage)])
    #             rec.status = status.id


class HousingRoomsMembers(models.Model):
    _name = 'housing.rooms.members'
    _description = "Benefits - housing members"

    room_id = fields.Many2one(
        'benefit.housing.rooms')
    housing_id = fields.Many2one('benefit.housing', related='room_id.housing_id')
    rooms_categories_id = fields.Many2one('rooms.categories', related='room_id.rooms_categories_id',
                                          string='',
                                          required=False)
    benefit_id = fields.Many2one(
        'grant.benefit',
        string='')
    age = fields.Integer(
        string='',
        related='benefit_id.age', required=False)
    gender = fields.Selection(selection=[('male', 'Male'), ('female', 'Female')], related='benefit_id.gender',
                              string="Gender")
    is_accept = fields.Boolean(
        string='',
        store=True,
        compute='_check_accept',
        required=False)

    @api.depends('age', 'gender')
    def _check_accept(self):
        for i in self:
            i.is_accept = False
            if i.age >= i.room_id.rooms_categories_id.age_from and i.age <= i.room_id.rooms_categories_id.age_to and (
                    i.gender == i.room_id.rooms_categories_id.gender or i.room_id.rooms_categories_id.gender == 'both'):
                i.is_accept = True


class RoomsType(models.Model):
    _name = 'housing.rooms.type'
    _rec_name = 'name'
    _description = "Benefits - rooms type"

    name = fields.Char(
        string='',
        required=False)
    items = fields.Many2many('rooms.items',
                             string='')


class RoomsItems(models.Model):
    _name = 'rooms.items'
    _rec_name = 'name'
    _description = "Benefits - rooms items"

    name = fields.Char(
        string='',
        required=False)
    description = fields.Char(
        string='Description',
        required=False)


class RoomsCategories(models.Model):
    _name = 'rooms.categories'
    _rec_name = 'name'
    _description = "Benefits - rooms categories"

    name = fields.Char(
        string='',
        required=False)
    age_from = fields.Integer(
        string='',
        required=False)
    age_to = fields.Integer(
        string='',
        required=False)
    gender = fields.Selection(selection=[('male', 'Male only'), ('female', 'Female only'), ('both', 'both')],
                              string="Gender")
    description = fields.Char(
        string='Description',
        required=False)


class ItemStatus(models.Model):
    _name = 'item.status'
    _description = "Benefits - item status"

    name = fields.Char(
        string='',
        required=False)

    minimum_percentage = fields.Float(
        string='',
        required=False)
    maximum_percentage = fields.Float(
        string='',
        required=False)


class DomesticLabor(models.Model):
    _name = 'domestic.labor'
    _description = "Benefits - domestic labor"

    name = fields.Char(string='name')

    # @staticmethod
    # def _get_default_color():
    #     return randint(1, 11)

    color = fields.Integer(string='Color Index')


class housingNeed(models.Model):
    _name = 'housing.need'
    _description = 'housing needs'

    ap_id = fields.Many2one(
        'appliances.furniture')
    housing_id = fields.Many2one(
        'benefit.housing')
    benefit_id = fields.Many2one(
        'grant.benefit')
    amount = fields.Float(
        string='',
        required=False)

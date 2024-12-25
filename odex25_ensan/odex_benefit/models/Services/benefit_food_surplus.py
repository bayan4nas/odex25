from odoo import fields, models, api, _
from datetime import datetime
from odoo.exceptions import UserError, ValidationError


# receive
class ReceiveFoodSurplus(models.Model):
    _name = 'receive.food.surplus'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Receive Food Surplus'

    # TODO
    # barcode
    # sms notification

    name = fields.Char()
    surplus_type = fields.Many2many(
        'food.surplus.type',
        string='',
        required=False)
    quantity = fields.Float(
        compute='_compute_quantity',
        string='',
        required=False)
    zone = fields.Char(
        string='',
        required=False)
    neighborhood = fields.Char(
        string='',
        required=False)
    city_id = fields.Many2one(
        comodel_name='res.country.city',
        string='',
        required=False)
    address = fields.Char(
        string='',
        required=False)
    location = fields.Char(
        string='Location',
        required=False)
    surplus_ids = fields.One2many(
        'food.surplus.line',
        'food_surplus_id',
        string='surplus',
        required=False)
    # barcode
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approve', 'Waiting Approved'),
        ('approve', 'Approved'),
        ('refused', 'Refused')
    ], string='state', default="draft", tracking=True)

    # @api.multi
    def open_map(self):
        for Location in self:
            url = "http://maps.google.com/maps?oi=map&q="
            if Location.city_id:
                url += '+' + Location.city_id.name.replace(' ', '+')
                url += '+' + Location.city_id.state_id.name.replace(' ', '+')
                url += '+' + Location.city_id.country_id.name.replace(' ', '+')
            if Location.zone:
                url += '+' + Location.zone.replace(' ', '+')
            if Location.name:
                url += Location.name.replace(' ', '+')
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': url
        }

    def action_submit(self):
        self.state = 'waiting_approve'

    def action_approve(self):
        self.state = 'approve'

    def action_refused(self):
        self.state = 'refused'

    @api.onchange('surplus_ids')
    def _compute_quantity(self):
        for rec in self:
            rec.quantity = 0.0
            if rec.surplus_ids:
                for payment in rec.surplus_ids:
                    rec.quantity += payment.quantity


class benefitFoodSurplus(models.Model):
    _name = 'benefit.food.surplus'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Food Surplus'

    # TODO
    # barcode
    # sms notification

    partner_id = fields.Many2one('res.partner', 'Responsible')
    name = fields.Char()
    surplus_type = fields.Many2many(
        'food.surplus.type',
        string='',
        required=False)
    benefit_count = fields.Integer(
        string='',
        required=False)
    phone = fields.Char(related='partner_id.phone')
    quantity = fields.Float(
        compute='_compute_quantity',
        string='',
        required=False)
    zone = fields.Char(
        string='',
        required=False)
    neighborhood = fields.Char(
        string='',
        required=False)
    city_id = fields.Many2one(
        comodel_name='res.country.city',
        string='',
        required=False)
    address = fields.Char(
        string='',
        required=False)
    location = fields.Char(
        string='Location',
        required=False)
    lat = fields.Char()
    lon = fields.Char()
    surplus_ids = fields.One2many(
        'food.surplus.line',
        'food_surplus_id',
        string='surplus',
        required=False)
    # barcode
    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting_approve', 'Waiting Approved'),
        ('approve', 'Approved'),
        ('refused', 'Refused')
    ], string='state', default="draft", tracking=True)

    # @api.multi
    def open_map(self):
        for Location in self:
            url = "http://maps.google.com/maps?oi=map&q="
            if Location.city_id:
                url += '+' + Location.city_id.name.replace(' ', '+')
                url += '+' + Location.city_id.state_id.name.replace(' ', '+')
                url += '+' + Location.city_id.country_id.name.replace(' ', '+')
            if Location.zone:
                url += '+' + Location.zone.replace(' ', '+')
            if Location.name:
                url += Location.name.replace(' ', '+')
        return {
            'type': 'ir.actions.act_url',
            'target': 'new',
            'url': url
        }

    def action_submit(self):
        self.state = 'waiting_approve'

    def action_approve(self):
        self.state = 'approve'

    def action_refused(self):
        self.state = 'refused'

    @api.onchange('surplus_ids')
    def _compute_quantity(self):
        for rec in self:
            rec.quantity = 0.0
            if rec.surplus_ids:
                for payment in rec.surplus_ids:
                    rec.quantity += payment.quantity


class FoodSurplus(models.Model):
    _name = 'food.surplus.line'
    _description = 'Food Surplus'

    food_surplus_id = fields.Many2one(
        'benefit.food.surplus',
        string='',
        required=False)
    benefit_ids = fields.Many2many(
        'grant.benefit',
        string='',
        required=False)
    surplus_type = fields.Many2one(
        'food.surplus.type',
        string='',
        required=False)
    surplus_count = fields.Integer(
        string='',
        required=False)
    date_start = fields.Date(
        string='',
        required=False)
    date_end = fields.Date(
        string='',
        required=False)
    quantity = fields.Float(
        string='',
        required=False)
    description = fields.Char(
        string='',
        required=False)
    is_available = fields.Boolean(compute="_compute_available", store=True)

    @api.onchange('benefit_ids')
    def _compute_available(self):
        for rec in self:
            now = datetime.now().date()
            if rec.date_start and rec.date_end:
                if len(rec.benefit_ids) > rec.surplus_count or (str(rec.date_start) <= str(now) <= str(rec.date_end)):
                    rec.is_available = True
                else:
                    rec.is_available = False

    @api.onchange('benefit_ids')
    def benefit_limit(self):
        for rec in self:
            if len(rec.benefit_ids) <= rec.surplus_count:
                pass
            else:
                raise ValidationError(
                    _(u' You cant Add benefits'))


class FoodSurplusType(models.Model):
    _name = 'food.surplus.type'
    _description = 'Food Surplus'

    name = fields.Char(
        string='',
        required=False)

    description = fields.Char(
        string='description',
        required=False)

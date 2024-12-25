from odoo import fields, models, api, _


class BenefitsNeeds(models.Model):
    _name = 'benefits.needs'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'percentage of need of benefit '

    name = fields.Char(string='', required=False)
    benefit_need_type = fields.Selection(
        string='',
        selection=[('special', 'special (for one)'),
                   ('general', 'general(for group)'), ],
        required=False, )
    date = fields.Datetime(
        string='',
        required=False)
    benefit_id = fields.Many2one(
        'grant.benefit',
        string='',
        required=False)
    description = fields.Char(
        string='',
        required=False)
    benefit_type = fields.Selection(
        string='Benefits Type',
        selection=[('orphans', _('orphans')),
                   ('widows', _('widows')),
                   ('both', _('Both')),
                   ],
        compute='_onchange_benefit_ids',
        required=False, store=True)
    need_status = fields.Selection(string='',
                                   selection=[('urgent', 'urgent'),
                                              ('not_urgent', 'Not urgent'), ],
                                   required=False, )
    need_category = fields.Many2one('needs.categories', required=False)
    category_name = fields.Char(related='need_category.name')
    need_type_ids = fields.Many2many('product.product', string='')
    city_id = fields.Many2one('res.country.city')
    city_name = fields.Char(related='city_id.name')
    benefit_ids = fields.Many2many('grant.benefit', string='')
    target_amount = fields.Float(string='', compute="_onchange_paid_amount")
    f_amount = fields.Float(string='')
    paid_amount = fields.Float(string='', compute='_onchange_paid_amount')
    remaining_amount = fields.Float(string='', compute='_onchange_paid_amount')
    completion_ratio = fields.Float(string='', compute='_onchange_paid_amount')
    payments_ids = fields.One2many('needs.payment.line', 'need_id')
    need_attach = fields.Binary(string="", )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('sent', 'sent'),
        ('review', 'Under Review'),
        ('approve', 'Approved'),
        ('published', 'Published'),
        ('refused', 'Refused'),
        ('done', 'Done'),
    ], string='state', default="draft", tracking=True)

    benefit_count = fields.Integer(string='Benefits count for needs',
                                   compute='_compute_needs_benefit_count', store=True)

    @api.depends('benefit_id', 'benefit_ids')
    def _compute_needs_benefit_count(self):
        """ Calculate needs benefits count """
        for rec in self:
            if rec.benefit_ids:
                rec.benefit_count = len(rec.benefit_ids)
            elif rec.benefit_id:
                rec.benefit_count = 1
            else:
                rec.benefit_count = 0

    def action_submit(self):
        for rec in self:
            rec.state = 'sent'

    def action_review(self):
        for rec in self:
            rec.state = 'review'

    def action_approve(self):
        for rec in self:
            rec.state = 'approve'

    def action_published(self):
        for rec in self:
            rec.state = 'published'

    def action_refused(self):
        for rec in self:
            rec.state = 'refused'

    def action_done(self):
        for rec in self:
            rec.state = 'done'

    @api.onchange('need_category')
    def _onchange_need_category(self):
        for rec in self:
            need_list = []
            for i in rec.need_category.product_ids:
                need_list.append(i.id)
            rec.need_type_ids = [(6, 0, need_list)]

    @api.onchange('benefit_ids', 'benefit_id')
    def _onchange_benefit_ids(self):
        for rec in self:
            b_type = []
            if rec.benefit_ids:
                for i in rec.benefit_ids:
                    b_type.append(i.benefit_type)
            if rec.benefit_id:
                for i in rec.benefit_id:
                    b_type.append(i.benefit_type)
            if 'orphan' in b_type and 'widow' not in b_type:
                rec.benefit_type = 'orphans'
            if 'widow' in b_type and 'orphan' not in b_type:
                rec.benefit_type = 'widows'
            if 'widow' in b_type and 'orphan' in b_type:
                rec.benefit_type = 'both'
            if b_type == []:
                rec.benefit_type = False

    @api.onchange('need_type_ids', 'paid_amount', 'need_category')
    def _onchange_paid_amount(self):
        for rec in self:
            paid_amount = 0.0
            target_amount = 0.0
            for pay in rec.payments_ids:
                if pay.state == 'paid':
                    paid_amount += pay.amount
            rec.paid_amount = format(paid_amount, '.2f')
            for i in rec.need_type_ids:
                if rec.f_amount > 0:
                    target_amount = rec.f_amount
                else:
                    target_amount += i.lst_price
            rec.target_amount = format(target_amount, '.2f')
            if rec.target_amount:
                remaining_amount = format(rec.target_amount - rec.paid_amount, '.2f')
                rec.remaining_amount = remaining_amount
                if not rec.target_amount == 0.0 and rec.target_amount >= rec.paid_amount:
                    completion_ratio = 100 - ((rec.remaining_amount / rec.target_amount) * 100)
                    rec.completion_ratio = format(completion_ratio, '.2f')
                else:
                    rec.completion_ratio = 0.0
            else:
                rec.remaining_amount = 0.0
                rec.completion_ratio = 0.0
                    # else:
                #     raise ValidationError(
                #         _(u' You cant Add pay anymore'))


class Payments(models.Model):
    _name = 'needs.payment.line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Payments'

    need_id = fields.Many2one('benefits.needs')
    invoice_id = fields.Many2one('account.move')
    partner_id = fields.Many2one('res.partner', related="invoice_id.partner_id")
    amount = fields.Monetary(related="invoice_id.amount_total")
    currency_id = fields.Many2one('res.currency', string='Currency', readonly=True, related="invoice_id.currency_id")
    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('paid', 'Paid'),
        ('cancel', 'Cancelled'), ], store=True, related="invoice_id.state")
    date = fields.Date(related="invoice_id.invoice_date")


class NeedsCategories(models.Model):
    _name = 'needs.categories'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Categories of need of benefit '

    name = fields.Char(
        string='',
        required=False)
    description = fields.Char(
        string='',
        required=False)
    product_ids = fields.Many2many('product.product')


class PercentageOfNeed(models.Model):
    _name = 'benefit.need'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'percentage of need of benefit '

    name = fields.Char()
    housing_id = fields.Many2one(
        'benefit.housing',
        string='',
        tracking=True,
        required=False)
    benefit_ids = fields.One2many('grant.benefit', 'housing_id', string="Benefits")
    house_need = fields.One2many(
        comodel_name='house.need',
        inverse_name='benefit_need_id',
        string='',
        required=False)
    total_expenses = fields.Float(
        compute='_get_total_expenses',
        store=True,
        tracking=True,
        string='',
        required=False)
    expenses_ids = fields.Many2many(
        comodel_name='grant.benefit',relation='grant_benefit_group_rel',compute='_get_total_expenses',column1='benefit_id',column2='grant_id',tracking=True,
        store=True,
        string='',
        required=False)
    income_ids = fields.Many2many(
        'grant.benefit',
        compute='_get_total_income',
        tracking=True,
        store=True,
        string='',
        required=False)
    total_income = fields.Float(
        compute='_get_total_income',
        tracking=True,
        store=True,
        string='total income',
        required=False)
    total_net = fields.Float(
        string='net',
        store=True,
        compute='_get_total_net',
        tracking=True,
        required=False)
    financial_aid = fields.Float(
        string='Financial Aid',
        store=True,
        compute='_get_total_net',
        tracking=True,
        required=False)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('visit', 'field visit'),
        ('waiting_approve', 'Waiting Approved'),
        ('approve', 'Approved'),
        ('refused', 'Refused'),
    ], string='state', default="draft", tracking=True)

    def action_visit(self):
        self.state = 'visit'

    def action_waiting_approve(self):
        self.state = 'waiting_approve'

    def action_approve(self):
        self.state = 'approve'

    def action_refused(self):
        self.state = 'refused'

    @api.depends('housing_id')
    def _get_total_expenses(self):
        for rec in self:
            if rec.state == 'draft':
                benefit_id = rec.env['grant.benefit'].sudo().search([('housing_id', '=', rec.housing_id.id)])
                benefit_ids = rec.env['grant.benefit'].sudo().search(
                    [('housing_id', '=', rec.housing_id.id), ('benefit_type', '=', 'benefit')])
                benefit = []
                total_expenses = 0.0
                for i in benefit_id:
                    benefit.append(i.id)
                    total_expenses += i.total_expenses
                for r in self:
                    r.expenses_ids = [(6, 0, benefit)]
                    r.total_expenses = total_expenses

    @api.depends('housing_id')
    def _get_total_income(self):
        for rec in self:
            if rec.state == 'draft':
                benefit_ids = rec.env['grant.benefit'].sudo().search(
                    [('housing_id', '=', rec.housing_id.id), ('benefit_type', '=', 'benefit')])
                benefit = []
                total_income = 0.0
                for i in benefit_ids:
                    benefit.append(i.id)
                    total_income += i.total_income
                for r in rec:
                    r.income_ids = [(6, 0, benefit)]
                    r.total_income = total_income

    @api.depends('housing_id')
    def _get_total_net(self):
        for rec in self:
            if rec.state == 'draft':
                rec.total_net = 0.0
                rec.financial_aid = 0.0
                if rec.total_expenses >= rec.total_income:
                    rec.total_net = rec.total_expenses - rec.total_income
                else:
                    rec.total_net = rec.total_income - rec.total_expenses
                if rec.total_net < 0:
                    rec.financial_aid = (abs(rec.total_net) * .5)


class HouseNeed(models.Model):
    _name = 'house.need'
    _description = 'House Need'

    benefit_need_id = fields.Many2one(
        'benefit.need',
        string='',
        required=False)
    housing_id = fields.Many2one(
        'benefit.housing',
        string='',
        related="benefit_need_id.housing_id",
        required=False)
    room_id = fields.Many2one(
        'benefit.housing.rooms',
        string='',
        domain="[('housing_id', '=', housing_id)]",
        required=False)
    needs = fields.Char(
        string='',
        required=False)
    needs_percentage = fields.Float(
        string='',
        required=False)

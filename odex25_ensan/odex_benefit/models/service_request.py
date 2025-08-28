from multiprocessing.connection import families

from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import timedelta
from dateutil.relativedelta import relativedelta


class ServiceRequest(models.Model):
    _name = 'service.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Reference', required=True, copy=False, readonly=True, index=True,
                       default=lambda self: _('New'))
    # family_id = fields.Many2one('grant.benefit',string='Family')
    # is_main_service = fields.Boolean(string='Is Main Service?')
    # max_amount_for_student = fields.Float(string='Max Amount for Student')
    # raise_amount_for_orphan = fields.Float(string='Raise Amount For Orphan')
    # rent_lines = fields.One2many('rent.lines','services_settings_id')
    benefit_type = fields.Selection(string='Benefit Type',
                                    selection=[('family', 'Family'), ('member', 'Member'), ('detainee', 'Detainee')])
    date = fields.Datetime(string='Request Date', default=fields.Datetime.now)
    family_id = fields.Many2one('grant.benefit', string='Family', )
    family_category = fields.Many2one('benefit.category', string='Family Category',
                                      related='family_id.benefit_category_id')
    benefit_member_count = fields.Integer(string="Benefit Member count", related='family_id.member_count')
    branches_custom = fields.Many2one('branch.details', string="Branch")
    member_id = fields.Many2one(
        'family.member',
        string='Member',
    )
    detainee_member = fields.Many2one('family.member', string='Detainee')
    detainee_file = fields.Many2one('detainee.file', string='Detainee File')

    description = fields.Char(string='Description')
    need_status_id = fields.Many2one(
        "service.need.status",
        string="Need Status",
        tracking=True,

    )
    need_status = fields.Char(related="need_status_id.name")
    delivery_method_id = fields.Many2one(
        "service.delivery.method",
        string="Service Delivery Method",
        required=True

    )
    provider_id = fields.Many2one(
        "service.provider",
        string="Service Provider",
        required=True

    )

    partner_id = fields.Many2one("res.partner", string="Partner")

    provider_need_partner = fields.Boolean(
        related="provider_id.need_partner",
        store=True,
        readonly=True,
    )
    need_products = fields.Boolean(related="delivery_method_id.need_products", )

    main_service_category = fields.Many2one('services.settings', domain="[('is_main_service','=',True)]",
                                            string="Main Service Category")
    sub_service_category = fields.Many2one('services.settings',
                                           domain="[('is_main_service','=',False),('service_type','=',False),('parent_service','=',main_service_category)]",
                                           string='Sub Service Category')
    service_cat = fields.Many2one('services.settings', string='Service Cat.')
    service_cats = fields.Many2one('benefits.service', string='Service Cat.', domain=[('active', '=', True)])
    # service_attach = fields.Many2many('ir.attachment', 'rel_service_attachment_service_request', 'service_request_id','attachment_id', string='Service Attachment')
    requested_service_amount = fields.Float(string="Requested Service Amount")
    # yearly Estimated Rent Amount
    estimated_rent_amount = fields.Float(string="Estimated Rent Amount", compute="_get_estimated_rent_amount")
    # The value of payment by payment method(yearly-half-quartarly)
    estimated_rent_amount_payment = fields.Float(string="Estimated Rent Amount Payment",
                                                 compute="_get_estimated_rent_amount_payment")
    paid_rent_amount = fields.Float(string="Paid Rent Amount", compute="_get_paid_rent_amount")
    service_type = fields.Selection([('rent', 'Rent')], string='Service Type', related='service_cat.service_type')
    # is_alternative_housing = fields.Boolean(string='Is Alternative Housing?')
    rent_contract_number = fields.Char(string="Rent Contract Number", compute='_compute_rent_details', store=True)
    rent_start_date = fields.Date(string='Rent Start Date', compute='_compute_rent_details', store=True)
    rent_end_date = fields.Date(string='Rent End Date', compute='_compute_rent_details', store=True)
    rent_amount = fields.Float(string='Rent Amount', compute='_compute_rent_details', store=True)
    rent_amount_payment = fields.Float(string='Rent Amount Payment', compute='_get_rent_amount_payment')
    payment_type = fields.Selection([('1', 'Yearly'), ('2', 'Half Year'), ('4', 'Quarterly')], string='Payment Type',
                                    compute='_compute_rent_details', store=True)
    rent_attachment = fields.Many2many('ir.attachment', 'rel_rent_attachment_service_request', 'service_request_id',
                                       'attachment_id', string='Rent Attachment', compute='_compute_rent_details',
                                       store=True)
    rent_payment_date = fields.Date(string='Rent Payment Date')
    rent_payment_date_exception = fields.Boolean(string='Rent Payment Date Exception?')
    start = fields.Date(string="Start Date")
    end = fields.Date(string='End Date')
    # New Rent Contract
    new_rent_contract = fields.Boolean(string='New Rent Contract?')
    new_start = fields.Date(string="Start Date")
    new_end = fields.Date(string='End Date')
    new_rent_contract_number = fields.Char(string="Rent Contract Number")
    new_rent_start_date = fields.Date(string='Rent Start Date')
    new_rent_end_date = fields.Date(string='Rent End Date')
    new_rent_amount = fields.Float(string='Rent Amount')
    new_rent_amount_payment = fields.Float(string='New Rent Amount Payment', compute='_get_new_rent_amount_payment')
    new_payment_type = fields.Selection([('1', 'Yearly'), ('2', 'Half Year'), ('4', 'Quarterly')],
                                        string='Payment Type')
    new_rent_attachment = fields.Many2many('ir.attachment', 'rel_rent_attachment_service_request', 'service_request_id',
                                           'attachment_id', string='Rent Attachment')
    new_rent_payment_date = fields.Date(string='Rent Payment Date')
    new_rent_payment_date_exception = fields.Boolean(string='Rent Payment Date Exception?')
    # Rent details for member
    member_rent_contract_number = fields.Char(string="Rent Contract Number")
    member_rent_start_date = fields.Date(string='Rent Start Date')
    member_rent_end_date = fields.Date(string='Rent End Date')
    member_rent_attachment = fields.Many2many('ir.attachment', 'rel_member_rent_attachment_service_request',
                                              'service_request_id',
                                              'attachment_id', string='Rent Attachment')
    added_amount_if_mother_dead = fields.Float(string="Added Amount (If mother dead)",
                                               compute="_get_added_amount_if_mother_dead")
    attachment_lines = fields.One2many('service.attachments.settings', 'service_request_id', readonly=False)
    account_id = fields.Many2one('account.account', string='Expenses Account', related='service_cat.account_id')
    device_account_id = fields.Many2one('account.account', string='Expenses Account', related='device_id.account_id')
    accountant_id = fields.Many2one('res.users', string='Accountant', related='service_cat.accountant_id',
                                    readonly=False)
    service_producer_id = fields.Many2one('res.partner', string='Service Producer',
                                          related='service_cat.service_producer_id')
    is_service_producer = fields.Boolean(string='Is Service Producer?', related='service_cat.is_service_producer')
    # maintenance_items_id = fields.Many2one('home.maintenance.lines', string="Maintenance Items")
    maintenance_items_ids = fields.One2many('home.maintenance.items', 'service_request_id',
                                            string="Maintenance Items", )
    # Home restoration fields
    restoration_max_amount = fields.Float(string='Restoration Max Amount', compute='_get_restoration_max_amount')
    has_money_to_pay_first_payment = fields.Selection([('yes', 'Yes'), ('no', 'No')],
                                                      string='Has money to pay first payment?')
    has_money_field_is_appearance = fields.Boolean(string='Has money Field is appearance?',
                                                   compute='_get_money_field_is_appearance')
    payment_order_id = fields.Many2one('payment.orders', string='Payment Order')
    is_payment_order_done = fields.Boolean(string='Is Payment Order Done?')
    aid_amount = fields.Float(string='Aid Amount', compute='_get_aid_amount')
    # Fields for alternative house
    providing_alternative_housing_based_rent = fields.Boolean(string='Providing alternative housing based on rent')
    rent_for_alternative_housing = fields.Many2one('services.settings', compute='_get_rent_for_alternative_housing')

    # this field for complete building house service
    has_money_for_payment_is_appearance = fields.Boolean(string='Has money Field is appearance?',
                                                         compute='_get_money_for_payment_is_appearance')
    has_money_for_payment = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Has money for payment?')
    max_complete_building_house_amount = fields.Float(string='Max Complete Building House Amount',
                                                      related='service_cat.max_complete_building_house_amount')
    # Fields for electrical_devices service
    device_id = fields.Many2one('electrical.devices', string='Device',
                                domain="[('min_count_member','<=',benefit_member_count),('max_count_member','>=',benefit_member_count)]")
    vendor_bill = fields.Many2one('account.move')
    requested_quantity = fields.Integer(string='Requested Quantity')
    exception_or_steal = fields.Boolean(string='Exception Or Steal?')
    # Home furnishing Exception
    home_furnishing_exception = fields.Boolean(string='Exception(Fire Or Steal or Natural disaster)')
    furnishing_items_ids = fields.One2many('home.furnishing.items', 'service_request_id', string="Furnishing Items")
    # Electricity_bill
    max_electricity_bill_amount = fields.Float(string='Max Electricity Bill Amount')
    max_water_bill_amount = fields.Float(string='Max Water Bill Amount')
    # Transportation insurance
    service_reason = fields.Selection(selection=[
        ('government_transportation', 'Government Transportation'),
        ('universities_training_institutes_transportation', 'Universities Training Institutes Transportation'),
        ('hospitals_transportation', 'Hospitals Transportation'),
        ('programs_transportation', 'Programs Transportation'),
    ], string='Service Reason')
    max_government_transportation_amount = fields.Float(string='Max Government Transportation Amount')
    max_universities_training_institutes_transportation_amount = fields.Float(
        string='Max Universities Training Institutes Transportation Amount')
    max_hospitals_transportation_amount = fields.Float(string='Max Hospitals Transportation Amount')
    max_programs_transportation_amount = fields.Float(string='Max Programs Transportation Amount')
    requests_counts = fields.Integer(string='Requests Counts', default=1)
    # Marriage
    member_age = fields.Integer(string="Member Age", related="member_id.age")
    member_payroll = fields.Float(string="Member Payroll", related="member_id.member_income")
    has_marriage_course = fields.Selection(selection=[
        ('yes', 'Yes'),
        ('no', 'No'),
    ], string='Has Marriage Course')
    # Eid Gift
    eid_gift_benefit_count = fields.Integer(string='Eid Gift Benefit Count', compute="_get_eid_gift_benefit_count")
    # Buy home
    amount_for_buy_home_for_member_count = fields.Float(string="Amount For Buy Home for member count",
                                                        compute='_get_amount_for_buy_home')
    home_age = fields.Integer(string='Home Age')
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('researcher', 'Researcher'),
        ('send_request', 'Send Request'),
        ('first_approve', 'Request First Approve'),
        ('second_approve', 'Request Second Approve'),
        ('accounting_approve', 'Accounting Approve'),
        ('send_request_to_supplier', 'Send Request To Supplier'),
        ('family_received_device', 'Family Received Device'),
        ('refused', 'Refused')
    ], string='state', default='draft', tracking=True)
    state_a = fields.Selection(related='state', tracking=False)
    state_b = fields.Selection(related='state', tracking=False)
    line_ids = fields.One2many('service.request.line', 'request_id', string='Product Lines')

    benefit_breadwinner_ids = fields.One2many(
        related='family_id.benefit_breadwinner_ids',
        string="Benefit breadwinner"
    )

    member_id_number = fields.Char(string="Id Number", related="member_id.member_id_number", readonly=True)
    beneficiary_category = fields.Selection(related="family_id.beneficiary_category", string="Member Status",
                                            store=True,
                                            readonly=True)

    member_id_phone = fields.Char(string="Contact Phone", related="member_id.member_phone")
    need_calculator = fields.Selection(related="family_id.need_calculator", string="Need Calculator", store=True,
                                       readonly=True)
    member_name = fields.Char(string="Name", related="member_id.name")
    first_breadwinner_id = fields.Many2one(
        'grant.benefit.breadwinner',
        string="First Breadwinner",
        compute="_compute_first_breadwinner",
        store=True
    )
    family_id_member_name = fields.Char(string="Name", related="first_breadwinner_id.member_name.name")
    family_id_member_id_number = fields.Char(string="Id Number",
                                             related="first_breadwinner_id.member_name.member_id_number", readonly=True)
    family_id_relationn = fields.Char(
        related="first_breadwinner_id.relation_id.name",
        string="Relation",
        readonly=True,

    )
    family_id_phone = fields.Char(string="Contact Phone", related="first_breadwinner_id.member_name.member_phone")
    member_id_relationn = fields.Char(
        string="Relation",
        compute="_compute_member_relation",
        store=True,
        readonly=True
    )
    allowed_member_ids = fields.Many2many('family.member', compute='_compute_allowed_members')

    @api.depends('family_id')
    def _compute_allowed_members(self):
        for rec in self:
            rec.allowed_member_ids = rec.family_id.benefit_member_ids.mapped('member_id')

    @api.onchange('service_cats')
    def _onchange_service_cats(self):
        if self.service_cats:
            self.attachment_lines = [(5, 0, 0)]
            self.attachment_lines = [
                (0, 0, {
                    'name': line.attachment_name,
                    'attachment_type': line.attach_type,
                })
                for line in self.service_cats.attachment_ids
            ]

    @api.onchange('detainee_file')
    def _onchange_detainee_file_id(self):
        if self.detainee_file:
            member_id = self.detainee_file.detainee_id.id
            return {'domain': {'detainee_member': [('id', '=', member_id)]}}
        return {'domain': {'detainee_member': []}}

    @api.depends('family_id', 'member_id')
    def _compute_member_relation(self):
        for rec in self:
            rec.member_id_relationn = False
            if rec.family_id and rec.member_id:
                rel = self.env['grant.benefit.member'].search([
                    ('grant_benefit_id', '=', rec.family_id.id),
                    ('member_id', '=', rec.member_id.id)
                ], limit=1)
                rec.member_id_relationn = rel.relation_id.name if rel else False

    @api.depends('benefit_breadwinner_ids')
    def _compute_first_breadwinner(self):
        for rec in self:
            if rec.benefit_breadwinner_ids:
                rec.first_breadwinner_id = rec.benefit_breadwinner_ids[0]
            else:
                rec.first_breadwinner_id = False

    @api.onchange('family_id', 'member_id')
    def _onchange_family_id(self):
        if self.family_id:
            member_ids = self.family_id.benefit_member_ids.mapped('member_id.id')
            if member_ids:
                return {
                    'domain': {'member_id': [('id', 'in', member_ids)]}
                }
            else:
                self.member_id = False
                return {
                    'domain': {'member_id': [('id', '=', 0)]}
                }
        elif self.member_id:
            families = self.member_id.family_file_link.id
            print(families, 'family_file_link')
            return {
                'domain': {'family_id': [('id', '=', families)]}
            }

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        if self.env.user and self.env.user.id and self.env.user.has_group(
                "odex_benefit.group_benefit_accountant_accept") \
                and not self.env.user.has_group("odex_benefit.group_benefit_payment_accountant_accept"):
            args += [('accountant_id', '=', self.env.user.id)]
        if self.env.user and self.env.user.id and self.env.user.has_group(
                "odex_benefit.group_benefit_accountant_accept") \
                and self.env.user.has_group("odex_benefit.group_benefit_payment_accountant_accept"):
            args += []
        return super(ServiceRequest, self).search(args, offset, limit, order, count)

    @api.model
    def create(self, vals):
        # Define the list of fields to check
        new_rent_fields = [
            'new_rent_contract_number',
            'new_rent_start_date',
            'new_rent_end_date',
            'new_rent_amount',
            'new_payment_type',
            'new_rent_attachment'
        ]
        res = super(ServiceRequest, self).create(vals)
        if not res.name or res.name == _('New'):
            res.name = self.env['ir.sequence'].sudo().next_by_code('service.request.sequence') or _('New')
        # Check if any of the specified fields are present in vals
        if any(field in vals for field in new_rent_fields) and vals['new_rent_contract']:
            if res.family_id:
                # Prepare values for family_id write
                update_values = {}
                if 'new_rent_contract_number' in vals:
                    update_values['contract_num'] = vals['new_rent_contract_number']
                if 'new_rent_start_date' in vals:
                    update_values['rent_start_date'] = vals['new_rent_start_date']
                if 'new_rent_end_date' in vals:
                    update_values['rent_end_date'] = vals['new_rent_end_date']
                if 'new_rent_amount' in vals:
                    update_values['rent_amount'] = vals['new_rent_amount']
                if 'new_payment_type' in vals:
                    update_values['payment_type'] = vals['new_payment_type']
                if 'new_rent_attachment' in vals:
                    update_values['rent_attachment'] = vals['new_rent_attachment']

                # Write updates to the related family_id
                res.family_id.write(update_values)
        return res

    def write(self, vals):
        # Define the list of fields you want to check
        new_rent_fields = ['new_rent_contract_number', 'new_rent_start_date', 'new_rent_end_date', 'new_rent_amount',
                           'new_payment_type', 'new_rent_attachment']
        result = super(ServiceRequest, self).write(vals)
        update_values = {}
        if any(field in vals for field in new_rent_fields) and self.new_rent_contract:
            for record in self:
                # Ensure family_id exists before proceeding
                if record.family_id:
                    # Prepare values for family_id write
                    update_values = {}
                    # Add fields to update_values only if they exist in vals
                    if 'new_rent_contract_number' in vals:
                        update_values['contract_num'] = vals['new_rent_contract_number']
                    if 'new_rent_start_date' in vals:
                        update_values['rent_start_date'] = vals['new_rent_start_date']
                    if 'new_rent_end_date' in vals:
                        update_values['rent_end_date'] = vals['new_rent_end_date']
                    if 'new_rent_amount' in vals:
                        update_values['rent_amount'] = vals['new_rent_amount']
                    if 'new_payment_type' in vals:
                        update_values['payment_type'] = vals['new_payment_type']
                    if 'new_rent_attachment' in vals:
                        update_values['rent_attachment'] = vals['new_rent_attachment']

                # Write the prepared update values to `family_id`
                record.family_id.write(update_values)

        return result

    def unlink(self):
        for request in self:
            if request.state not in ['draft']:
                raise UserError(_('You cannot delete this record'))
        return super(ServiceRequest, self).unlink()

    @api.depends('family_id')
    def _compute_rent_details(self):
        for rec in self:
            # Compute values only if they are not already set
            if rec.family_id:
                if not rec.rent_contract_number:
                    rec.rent_contract_number = rec.family_id.contract_num
                if not rec.rent_start_date:
                    rec.rent_start_date = rec.family_id.rent_start_date
                if not rec.rent_end_date:
                    rec.rent_end_date = rec.family_id.rent_end_date
                if not rec.rent_amount:
                    rec.rent_amount = rec.family_id.rent_amount
                if not rec.payment_type:
                    rec.payment_type = rec.family_id.payment_type
                if not rec.rent_attachment:
                    rec.rent_attachment = rec.family_id.rent_attachment

    def _get_estimated_rent_amount(self):
        for rec in self:
            rec.estimated_rent_amount = 0.0  # Default value

            if not rec.family_id:
                continue
            if rec.service_type == 'rent':
                for item in rec.service_cat.rent_lines:
                    # Check if benefit category and member count match
                    if rec.family_id.benefit_category_id != item.benefit_category_id or rec.family_id.benefit_member_count != item.benefit_count:
                        continue

                    # Determine rent amount based on branch type and property type
                    branch_type = rec.family_id.branches_custom.branch_type
                    is_shared_rent = rec.family_id.property_type == 'rent_shared'

                    if branch_type == 'branches':
                        rec.estimated_rent_amount = item.estimated_rent_branches * (
                            item.discount_rate_shared_housing if is_shared_rent else 1)
                    elif branch_type == 'governorates':
                        rec.estimated_rent_amount = item.estimated_rent_governorate * (
                            item.discount_rate_shared_housing if is_shared_rent else 1)
            if rec.service_type == 'alternative_housing':
                for item in rec.rent_for_alternative_housing.rent_lines:
                    # Check if benefit category and member count match
                    if rec.family_id.benefit_category_id != item.benefit_category_id or rec.family_id.benefit_member_count != item.benefit_count:
                        continue

                    # Determine rent amount based on branch type and property type
                    branch_type = rec.family_id.branches_custom.branch_type
                    is_shared_rent = rec.family_id.property_type == 'rent_shared'

                    if branch_type == 'branches':
                        rec.estimated_rent_amount = item.estimated_rent_branches * (
                            item.discount_rate_shared_housing if is_shared_rent else 1)
                    elif branch_type == 'governorates':
                        rec.estimated_rent_amount = item.estimated_rent_governorate * (
                            item.discount_rate_shared_housing if is_shared_rent else 1)

    def _get_estimated_rent_amount_payment(self):
        for rec in self:
            rec.estimated_rent_amount_payment = 0.0
            if rec.estimated_rent_amount and rec.payment_type:
                rec.estimated_rent_amount_payment = rec.estimated_rent_amount / int(rec.payment_type)
            if rec.estimated_rent_amount and rec.new_payment_type:
                rec.estimated_rent_amount_payment = rec.estimated_rent_amount / int(rec.new_payment_type)

    def _get_rent_amount_payment(self):
        for rec in self:
            if rec.rent_amount and rec.payment_type:
                rec.rent_amount_payment = rec.rent_amount / int(rec.payment_type)
            else:
                rec.rent_amount_payment = 0.0

    def _get_new_rent_amount_payment(self):
        for rec in self:
            if rec.new_rent_amount and rec.new_payment_type:
                rec.new_rent_amount_payment = rec.new_rent_amount / int(rec.new_payment_type)
            else:
                rec.new_rent_amount_payment = 0.0

    def _get_paid_rent_amount(self):
        for rec in self:
            rec.paid_rent_amount = min(rec.estimated_rent_amount_payment, rec.requested_service_amount)

    def _get_added_amount_if_mother_dead(self):
        for rec in self:
            rec.added_amount_if_mother_dead = 0.0
            if rec.family_id.mother_marital_conf.is_dead:
                rec.added_amount_if_mother_dead = rec.service_cat.raise_amount_for_orphan

    @api.depends('service_cat', 'family_id')
    def _get_restoration_max_amount(self):
        self.restoration_max_amount = 0.0
        for line in self.service_cat.home_restoration_lines:
            if line.benefit_category_id == self.family_category:
                self.restoration_max_amount = line.max_amount
            # else:
            #     self.restoration_max_amount = 0.0

    @api.depends('requested_service_amount', 'restoration_max_amount')
    def _get_money_field_is_appearance(self):
        for rec in self:
            if rec.requested_service_amount and rec.restoration_max_amount and rec.requested_service_amount > rec.restoration_max_amount:
                rec.has_money_field_is_appearance = True
            else:
                rec.has_money_field_is_appearance = False

    @api.depends('requested_service_amount', 'max_complete_building_house_amount')
    def _get_money_for_payment_is_appearance(self):
        for rec in self:
            if rec.requested_service_amount and rec.max_complete_building_house_amount and rec.requested_service_amount > rec.max_complete_building_house_amount:
                rec.has_money_for_payment_is_appearance = True
            else:
                rec.has_money_for_payment_is_appearance = False

    def _get_aid_amount(self):
        for rec in self:
            if rec.service_type == 'rent':
                rec.aid_amount = rec.paid_rent_amount + rec.added_amount_if_mother_dead
            else:
                rec.aid_amount = rec.requested_service_amount

    def _get_rent_for_alternative_housing(self):
        for rec in self:
            if rec.service_cat.service_type == 'alternative_housing':
                rec.rent_for_alternative_housing = self.env['services.settings'].search([('service_type', '=', 'rent')],
                                                                                        limit=1).id
            else:
                rec.rent_for_alternative_housing = False

    @api.depends('family_id')
    def _get_eid_gift_benefit_count(self):
        for rec in self:
            rec.eid_gift_benefit_count = 0
            if rec.family_id:
                rec.eid_gift_benefit_count = len(
                    rec.family_id.member_ids.filtered(lambda x: x.age <= rec.service_cat.member_max_age))

    @api.onchange('requests_counts', 'service_type')
    def _get_max_transportation_amounts(self):
        for rec in self:
            rec.max_government_transportation_amount = rec.requests_counts * rec.service_cat.max_government_transportation_amount
            rec.max_universities_training_institutes_transportation_amount = rec.requests_counts * rec.service_cat.max_universities_training_institutes_transportation_amount
            rec.max_hospitals_transportation_amount = rec.requests_counts * rec.service_cat.max_hospitals_transportation_amount
            rec.max_programs_transportation_amount = rec.requests_counts * rec.service_cat.max_programs_transportation_amount

    @api.depends('service_cat', 'family_id')
    def _get_amount_for_buy_home(self):
        for rec in self:
            rec.amount_for_buy_home_for_member_count = 0
            if rec.service_type == 'buy_home':
                rec.amount_for_buy_home_for_member_count = (rec.service_cat.buy_home_lines.filtered(lambda
                                                                                                        x: x.min_count_member <= rec.benefit_member_count <= rec.benefit_member_count)).amount_for_buy_home

    def action_for_researcher(self):
        for rec in self:
            rec.state = 'researcher'

    def action_send_request(self):
        for rec in self:
            rec.state = 'send_request'

    def action_first_approve(self):
        for rec in self:
            rec.state = 'first_approve'

    def action_second_approve(self):
        for rec in self:
            rec.state = 'second_approve'

    def action_accounting_approve(self):
        for rec in self:
            rec.state = 'accounting_approve'
            if rec.service_type == 'buy_car':
                rec.family_id.has_car = True

    def action_send_request_to_supplier(self):
        for rec in self:
            rec.state = 'send_request_to_supplier'

    def action_family_received_device(self):
        for rec in self:
            rec.state = 'family_received_device'

    def action_accounting_first_refuse(self):
        for rec in self:
            rec.state = 'draft'

    def action_refuse(self):
        for rec in self:
            rec.state = 'refused'

    @api.onchange('service_cat', 'family_id')
    def onchange_service_cat(self):
        for rec in self:
            if rec.service_cat.service_type == 'rent' and rec.family_id.property_type != 'rent' and rec.family_id.property_type != 'rent_shared' and rec.benefit_type == 'family':
                raise UserError(_("You cannot benefit from this service (property type not rent)"))
            if rec.service_cat.service_type == 'home_restoration' and rec.family_id.property_type != 'ownership' and rec.family_id.property_type != 'ownership_shared' and rec.family_id.property_type != 'charitable' and rec.benefit_type == 'family':
                raise UserError(_("You cannot benefit from this service (property type not ownership)"))

    @api.onchange('rent_payment_date', 'new_rent_payment_date')
    def onchange_rent_payment_date(self):
        today_date = fields.Date.today()
        for rec in self:
            if rec.rent_payment_date and not rec.rent_payment_date_exception and not rec.new_rent_payment_date:
                month_before_rent_payment_date = rec.rent_payment_date - timedelta(days=30)
                if today_date > month_before_rent_payment_date:
                    raise UserError(_("You Should request At least a month ago rent payment date"))
            if rec.new_rent_payment_date and not rec.new_rent_payment_date_exception:
                new_month_before_rent_payment_date = rec.new_rent_payment_date - timedelta(days=30)
                if today_date > new_month_before_rent_payment_date:
                    raise UserError(_("You Should request At least a month ago rent payment date"))

    @api.onchange('furnishing_items_ids')
    def _onchange_home_furnishing_cost(self):
        furnishing_cost_sum = 0
        for rec in self.furnishing_items_ids:
            furnishing_cost_sum += rec.furnishing_cost
        self.requested_service_amount = furnishing_cost_sum

    @api.onchange('member_id', 'family_id', 'eid_gift_benefit_count', 'service_cat')
    def _onchange_member(self):
        for rec in self:
            if rec.benefit_type == 'member' and rec.service_type == 'marriage':
                rec.requested_service_amount = rec.service_cat.fatherless_member_amount
                if not rec.member_id.benefit_id.add_replacement_mother and rec.member_id.benefit_id.mother_marital_conf.is_dead:
                    rec.requested_service_amount = rec.service_cat.orphan_member_amount
                if rec.member_id.benefit_id.add_replacement_mother and rec.member_id.benefit_id.replacement_mother_marital_conf.is_dead:
                    rec.requested_service_amount = rec.service_cat.orphan_member_amount
            if rec.benefit_type == 'family' and rec.service_type == 'eid_gift':
                rec.requested_service_amount = rec.eid_gift_benefit_count * rec.service_cat.eid_gift_member_amount
            if rec.benefit_type == 'member' and rec.service_type == 'eid_gift':
                rec.requested_service_amount = rec.service_cat.eid_gift_member_amount
            if rec.benefit_type == 'family' and rec.service_type == 'winter_clothing':
                rec.requested_service_amount = rec.benefit_member_count * rec.service_cat.winter_clothing_member_amount
            if rec.benefit_type == 'member' and rec.service_type == 'winter_clothing':
                rec.requested_service_amount = rec.service_cat.winter_clothing_member_amount
            if rec.benefit_type == 'family' and rec.service_type == 'ramadan_basket':
                rec.requested_service_amount = rec.service_cat.ramadan_basket_member_amount

    @api.onchange('service_cat', 'family_id')
    def _onchange_service_cat(self):
        electricity_bill_amount = self.service_cat.electricity_bill_lines.filtered(lambda
                                                                                       x: x.benefit_category_id.id == self.family_category.id and x.max_count_member > self.benefit_member_count > x.min_count_member)
        water_bill_amount = self.service_cat.water_bill_lines.filtered(lambda
                                                                           x: x.benefit_category_id.id == self.family_category.id and x.max_count_member > self.benefit_member_count > x.min_count_member)
        self.max_electricity_bill_amount = electricity_bill_amount.max_amount_for_electricity_bill
        self.max_water_bill_amount = water_bill_amount.max_amount_for_water_bill

    @api.onchange('requested_service_amount', 'benefit_type', 'date', 'service_cat', 'family_id', 'exception_or_steal',
                  'home_furnishing_exception', 'has_marriage_course', 'home_age')
    def onchange_requested_service_amount(self):
        res = {}
        today = fields.Date.today()
        date_before_year = today - timedelta(days=365)
        date_before_seven_years = today - relativedelta(years=7)
        date_before_three_years = today - relativedelta(years=3)
        date_before_ten_years = today - timedelta(days=3650)
        date_before_month = today - timedelta(days=30)
        for rec in self:
            # Validation for 'member' benefit type
            if rec.benefit_type == 'member' and rec.service_cat.service_type == 'rent':
                max_requested_amount = rec.service_cat.max_amount_for_student
                if rec.requested_service_amount > max_requested_amount:
                    self.benefit_type = False
                    res['warning'] = {'title': _('ValidationError'),
                                      'message': _("You cannot request more than %s") % max_requested_amount}
                    return res

            # Validation for 'family' benefit type with 'home_maintenance'
            if rec.benefit_type == 'family' and rec.service_cat.service_type == 'home_maintenance':
                max_requested_amount = rec.service_cat.max_maintenance_amount
                if rec.requested_service_amount > max_requested_amount:
                    self.benefit_type = False
                    res['warning'] = {'title': _('ValidationError'),
                                      'message': _("You cannot request more than %s") % max_requested_amount}
                    return res

                # Prevent multiple 'home_maintenance' requests within the same year
                existing_request_maintenance = self.search([
                    ('date', '>', date_before_year),
                    ('family_id', '=', rec.family_id.id),
                    ('service_cat.service_type', '=', 'home_maintenance'), ('id', '!=', self._origin.id)
                ], limit=1)
                if existing_request_maintenance:
                    raise UserError(_("You cannot request this service more than once a year."))
                existing_request_restoration = self.search([
                    ('date', '>', date_before_year),
                    ('family_id', '=', rec.family_id.id),
                    ('service_cat.service_type', '=', 'home_restoration'), ('id', '!=', self._origin.id)
                ], limit=1)
                if existing_request_restoration:
                    raise UserError(_("You cannot request this service with restoration service in the same year."))
            # Validation for 'family' benefit type with 'home_restoration'
            if rec.benefit_type == 'family' and rec.service_cat.service_type == 'home_restoration':
                # Prevent multiple 'home_maintenance' requests within the same year
                existing_request_restoration = self.search([
                    ('date', '>', date_before_ten_years),
                    ('family_id', '=', rec.family_id.id),
                    ('service_cat.service_type', '=', 'home_restoration'), ('id', '!=', self._origin.id)
                ], limit=1)
                if existing_request_restoration:
                    raise UserError(_("You cannot request this service more than once a ten years."))
                existing_request_maintenance = self.search([
                    ('date', '>', date_before_year),
                    ('family_id', '=', rec.family_id.id),
                    ('service_cat.service_type', '=', 'home_maintenance')
                ], limit=1)
                if existing_request_maintenance:
                    raise UserError(
                        _("You cannot request this service with maintenance service in the same year."))

            # Validation for 'family' benefit type with 'complete_building_house' service type
            if rec.benefit_type == 'family' and rec.service_cat.service_type == 'complete_building_house':
                # Check for existing request of the same type
                existing_request = self.search([
                    ('family_id', '=', rec.family_id.id),
                    ('service_cat.service_type', '=', 'complete_building_house'),
                ], limit=1)
                if existing_request:
                    raise UserError(
                        _("You Cannot request this service twice"))
                existing_request_restoration = self.search([
                    ('family_id', '=', rec.family_id.id),
                    ('service_cat.service_type', '=', 'home_restoration'),
                ], limit=1)
                if existing_request_restoration:
                    raise UserError(
                        _("You Cannot request this service and home restoration twice"))
            # Validation for 'family' benefit type with 'electrical_devices' service type
            if rec.benefit_type == 'family' and rec.service_cat.service_type == 'electrical_devices':
                # Check for existing request of the same type in seven years and not exception or steal
                existing_request = self.search([
                    ('family_id', '=', rec.family_id.id),
                    ('service_cat.service_type', '=', 'electrical_devices'),
                    ('date', '>', date_before_seven_years),
                    ('device_id', '=', rec.device_id.id)
                ], limit=1)
                if existing_request and not rec.exception_or_steal:
                    raise UserError(
                        _("You Cannot request this service twice in seven years"))
            # Validation for 'family' benefit type with 'home_furnishing' service type
            if rec.benefit_type == 'family' and rec.service_cat.service_type == 'home_furnishing':
                # Add current record conditionally
                domain = [
                    ('family_id', '=', self.family_id.id),
                    ('service_cat.service_type', '=', 'home_furnishing'),
                    ('date', '>', date_before_three_years),
                    ('id', '!=', self._origin.id),
                ]
                # if self.id:
                #     domain.append(('id', '!=', self.id))  # Exclude current record if already saved

                # Search for existing requests
                existing_requests_within_three_years = self.search(domain)

                # Include current record in the calculation
                total_amount_in_three_years = sum(
                    existing_requests_within_three_years.mapped('requested_service_amount'))
                total_amount_in_three_years += sum(self.furnishing_items_ids.mapped('furnishing_cost'))
                if not rec.home_furnishing_exception:
                    if total_amount_in_three_years > rec.service_cat.max_furnishing_amount:
                        self.benefit_type = False
                        res['warning'] = {'title': _('ValidationError'),
                                          'message': _(
                                              "You cannot request more than %s within 3 years") % rec.service_cat.max_furnishing_amount}
                        return res
                if rec.home_furnishing_exception:
                    if total_amount_in_three_years > rec.service_cat.max_furnishing_amount_if_exception:
                        self.benefit_type = False
                        res['warning'] = {'title': _('ValidationError'),
                                          'message': _(
                                              "You cannot request more than %s within 3 years") % rec.service_cat.max_furnishing_amount_if_exception}
                        return res
            # Validation for 'family' benefit type with 'electricity_bill' service type
            if rec.benefit_type == 'family' and rec.service_cat.service_type == 'electricity_bill':
                # Add current record conditionally
                domain = [
                    ('family_id', '=', self.family_id.id),
                    ('service_cat.service_type', '=', 'electricity_bill'),
                    ('date', '>', date_before_month)
                ]
                # Search for existing requests
                existing_requests_within_month = self.search(domain)
                if existing_requests_within_month:
                    raise UserError(_("You cannot request this service agin in this month"))
                if rec.requested_service_amount > rec.max_electricity_bill_amount:
                    self.benefit_type = False
                    res['warning'] = {'title': _('ValidationError'),
                                      'message': _(
                                          "You cannot request more than %s") % rec.max_electricity_bill_amount}
                    return res
            # Validation for 'family' benefit type with 'water_bill' service type
            if rec.benefit_type == 'family' and rec.service_cat.service_type == 'water_bill':
                # Add current record conditionally
                domain = [
                    ('family_id', '=', self.family_id.id),
                    ('service_cat.service_type', '=', 'water_bill'),
                    ('date', '>', date_before_year), ('id', '!=', self._origin.id)
                ]
                # Search for existing requests
                existing_requests_within_year = self.search(domain)
                if existing_requests_within_year:
                    raise UserError(_("You cannot request this service agin in this year"))
                if rec.requested_service_amount > rec.max_water_bill_amount:
                    self.benefit_type = False
                    res['warning'] = {'title': _('ValidationError'),
                                      'message': _(
                                          "You cannot request more than %s") % rec.max_water_bill_amount}
                    return res
            # Validation for 'family' benefit type with  'buy_car' service type
            if rec.benefit_type == 'family' and rec.service_cat.service_type == 'buy_car':
                if rec.family_id.has_car:
                    raise UserError(_("You cannot request this service because you had a car"))
                if rec.benefit_member_count < rec.service_cat.min_count_member:
                    raise UserError(
                        _("You cannot request this service because you are less than %s") % rec.service_cat.min_count_member)
                if rec.requested_service_amount > rec.service_cat.max_buy_car_amount:
                    self.benefit_type = False
                    res['warning'] = {'title': _('ValidationError'),
                                      'message': _(
                                          "You cannot request more than %s") % rec.service_cat.max_buy_car_amount}
                    return res
            # Validation for 'family' benefit type with  'recruiting_driver' service type
            if rec.benefit_type == 'family' and rec.service_cat.service_type == 'recruiting_driver':
                recruiting_driver_existing_request = self.search([
                    ('family_id', '=', self.family_id.id),
                    ('service_cat.service_type', '=', 'recruiting_driver'), ('id', '!=', self._origin.id)],
                    limit=1)
                son_members_above_age = rec.family_id.mapped('member_ids').filtered(
                    lambda x: x.relationn.relation_type == 'son' and x.age > 18)
                daughter_members_above_age = rec.family_id.mapped('member_ids').filtered(
                    lambda x: x.relationn.relation_type == 'daughter' and x.age > 18)
                disable_mother = rec.family_id.mapped('member_ids').filtered(
                    lambda x: x.relationn.relation_type == 'mother' and x.has_disabilities)
                work_mother = rec.family_id.mapped('member_ids').filtered(
                    lambda x: x.relationn.relation_type == 'mother' and x.is_mother_work)
                disable_replacement_mother = rec.family_id.mapped('member_ids').filtered(
                    lambda x: x.relationn.relation_type == 'replacement_mother' and x.has_disabilities)
                work_replacement_mother = rec.family_id.mapped('member_ids').filtered(lambda
                                                                                          x: x.relationn.relation_type == 'replacement_mother' and x.replacement_is_mother_work)
                if not rec.family_id.has_car:
                    raise UserError(_("You cannot request this service because you do not have a car"))
                if son_members_above_age or daughter_members_above_age:
                    raise UserError(
                        _("You cannot request this service because children above 18 years"))
                if rec.family_id.add_replacement_mother and not disable_replacement_mother and not work_replacement_mother:
                    raise UserError(
                        _("You cannot request this service because mother should be worked or has disability"))
                if not rec.family_id.add_replacement_mother and not disable_mother and not work_mother:
                    raise UserError(
                        _("You cannot request this service because mother should be worked or has disability"))
                if recruiting_driver_existing_request:
                    raise UserError(
                        _("You cannot request this service Again"))
                if rec.requested_service_amount > rec.service_cat.max_recruiting_driver_amount:
                    self.benefit_type = False
                    res['warning'] = {'title': _('ValidationError'),
                                      'message': _(
                                          "You cannot request more than %s") % rec.service_cat.max_recruiting_driver_amount}
                    return res
            # Validation for 'family' benefit type with  'transportation_insurance' service type
            if rec.benefit_type == 'family' and rec.service_cat.service_type == 'transportation_insurance':
                if rec.service_reason == 'government_transportation':
                    if rec.requested_service_amount > rec.max_government_transportation_amount:
                        self.benefit_type = False
                        res['warning'] = {'title': _('ValidationError'),
                                          'message': _(
                                              "You cannot request more than %s") % rec.max_government_transportation_amount}
                        return res
                if rec.service_reason == 'universities_training_institutes_transportation':
                    if rec.requested_service_amount > rec.max_universities_training_institutes_transportation_amount:
                        self.benefit_type = False
                        res['warning'] = {'title': _('ValidationError'),
                                          'message': _(
                                              "You cannot request more than %s") % rec.max_universities_training_institutes_transportation_amount}
                        return res
                if rec.service_reason == 'hospitals_transportation':
                    if rec.requested_service_amount > rec.max_hospitals_transportation_amount:
                        self.benefit_type = False
                        res['warning'] = {'title': _('ValidationError'),
                                          'message': _(
                                              "You cannot request more than %s") % rec.max_hospitals_transportation_amount}
                        return res
                if rec.service_reason == 'programs_transportation':
                    if rec.requested_service_amount > rec.max_programs_transportation_amount:
                        self.benefit_type = False
                        res['warning'] = {'title': _('ValidationError'),
                                          'message': _(
                                              "You cannot request more than %s") % rec.max_hospitals_transportation_amount}
                        return res
            # Validation for 'family' benefit type with  'recruiting_driver' service type
            if rec.benefit_type == 'family' and rec.service_cat.service_type == 'debits':
                if rec.requested_service_amount > rec.service_cat.max_debits_amount:
                    self.benefit_type = False
                    res['warning'] = {'title': _('ValidationError'),
                                      'message': _(
                                          "You cannot request more than %s") % rec.service_cat.max_debits_amount}
                    return res
            # Validation for 'family' benefit type with  'health_care' service type
            if rec.benefit_type == 'family' and rec.service_cat.service_type == 'health_care':
                # Add current record conditionally
                domain = [
                    ('family_id', '=', self.family_id.id),
                    ('service_cat.service_type', '=', 'health_care'),
                    ('date', '>', date_before_year),
                    ('id', '!=', self._origin.id),
                ]
                # Search for existing requests
                existing_requests_within_year = self.search(domain)

                # Include current record in the calculation
                total_amount_in_year = sum(existing_requests_within_year.mapped('requested_service_amount'))
                total_amount_in_year += rec.requested_service_amount
                if total_amount_in_year > rec.service_cat.max_health_care_amount:
                    self.benefit_type = False
                    res['warning'] = {'title': _('ValidationError'),
                                      'message': _(
                                          "You cannot request more than %s within year") % rec.service_cat.max_health_care_amount}
                    return res
            # Validation for 'family' benefit type with  'health_care' service type
            if rec.benefit_type == 'family' and rec.service_cat.service_type == 'recruiting_domestic_worker_or_nurse':
                # Add current record conditionally
                domain = [
                    ('family_id', '=', self.family_id.id),
                    ('service_cat.service_type', '=', 'recruiting_domestic_worker_or_nurse'),
                    ('date', '>', date_before_year),
                    ('id', '!=', self._origin.id),
                ]
                # Search for existing requests
                existing_requests_within_year = self.search(domain)
                if existing_requests_within_year:
                    raise UserError(_("You cannot request this service more than once Within year."))
                # Include current record in the calculation
                if rec.requested_service_amount > rec.service_cat.max_recruiting_domestic_worker_or_nurse_amount:
                    self.benefit_type = False
                    res['warning'] = {'title': _('ValidationError'),
                                      'message': _(
                                          "You cannot request more than %s within year") % rec.service_cat.max_recruiting_domestic_worker_or_nurse_amount}
                    return res
            if rec.benefit_type == 'member' and rec.service_cat.service_type == 'marriage':
                if rec.member_age > rec.service_cat.member_max_age:
                    self.benefit_type = False
                    res['warning'] = {'title': _('ValidationError'),
                                      'message': _(
                                          "Member Age should be less than %s ") % rec.service_cat.member_max_age}
                    return res
                if rec.member_payroll > rec.service_cat.member_max_payroll:
                    self.benefit_type = False
                    res['warning'] = {'title': _('ValidationError'),
                                      'message': _(
                                          "Member Payroll should be less than %s ") % rec.service_cat.member_max_payroll}
                    return res
                if rec.has_marriage_course == 'no':
                    raise UserError(_("You Should take a course"))
            # Validation for 'family' benefit type with  'eid_gift' service type
            if rec.benefit_type == 'family' and rec.service_cat.service_type == 'eid_gift':
                if rec.eid_gift_benefit_count == 0:
                    raise UserError(_("You cannot request this service"))
            # Validation for 'family' benefit type with  'natural_disasters' service type
            if rec.benefit_type == 'family' and rec.service_cat.service_type == 'natural_disasters':
                if rec.requested_service_amount > rec.service_cat.natural_disasters_max_amount:
                    self.benefit_type = False
                    res['warning'] = {'title': _('ValidationError'),
                                      'message': _(
                                          "You cannot request more than %s") % rec.service_cat.natural_disasters_max_amount}
                    return res
            # Validation for 'family' benefit type with  'legal_arguments' service type
            if rec.benefit_type == 'family' and rec.service_cat.service_type == 'legal_arguments':
                if rec.requested_service_amount > rec.service_cat.legal_arguments_max_amount:
                    self.benefit_type = False
                    res['warning'] = {'title': _('ValidationError'),
                                      'message': _(
                                          "You cannot request more than %s") % rec.service_cat.legal_arguments_max_amount}
                    return res
            # Validation for 'family' benefit type with  'buy_home' service type
            if rec.benefit_type == 'family' and rec.service_cat.service_type == 'buy_home':
                # Search for existing requests
                existing_buy_home_requests = self.search([('family_id', '=', self.family_id.id),
                                                          ('service_cat.service_type', '=', 'buy_home'),
                                                          ('id', '!=', self._origin.id)])
                existing_home_restoration_requests = self.search([('family_id', '=', self.family_id.id),
                                                                  ('service_cat.service_type', '=',
                                                                   'home_restoration'),
                                                                  ('id', '!=', self._origin.id)])
                if rec.requested_service_amount > rec.service_cat.buy_home_max_total_amount:
                    self.benefit_type = False
                    res['warning'] = {'title': _('ValidationError'),
                                      'message': _(
                                          "You cannot request more than %s") % rec.service_cat.buy_home_max_total_amount}
                    return res
                if existing_buy_home_requests:
                    raise UserError(_("You cannot request this service Again"))
                if existing_home_restoration_requests:
                    raise UserError(
                        _("You cannot request this service Again Because you request Home restoration service"))
                if rec.home_age > rec.service_cat.home_age:
                    raise UserError(
                        _("You cannot request this service Again Because the home Age More than %s") % rec.service_cat.home_age)

    @api.onchange('requested_quantity', 'benefit_type')
    def onchange_requested_quantity(self):
        res = {}
        for rec in self:
            if rec.requested_quantity > rec.device_id.allowed_quantity:
                self.benefit_type = False
                res['warning'] = {'title': _('ValidationError'),
                                  'message': _("You cannot request more than %s") % rec.device_id.allowed_quantity}
                return res

    @api.onchange('member_id')
    def onchange_member_id(self):
        for rec in self:
            if rec.member_id and rec.member_id.member_location != 'study_inside_saudi_arabia' and rec.service_type == 'rent':
                raise UserError(_("You Cannot request Service if you not study inside Saudi Arabia"))

    @api.onchange('start', 'end', 'rent_start_date', 'rent_end_date', 'new_start', 'new_end', 'new_rent_start_date',
                  'new_rent_end_date', 'new_rent_contract')
    def _check_date_range(self):
        for rec in self:
            # Ensure both start and end dates are set
            if rec.start and rec.end and rec.rent_start_date and rec.rent_end_date and not rec.new_rent_contract:
                # Check if `start` and `end` are within `rent_start_date` and `rent_end_date`
                if not (rec.rent_start_date <= rec.start <= rec.rent_end_date and
                        rec.rent_start_date <= rec.end <= rec.rent_end_date):
                    raise UserError(
                        "The Start Date and End Date must be within the Rent Start Date and Rent End Date range.")
            if rec.new_start and rec.new_end and rec.new_rent_start_date and rec.new_rent_end_date and rec.new_rent_contract:
                # Check if `start` and `end` are within `rent_start_date` and `rent_end_date`
                if not (rec.new_rent_start_date <= rec.new_start <= rec.new_rent_end_date and
                        rec.new_rent_start_date <= rec.new_end <= rec.new_rent_end_date):
                    raise UserError(
                        "The Start Date and End Date must be within the Rent Start Date and Rent End Date range.")

    @api.onchange('family_category', 'sub_service_category')
    def _onchange_service_cat_domain(self):
        # Build the dynamic domain
        domain = []
        if self.benefit_type == 'family':
            domain = [
                '|', '|', '|', '|',
                ('rent_lines.benefit_category_id', 'in', [self.family_category.id]),
                ('home_restoration_lines.benefit_category_id', 'in', [self.family_category.id]),
                ('electricity_bill_lines.benefit_category_id', 'in', [self.family_category.id]),
                ('water_bill_lines.benefit_category_id', 'in', [self.family_category.id]),
                ('benefit_category_ids', 'in', [self.family_category.id]),
                ('is_main_service', '=', False),
                ('service_type', '!=', False),
                ('parent_service', '=', self.sub_service_category.id)
            ]
        if self.benefit_type == 'member':
            domain = [
                # '|', '|',
                # ('rent_lines.benefit_category_id', 'in', [self.family_category.id]),
                # ('home_restoration_lines.benefit_category_id', 'in', [self.family_category.id]),
                ('benefit_category_ids', 'in', [self.family_category.id]),
                ('is_main_service', '=', False),
                ('service_type', '!=', False),
                ('parent_service', '=', self.sub_service_category.id),
                ('is_this_service_for_student', '=', True)
            ]
            # Apply the domain
        return {'domain': {'service_cat': domain}}

    def action_set_to_draft(self):
        for rec in self:
            rec.state = 'draft'

    def action_open_exchange_order_wizard(self):
        ids = []
        for rec in self:
            ids.append(rec.id)
        default_service_ids = ids
        service_requests = self.env['service.request'].browse(ids)
        if any(request.state not in 'accounting_approve' for request in service_requests):
            raise UserError(_("All selected requests should be in Accounting Approve state"))
        if any(request.payment_order_id for request in service_requests):
            raise UserError(_("All selected requests should be not has payment order"))
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Exchange Order',
                'res_model': 'exchange.order.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_service_ids': ids}
            }

    def create_vendor_bill(self):
        ids = []
        line_ids = []
        for rec in self:
            ids.append(rec.id)
        service_requests = self.env['service.request'].browse(ids)
        service_producer_id = self.env['service.request'].search([('id', '=', ids[0])], limit=1)
        if any(request.state not in 'family_received_device' for request in service_requests):
            raise UserError(_("All selected requests should be in Family Received Device state"))
        if any(request.vendor_bill for request in service_requests):
            raise UserError(_("All selected requests should be not has Vendor Bill"))
        for request in service_requests:
            invoice_line = (0, 0, {
                'name': f'{request.family_id.name}/{request.device_id.device_name}/{request.description}/{request.name}',
                'account_id': request.device_account_id.id,
                'analytic_account_id': request.branches_custom.branch.analytic_account_id.id,
                'quantity': request.requested_quantity,
                'price_unit': request.requested_service_amount,
            })
            line_ids.append(invoice_line)
        vendor_bill = self.env['account.move'].create({
            'move_type': 'in_invoice',
            'partner_id': service_producer_id.service_producer_id.id,
            # 'accountant_id': self.accountant_id.id,
            'invoice_line_ids': line_ids,
        })
        self.vendor_bill = vendor_bill

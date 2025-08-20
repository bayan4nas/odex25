from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ServiceSetting(models.Model):
    _name = 'benefits.service'
    _description = 'Service Settings'
    _order = 'name asc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Service Name',
        required=True,
        tracking=True
    )
    code = fields.Char(
        string='Service Code',
        required=True,
        tracking=True,
        help="Unique identifier for the service"
    )
    account_id = fields.Many2one(
        'account.account',
        string='Expense Account',
        domain=['|', ('user_type_id.name', '=', 'Expenses'), ('user_type_id.name', '=', 'المصروفات')]
    )
    accountant_id = fields.Many2one(
        'res.users',
        string='Responsible Accountant',
        domain=lambda self: [('groups_id', 'in', [self.env.ref('account.group_account_readonly').id,
                              self.env.ref('account.group_account_manager').id,
                              self.env.ref('account.group_account_invoice').id,
                              self.env.ref('account.group_account_user').id,])]
    )
    paths = fields.Many2one('beneficiary.path',
                            string='Path',
                            required=True,
                            tracking=True
                            )
    classification_id = fields.Many2one(
        'benefits.service.classification',
        string='Service Classification',
        required=True,
        tracking=True,

    )
    service_duration = fields.Integer('Service Duration')

    beneficiary_category = fields.Selection(
        [('detainee', 'Detainee'), ('detainee_family', 'Detainee Family'), ('released_family', 'Released Family')],
        string='Beneficiary Category')

    description = fields.Html(
        string='Service Description',
        sanitize=True,
        strip_style=False,
        help="Detailed description of the service"
    )
    attachment_ids = fields.One2many('service.attachment', 'attachment_id')
    provider_ids = fields.Many2many(
        'res.partner',
        string='Service Providers',
        domain=[('is_company', '=', True)],
        tracking=True,
        help="Organizations that provide this service"
    )

    output_ids = fields.Many2many(
        'benefits.output',
        string='Outputs',
        help="Expected outputs from this service"
    )

    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True
    )

    enable_disbursement_periodicity = fields.Boolean(
        string='Enable Disbursement Periodicity',
        help="Enable to set different disbursement periods based on need category",
        tracking=True
    )

    disbursement_periodicity_ids = fields.One2many(
        'benefits.service.disbursement.periodicity',
        'service_id',
        string='Disbursement Periodicity Settings',
        help="Configure different disbursement periods for different need categories"
    )

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Service code must be unique!'),
    ]

    # @api.onchange('path')
    # def _onchange_path(self):
    #     for rec in self:
    #         domain = []
    #         if rec.path:
    #             linked_classifications = self.env['benefits.service.classification'].search([
    #                 ('path_id', '=', rec.path.id)
    #             ]).mapped('classification_id').ids
    #             if linked_classifications:
    #                 domain.append(('id', 'in', linked_classifications))
    #
    #         return {'domain': {'classification_id': domain}}

    @api.constrains('disbursement_periodicity_ids')
    def _check_disbursement_periodicity(self):
        for service in self:
            if service.enable_disbursement_periodicity:
                categories = service.disbursement_periodicity_ids.mapped('category')
                if len(categories) != len(set(categories)):
                    raise ValidationError(_("Duplicate category found in disbursement periodicity settings."))
                if not categories:
                    raise ValidationError(_("At least one disbursement periodicity setting is required when enabled."))

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=100):
        args = args or []
        domain = ['|', ('name', operator, name), ('code', operator, name)]
        return self.search(domain + args, limit=limit).name_get()

    def name_get(self):
        return [(rec.id, f"[{rec.code}] {rec.name}" if rec.code else rec.name) for rec in self]

    def toggle_active(self):
        """ Override to prevent deactivation if linked to active records """
        return super().toggle_active()


class ServiceDisbursementPeriodicity(models.Model):
    _name = 'benefits.service.disbursement.periodicity'
    _description = 'Service Disbursement Periodicity Settings'
    _order = 'service_id, categories'

    service_id = fields.Many2one(
        'benefits.service',
        string='Service',
        required=True,
        ondelete='cascade'
    )

    categories = fields.Many2one('family.need.category',
                                 string='Category',
                                 required=True,
                                 help="Category of need for this disbursement period"
                                 )

    value = fields.Integer(
        string='Value',
        required=True,
        default=1
    )
    periodicity = fields.Selection([('month', 'Month'), ('Year', 'year')])
    months = fields.Integer(
        string='Months',
        required=True,
        help="Number of months between disbursements for this category",
        default=1
    )

    _sql_constraints = [
        ('unique_category_per_service', 'UNIQUE(service_id, categories)',
         'Each need category can only be defined once per service.'),
        ('positive_months', 'CHECK(months > 0)',
         'Months must be a positive number.')
    ]


class ServiceAttachment(models.Model):
    _name = 'service.attachment'
    _description = 'Service Attachment'

    attachment_id = fields.Many2one('benefits.service', 'attachment id')
    attach = fields.Binary('Attachment')
    attach_type = fields.Boolean('Attachment Type')
    attachment_name = fields.Char('Attachment Name')

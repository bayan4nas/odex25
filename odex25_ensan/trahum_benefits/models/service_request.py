# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class BenefitsServiceRequest(models.Model):
    _name = 'benefits.service.request'
    _description = 'Benefits Service Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # Request Information
    name = fields.Char(
        string='Request Number',
        readonly=True,
        copy=False,
        default=lambda self: _('New'),
        tracking=True
    )
    request_date = fields.Date(
        string='Request Date',
        required=True,
        default=fields.Date.context_today,
        tracking=True
    )
    requester_id = fields.Many2one(
        'family.member',
        string='Requester',
        required=True,
        tracking=True
    )
    request_source = fields.Selection(
        [
            ('website', 'Website'),
            ('phone', 'Phone Call'),
            ('whatsapp', 'WhatsApp'),
            ('branch', 'Branch Headquarters'),
            ('periodic', 'Periodic Requests')
        ],
        string='Request Source',
        required=True,
        tracking=True
    )

    # Family Information
    family_id = fields.Many2one(
        'grant.benefit',
        string='Family File',
        readonly=True,
        compute='_compute_family_info',
        store=True
    )
    family_file_number = fields.Char(
        string='Family File Number',
        readonly=True,
        compute='_compute_family_info',
        store=True
    )
    need_category = fields.Char(
        string='Need Category',
        readonly=True,
        compute='_compute_family_info',
        store=True
    )
    last_request_date = fields.Date(
        string='Last Request Date',
        readonly=True,
        compute='_compute_request_history'
    )
    service_count = fields.Integer(
        string='Service Count',
        readonly=True,
        compute='_compute_request_history'
    )
    family_member_count = fields.Integer(
        string='Family Members Count',
        readonly=True,
        compute='_compute_family_info',
        store=True
    )

    # Request Details
    request_type = fields.Selection(
        [
            ('service', 'Service'),
            ('complaint', 'Complaint'),
            ('suggestion', 'Suggestion')
        ],
        string='Request Type',
        required=True,
        tracking=True
    )
    classification_id = fields.Many2one(
        'benefits.service.classification',
        string='Service Classification',
        required=True,
        tracking=True
    )
    service_id = fields.Many2one(
        'benefits.service',
        string='Service',
        domain="[('classification_id', '=', classification_id)]",
        required=True,
        tracking=True
    )
    description = fields.Text(
        string='Description',
        tracking=True
    )

    # Outputs
    output_ids = fields.One2many(
        'benefits.service.request.output',
        'request_id',
        string='Outputs',
        tracking=True
    )

    # Approval Workflow
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('setup', 'Awaiting Setup Confirmation'),
            ('verification', 'Awaiting Verification Confirmation'),
            ('audit', 'Awaiting Audit'),
            ('approval', 'Awaiting Approval'),
            ('implementation', 'Awaiting Implementation'),
            ('done', 'Completed'),
            ('canceled', 'Canceled')
        ],
        string='Status',
        default='draft',
        tracking=True,
        group_expand='_expand_states'
    )

    cancel_reason = fields.Text(string="Cancellation Reason", tracking=True)
    return_reason = fields.Text(string="Return Reason", tracking=True)

    @api.depends('requester_id')
    def _compute_family_info(self):
        for record in self:
            if record.requester_id:
                family = self.env['grant.benefit'].search([
                    ('benefit_member_ids.member_id', '=', record.requester_id.id)
                ], limit=1)
                if family:
                    record.family_id = family.id
                    record.family_file_number = family.name
                    record.need_category = family.need_calculator if hasattr(family, 'need_calculator') else False
                    record.family_member_count = len(family.benefit_member_ids)
                else:
                    record.family_id = False
                    record.family_file_number = False
                    record.need_category = False
                    record.family_member_count = 0
            else:
                record.family_id = False
                record.family_file_number = False
                record.need_category = False
                record.family_member_count = 0

    def _compute_request_history(self):
        for record in self:
            if record.requester_id:
                requests = self.search([
                    ('requester_id', '=', record.requester_id.id),
                    ('id', '!=', record.id)
                ], order='request_date desc', limit=1)
                record.last_request_date = requests[0].request_date if requests else False
                record.service_count = self.search_count([
                    ('requester_id', '=', record.requester_id.id),
                    ('id', '!=', record.id)
                ])
            else:
                record.last_request_date = False
                record.service_count = 0

    def _expand_states(self, states, domain, order):
        return [key for key, val in type(self).state.selection]

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('benefits.service.request') or _('New')
        return super(BenefitsServiceRequest, self).create(vals)

    # Workflow Actions
    def action_submit(self):
        self.write({'state': 'setup'})

    def action_confirm_setup(self):
        self.write({'state': 'verification'})

    def action_confirm_verification(self):
        self.write({'state': 'audit'})

    def action_confirm_audit(self):
        self.write({'state': 'approval'})

    def action_confirm_approval(self):
        self.write({'state': 'implementation'})

    def action_complete(self):
        if any(output.state != 'executed' for output in self.output_ids):
            raise UserError(_("Cannot complete request. All outputs must be executed first."))
        self.write({'state': 'done'})

    def action_cancel(self):
        return {
            'name': _('Cancel Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'request.cancel.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_request_id': self.id},
        }

    def action_return(self):
        return {
            'name': _('Return Request'),
            'type': 'ir.actions.act_window',
            'res_model': 'request.return.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_request_id': self.id},
        }

    def action_draft(self):
        self.write({'state': 'draft'})

    @api.constrains('output_ids')
    def _check_outputs(self):
        for record in self:
            if record.state in ['implementation', 'done'] and not record.output_ids:
                raise ValidationError(_("Cannot move to implementation stage without outputs."))


class BenefitsServiceRequestOutput(models.Model):
    _name = 'benefits.service.request.output'
    _description = 'Service Request Output'
    _order = 'sequence, id'

    request_id = fields.Many2one(
        'benefits.service.request',
        string='Service Request',
        required=True,
        ondelete='cascade'
    )
    sequence = fields.Integer(string='Sequence', default=10)
    output_id = fields.Many2one(
        'benefits.output',
        string='Output',
        required=True
    )
    state = fields.Selection(
        [
            ('draft', 'Not Executed'),
            ('executed', 'Executed')
        ],
        string='Status',
        default='draft',
        readonly=True
    )
    notes = fields.Text(string='Notes')

    def action_confirm_execute(self):
        self.write({'state': 'executed'})


class ServiceRequest(models.Model):
    _inherit = 'service.request'

    branches_custom = fields.Many2one('branch.details', string="Branch", compute='get_branch_custom_id', store=True)

    @api.depends('benefit_type', 'family_id', 'member_id')
    def get_branch_custom_id(self):
        for rec in self:
            branch_id = False
            if rec.benefit_type == 'family' and rec.family_id:
                branch_id = rec.family_id.branch_details_id.id
            elif rec.benefit_type == 'member' and rec.member_id:
                fam = self.env['grant.benefit'].search(
                    [('benefit_member_ids.member_id', '=', rec.member_id.id)],
                    limit=1
                )
                branch_id = fam.branch_details_id.id if fam else False
            elif rec.benefit_type == 'detainee' and rec.detainee_file:
                branch_id = rec.detainee_file.branch_id.id

            rec.branches_custom = branch_id
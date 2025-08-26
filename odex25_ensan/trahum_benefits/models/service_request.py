# -*- coding: utf-8 -*-
from datetime import date

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

from odoo.exceptions import ValidationError
from datetime import date, timedelta, datetime

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
    service_path = fields.Many2one('beneficiary.path', 'Service Path', related='service_cats.paths')
    sub_service_path = fields.Many2one('benefits.service.classification', 'Sub Service Path',
                                       related='service_cats.classification_id')
    account_expense = fields.Many2one('account.account',related='service_cats.account_id' )

    family_need_class_id = fields.Many2one( 'family.need.category',related="family_id.family_need_class_id", string="Need Calculator", store=True,
                                       readonly=True)
    member_family_need_class_id = fields.Many2one( 'family.need.category',related="member_id.family_file_link_family_need_class_id", string="Need Calculator", store=True,
                                       readonly=True)
    requested_service_amount_before_tolerance = fields.Float(
        string='القيمة قبل خصم التحمل',
        readonly=True,
    )

    available_members = fields.Many2many(
        'family.member',
        compute='_compute_available_members',
        store=False
    )

    member_id = fields.Many2one(
        'family.member',
        string='Member',
        domain="[('id', 'in', available_members)]"
    )

    @api.depends('family_id', 'family_id.benefit_member_ids')
    def _compute_available_members(self):
        for record in self:
            if record.family_id and record.family_id.benefit_member_ids:
                member_ids = record.family_id.benefit_member_ids.mapped('member_id.id')
                record.available_members = [(6, 0, member_ids)]
            else:
                record.available_members = [(5, 0, 0)]

    @api.onchange('family_id')
    def _onchange_family_id(self):
        if self.family_id:
            if self.member_id:
                family_member_ids = self.family_id.benefit_member_ids.mapped('member_id.id')
                if self.member_id.id not in family_member_ids:
                    self.member_id = False
        else:
            self.member_id = False

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

    def _get_beneficiary_domain(self):
        """
        Helper method to get the domain for the beneficiary (family or member).
        This makes the rules applicable to any beneficiary type.
        """
        self.ensure_one()
        if self.benefit_type in ('family', 'detainee') and self.family_id:
            return [('family_id', '=', self.family_id.id)]
        elif self.benefit_type == 'member' and self.member_id:
            return [('member_id', '=', self.member_id.id)]
        return []

    def _get_period_domain(self, period, period_days=0):
        """
        Helper method to get the date domain based on the selected period.
        """
        today = date.today()
        domain = []
        if period == 'year':
            start_date = today.replace(month=1, day=1)
            end_date = today.replace(month=12, day=31)
            domain = [('date', '>=', start_date), ('date', '<=', end_date)]
        elif period == 'month':
            start_date = today.replace(day=1)
            next_month = (today.replace(day=28) + timedelta(days=4)).replace(day=1)
            end_date = next_month - timedelta(days=1)
            domain = [('date', '>=', start_date), ('date', '<=', end_date)]
        elif period == 'days' and period_days > 0:
            start_date = today - timedelta(days=period_days)
            domain = [('date', '>=', start_date), ('date', '<=', today)]
        return domain

    def _apply_rule(self, rule):
        """
        Applies a single rule to the service request.
        This function contains the core logic for each metric.
        """
        self.ensure_one()

        #
        # ---  (Validation Rules) ---
        #
        if rule.rule_type == 'validation':
            value_to_check = 0
            base_domain = self._get_beneficiary_domain()
            if not base_domain:
                return

            base_domain += [('id', '!=', self.id)]

            # 1.  (request_total)
            if rule.metric == 'request_total':
                value_to_check = self.requested_service_amount

            # 2.  (sum_amount_period)
            elif rule.metric == 'sum_amount_period':
                period_domain = self._get_period_domain(rule.period, rule.period_days)
                domain = base_domain + period_domain
                requests = self.env['service.request'].search(domain)
                total_amount = sum(requests.mapped('requested_service_amount'))
                value_to_check = total_amount + self.requested_service_amount

            # 3. (count_requests_period)
            elif rule.metric == 'count_requests_period':
                period_domain = self._get_period_domain(rule.period, rule.period_days)
                domain = base_domain + period_domain
                value_to_check = self.env['service.request'].search_count(domain)

            # 4.  (days_since_last_request)
            elif rule.metric == 'days_since_last_request':
                # last request
                last_request = self.env['service.request'].search(
                    base_domain, order='date desc', limit=1
                )
                if last_request:
                    days_diff = (datetime.now().date() - last_request.date.date()).days
                    value_to_check = days_diff
                else:
                    return

            # 5.  (family_members_count)
            elif rule.metric == 'family_members_count':
                if self.family_id and self.benefit_type == 'family':
                    value_to_check = self.family_id.benefit_member_count
                else:
                    return
            # 6.  (family_value)
            elif rule.metric == 'family_value':
                if self.family_id:
                    member = len(self.family_id.benefit_member_ids)
                    breadwinner = len(self.family_id.benefit_breadwinner_ids)
                    value_to_check = (member * rule.member_value) + (breadwinner * rule.breadwinner_value)
                    print(value_to_check)
                    if self.requested_service_amount > value_to_check:
                        message = rule.message or f"Rule Violation: {rule.name}"
                        if rule.severity == 'error':
                            raise ValidationError(message)

                        elif rule.severity == 'warning':
                            self.message_post(body=f"Warning: {message}")
                            return
                    else:
                        return

                else:
                    return
            elif rule.metric == 'tolerance_ratio' and rule.numeric_value:
                if not self.requested_service_amount_before_tolerance:
                    original_amount = self.requested_service_amount
                    tolerance_percentage = rule.numeric_value
                    adjusted_amount = self.requested_service_amount * tolerance_percentage

                    self.with_context(skip_rules_check=True).write({
                        'requested_service_amount_before_tolerance': original_amount,
                        'requested_service_amount': adjusted_amount
                    })

                    message =  f" '{rule.message}'"
                    self.message_post(body=message)

            # The `eval` function is used here for dynamic operator evaluation.
            # It's safe because the inputs (value, operator, threshold) are controlled within Odoo.
            condition_met = eval(f"{value_to_check} {rule.operator} {rule.threshold_value}")

            if not condition_met:
                message = rule.message or f"Rule Violation: {rule.name}"
                if rule.severity == 'error':
                    raise ValidationError(message)
                elif rule.severity == 'warning':
                    self.message_post(body=f"Warning: {message}")

        #
        # --- (Computation Rules) ---
        #
        # elif rule.rule_type == 'compute':
        #     if rule.metric == 'request_total' and rule.numeric_value:
        #         original_amount = self.requested_service_amount
        #         new_amount = original_amount * (rule.numeric_value / 100.0)
        #         self.write({'requested_service_amount': new_amount})
        #
        #         message = f"Applied rule '{rule.name}': Amount changed from {original_amount} to {new_amount}."
        #         self.message_post(body=message)

    def check_rules(self):
        """
        Main method to check all active rules for the selected service.
        """
        for rec in self:
            if not rec.service_cats:
                continue

            rules = rec.service_cats.rule_ids.filtered(lambda r: r.active).sorted('sequence')

            for rule in rules:
                rec._apply_rule(rule)
        return True

    @api.model
    def create(self, vals):
        rec = super().create(vals)
        rec.check_rules()
        return rec

    def write(self, vals):
        if self.env.context.get('skip_rules_check'):
            return super().write(vals)

        if 'requested_service_amount' in vals:
            vals['requested_service_amount_before_tolerance'] = 0

        res = super().write(vals)

        self.check_rules()

        return res
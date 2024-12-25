# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ProjectVariationOrder(models.Model):
    _name = "project.variation.order"
    _description = "Change Request"
    _order = 'name desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char("Name", default="/", tracking=True)
    request_date = fields.Date(
        string='Request Date',
        required=True,
        index=True,
        readonly=True,
        states={'draft': [('readonly', False)]},
        copy=False,
        default=fields.Date.context_today)
    description = fields.Text("Change Justifications", required=True)
    project_id = fields.Many2one(
        'project.project', string='Project', copy=False, tracking=True)
    currency_id = fields.Many2one(
        'res.currency', related="project_id.currency_id")
    company_id = fields.Many2one('res.company', string='Company', copy=False, tracking=True,
                                 default=lambda self: self.env.company)
    project_manager = fields.Many2one(
        'res.users', string='Project Manager', readonly=True, copy=False)
    project_owner = fields.Many2one(
        'res.users', string='Project Owner', copy=False)
    manager = fields.Boolean('Project Manager', tracking=True)
    new_project_manager = fields.Many2one(
        'res.users', string='New Project Manager', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'PM Approval'),
        ('approve', 'PMO Approval'),
        ('fin_approve', 'Financial Manager Approval'),
        ('owner_approve', 'Owner Approval'),
        ('implement', 'To implement'),
        ('done', 'Done'),
        ('refuse', 'Refused')], string='Status',
        copy=False, default='draft', required=True, tracking=True)
    # Time
    time = fields.Boolean('Project Schedule', tracking=True, readonly=True, states={
                          'draft': [('readonly', False)]})
    start = fields.Date(string='Start Date', readonly=False, copy=False)
    date = fields.Date(string='End Date', readonly=False, copy=False)
    new_date = fields.Date(string='New End Date', tracking=True)
    project_phase_ids = fields.Many2many(
        'project.phase', string="Project Phases", copy=False)
    project_task_ids = fields.Many2many(
        'project.task', string="Tasks", copy=False)
    # Budget
    budget = fields.Boolean('Project Budget', tracking=True, readonly=True, states={
                            'draft': [('readonly', False)]})
    total_invoiced_amount = fields.Float(
        'Currnt Project Budget', readonly=True)
    total_invoiced_payment = fields.Float(
        'Paid Amount', readonly=True, copy=False)
    residual_amount = fields.Float(
        'Residual Amount', readonly=True, copy=False)
    budget_amount = fields.Float(
        'New Project Budget', tracking=True, copy=False)
    # invoice_ids = fields.One2many('project.invoice', 'variation_order_id', "Invoice", copy=False)
    project_invoice_ids = fields.Many2many(
        'project.invoice', string="Invoice", copy=False)
    # scope
    scope = fields.Boolean('Project Scope', tracking=True, readonly=True, states={
                           'draft': [('readonly', False)]})
    project_scope = fields.Text(
        "Change Description", copy=False, tracking=True)
    mark_vo_as_sent = fields.Boolean("Mark as Sent")
    # todo start
    allowed_internal_user_ids = fields.Many2many('res.users', 'project_cr_allowed_internal_users_rel',
                                                 string="Allowed Internal Users", default=lambda self: self.env.user, domain=[('share', '=', False)])
    allowed_portal_user_ids = fields.Many2many('res.users', 'project_cr_allowed_portal_users_rel', string="Allowed Portal Users", domain=[('share', '=', True)])
    # todo end
    @api.onchange('project_id')
    def onchange_project_id(self):
        for rec in self:
            rec.project_phase_ids = False
            rec.project_invoice_ids = False
            rec.project_manager = False
            rec.start = False
            rec.date = False
            rec.total_invoiced_amount = 0.0
            rec.total_invoiced_payment = 0.0
            rec.residual_amount = 0.0
            if rec.project_id:
                rec.start = rec.project_id.date_start
                rec.date = rec.project_id.date
            if rec.project_id and rec.project_id.project_phase_ids:
                rec.project_phase_ids = rec.project_id.project_phase_ids.ids
            if rec.project_id and rec.project_id.user_id:
                rec.project_manager = rec.project_id.user_id.id

            if rec.project_id and rec.project_id.invoice_ids:
                rec.total_invoiced_amount = rec.project_id.total_invoiced_amount
                rec.total_invoiced_payment = rec.project_id.total_invoiced_payment
                rec.residual_amount = rec.project_id.residual_amount
                rec.project_invoice_ids = rec.project_id.invoice_ids.ids

    def action_view_previous(self):
        self.ensure_one()
        action_window = {
            "type": "ir.actions.act_window",
            "res_model": "project.variation.order",
            "name": "Previous Change Request",
            'view_type': 'form',
            'view_mode': 'tree,form',
            "context": {"create": False},
            "domain": [('project_id', '=', self.project_id.id)]
        }
        return action_window

    @api.model
    def _get_next_vo_code(self):
        next_sequence = " "
        sequence = self.env['ir.sequence'].search(
            [('code', '=', 'project.variation.order')])
        if sequence:
            next_sequence = sequence.get_next_char(sequence.number_next_actual)
        else:
            raise ValidationError(
                _("There is no sequence configured for VO in this company please contact your administrator to configure one."))
        return next_sequence

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code(
            'project.variation.order') or '/'
        res = super().create(vals)
        return res

    def unlink(self):
        for rec in self:
            if rec.state not in ['draft']:
                raise UserError(_('You cannot delete a confirmed VO.'))
        super(ProjectVariationOrder, self).unlink()

    def action_draft(self):
        for rec in self:
            if rec.state == 'implement' and rec.manager:
                rec.project_id.write({'user_id': rec.project_manager.id})
            if rec.state == 'implement' and rec.time:
                rec.project_id.write({'date': rec.date})

        self.write({'state': 'draft'})

    def action_confirm(self):
        self.write({'state': 'confirm'})

    def action_approve(self):
        self.write({'state': 'approve'})

    def action_approve_pom(self):
        for rec in self:
            if rec.budget:
                rec.write({'state': 'fin_approve'})
            else:
                rec.write({'state': 'owner_approve'})

    def action_approve_fin(self):
        self.write({'state': 'owner_approve'})

    def action_implement(self):
        for rec in self:
            if rec.project_owner.id != self.env.uid:
                raise UserError(
                    _('Only the project owner can approve the Change Request.'))
            if rec.manager:
                rec.project_id.write({'user_id': rec.new_project_manager.id})
            if rec.time:
                rec.project_id.write({'date': rec.new_date})
        self.write({'state': 'implement'})

    def action_done(self):
        self.write({'state': 'done'})

    def action_refuse(self):
        self.write({'state': 'refuse'})

    def _find_mail_template(self):
        self.ensure_one()
        template_id = False
        template_id = self.env['ir.model.data'].xmlid_to_res_id(
            'project_variation_order.mail_template_vo_confirm', raise_if_not_found=False)
        return template_id

    def action_vo_send(self):
        ''' Opens a wizard to compose an email, with relevant mail template loaded by default '''
        self.ensure_one()
        template_id = self._find_mail_template()
        lang = self.env.context.get('lang')
        template = self.env['mail.template'].browse(template_id)
        if template.lang:
            lang = template._render_lang(self.ids)[self.id]
        ctx = {
            'default_model': 'project.variation.order',
            'default_res_id': self.ids[0],
            'default_use_template': bool(template_id),
            'default_template_id': template_id,
            'default_composition_mode': 'comment',
            'mark_vo_as_sent': True,
            'proforma': self.env.context.get('proforma', False),
            'force_email': True,
            'model_description': self.with_context(lang=lang),
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        if self.env.context.get('mark_vo_as_sent'):
            self.with_context(tracking_disable=True).write(
                {'mark_vo_as_sent': True})
        return super(ProjectVariationOrder, self.with_context(mail_post_autofollow=True)).message_post(**kwargs)


class Project(models.Model):
    _inherit = "project.project"

    variation_order_ids = fields.One2many(
        'project.variation.order', 'project_id', string='Change Requests')
    variation_count = fields.Integer(
        compute="get_variation", string='Change Requests')

    def get_variation(self):
        for rec in self:
            rec.variation_count = len(rec.variation_order_ids)

    def get_attached_domain(self):
        return ['|','|','|','|',
            '&',('res_model', '=', 'project.project'),
            ('res_id', 'in', self.ids),
            '&',('res_model', '=', 'project.task'),
            ('res_id', 'in', self.task_ids.ids),
            '&',('res_model', '=', 'project.invoice'),
            ('res_id', 'in', self.invoice_ids.ids),
            '&',('res_model', '=', 'project.phase'),
            ('res_id', 'in', self.project_phase_ids.ids),
            '&',('res_model', '=', 'project.variation.order'),
            ('res_id', 'in', self.variation_order_ids.ids)
        ]

    def action_view_variation(self):
        self.ensure_one()
        action_window = {
            "type": "ir.actions.act_window",
            "res_model": "project.variation.order",
            "name": "Change Requests",
            'view_type': 'form',
            'view_mode': 'tree,form',
            "context": {"create": False},
            "domain": [('project_id', '=', self.id)]
        }
        return action_window

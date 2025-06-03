# -*- coding: utf-8 -*-
##############################################################################
#
#    Expert Co. Ltd.
#    Copyright (C) 2018 (<http://www.exp-sa.com/>).
#
##############################################################################


from odoo import api, fields, models, _
from odoo.exceptions import Warning, ValidationError


class BudgetConfirmation(models.Model):
    _name = 'budget.confirmation'
    _inherit = ['mail.thread']
    _description = 'Budget Confirmation'
    _order = "create_date desc"


    att_number = fields.Integer(
        string='Documents',
        compute='compute_att_number', store=False
    )
    attachment_count = fields.Integer(
        string='Documents',
        store=True
    )
    po_id = fields.Many2one('purchase.order')
    request_id = fields.Many2one('purchase.request')

    # @api.depends('po_id', 'ref', 'request_id')
    def compute_att_number(self):
        self.att_number =0
        print('attacj........')
        Attachment = self.env['ir.attachment']
        print('pre = ', self.request_id)
        for record in self:
            attachments = Attachment.search([
                '|',
                '&', ('res_model', '=', 'purchase.order'), ('res_id', '=', record.po_id.id),
                '&', ('res_model', '=', 'purchase.request'), ('res_id', '=', record.request_id.id),
            ])
            print('att= ', attachments)
            record.att_number = len(attachments)
            return len(attachments)

    def action_view_attachments(self):
        self.ensure_one()
        PurchaseRequest = self.env['purchase.request']
        matching_requests = PurchaseRequest.search([('name', '=', self.ref)])
        print('m = ',matching_requests)
        domain = []
        if self.po_id and self.request_id:

            domain = ['|',
                      '&', ('res_model', '=', 'purchase.order'), ('res_id', '=', self.po_id.id),
                      '&', ('res_model', '=', 'purchase.request'), ('res_id', '=', self.request_id.id)]
        elif self.po_id:
            domain = [('res_model', '=', 'purchase.order'), ('res_id', '=', self.po_id.id)]
        elif self.request_id or matching_requests:
            domain = [
                ('res_model', '=', 'purchase.request'),
                '|',  # OR operator
                ('res_id', 'in', matching_requests.ids),
                ('res_id', '=', self.request_id.id),
            ]
        else:
            domain = [('id', '=', 0)]
        self.att_number = self.compute_att_number()

        return {
            'type': 'ir.actions.act_window',
            'name': 'Related Attachments',
            'view_mode': 'tree,form',
            'res_model': 'ir.attachment',
            'domain': domain,
            'context': self.env.context,
        }
        print('in if')

    name = fields.Char(string='Name')

    date = fields.Date(string='Date', required=True)

    beneficiary_id = fields.Many2one(comodel_name='res.partner',
                                     required=False, string='Beneficiary')

    department_id = fields.Many2one(
        comodel_name='hr.department', string='Department')

    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Cost Center')

    type = fields.Selection(string='type', selection=[('purchase.order', 'Purchase Requisition'), ('purchase.request', 'Purchase Request')])

    ref = fields.Char(string='Reference')

    res_model = fields.Char(
        'Related Document Model Name')
    res_id = fields.Integer('Document ID')

    description = fields.Text(string='Description')

    total_amount = fields.Monetary(
        string='Amount',
        help="Total amount")

    state = fields.Selection(
        [('draft', 'Budget Officer '),
            ('bdgt_dep_mngr', 'Budget Department Manager'),
            ('confirmed', 'Budget Executive Director'),
            ('done', 'Done'),
            ('cancel', 'Cancel')],
        default='draft', string='Status', readonly=True, tracking=True)

    lines_ids = fields.One2many(comodel_name='budget.confirmation.line',
                                inverse_name='confirmation_id', string='Details', required=True)

    user_id = fields.Many2one(comodel_name='res.users', string='Request user',
                              required=False, default=lambda self: self.env.user)

    company_id = fields.Many2one(string='Company', comodel_name='res.company',
                                 default=lambda self: self.env.user.company_id)

    currency_id = fields.Many2one(
        'res.currency', string='Currency', required=True, readonly=True,
        states={'draft': [('readonly', False)]},
        default=lambda self: self.env.user.company_id.currency_id.id)

    exceed_budget = fields.Boolean(default=False, string='Allow Exceed Budget')
    reject_reason = fields.Char('Reject Reason')


    def reject(self):
        action_name = _('Specify Reject Reason')
        return {
            'type': 'ir.actions.act_window',
            'name': action_name,
            'res_model': 'reject.wizard',
            'view_type': 'form',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_origin': self.id, 'default_origin_name': self._name}
        }

    def confirm(self):
        """
        change state to confirm and check budget
        """
        for rec in self:
            for line in rec.lines_ids:
                line.sudo().check_budget()

        self.write({'state': 'confirmed'})

    def done(self):
        """
        change state to done and do specific action depend on operation type
        """
        self.write({'state': 'done'})


    def bdgt_dep_mngr(self):
        """
        change state to bdgt_dep_mngr and do specific action depend on operation type
        """
        self.write({'state': 'bdgt_dep_mngr'})

    def cancel(self):
        """
        change state to cancel
        """
        self.write({'state': 'cancel'})

    def to_draft(self):
        """
        change state to draft
        """
        self.write({'state': 'draft'})

    def unlink(self):
        """
        Delete budget confirmation, but they must be in cancel state.
        :return:
        """
        for rec in self:
            if rec.state != 'cancel':
                raise ValidationError(
                    _('You cannot delete a budget confirmation not in cancel state.'))
        return super(BudgetConfirmation, self).unlink()

    def copy(self):
        """
        prevent copy of budget confirmation.
        :return:
        """
        raise ValidationError(
            _('You cannot copy a budget confirmation .'))


class BudgetConfirmationLine(models.Model):
    _name = 'budget.confirmation.line'
    _description = 'Budget Confirmation details'

    confirmation_id = fields.Many2one(
        comodel_name='budget.confirmation',
        string='Budget Confirmation',
        ondelete='cascade', index=True
    )
    account_id = fields.Many2one(
        comodel_name='account.account',
        string='Account'
    )
    amount = fields.Float(
        string='Amount',
        digits='Product Price',
        help="Total amount in services request line"
    )
    remain = fields.Float(
        string='Remain',
        digits='Product Price',
        help="Remain in services budget for this cost center"
    )
    new_balance = fields.Float(
        string='New Balance',
        digits='Product Price',
        help="New Balance"
    )
    analytic_account_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string='Cost Center',
        required=True
    )
    date = fields.Date(
        related='confirmation_id.date',
        string='Date', store=True,
        readonly=True, related_sudo=False
    )
    state = fields.Selection(
        default='draft', string='Status',
        readonly=True, related='confirmation_id.state',
        store=True, related_sudo=False
    )
    budget_line_id = fields.Many2one(
        comodel_name='crossovered.budget.lines',
        string='Cost Center'
    )
    company_id = fields.Many2one(
        comodel_name='res.company', string='Company',
        related='confirmation_id.company_id', store=True,
        readonly=True, related_sudo=False
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        related='confirmation_id.currency_id',
        store=True, related_sudo=False
    )
    description = fields.Text(
        string='Description'
    )
    crossovered_budget_id = fields.Many2one(
        comodel_name='crossovered.budget',
        string='Budget',
        related='budget_line_id.crossovered_budget_id',
    )

    def check_budget(self):
        """
        check the available budget for given service and analytic amount
        in defined period of time
        :return:
        """
        self.ensure_one()
        if not self.account_id:
            raise ValidationError(_('''All lines should have accounts'''))
        analytic_account_id = self.analytic_account_id
        date = self.date
        date = fields.Date.from_string(date)
        budget_post = self.env['account.budget.post'].search([]).filtered(lambda x: self.account_id in x.account_ids)

        budget_lines = analytic_account_id.crossovered_budget_line.filtered(
            lambda x: x.general_budget_id in budget_post and
                      x.crossovered_budget_id.state == 'done' and
                      x.date_from <= date <= x.date_to)

        if budget_lines:
            remain = abs(budget_lines[0].remain)
            if remain >= self.confirmation_id.total_amount:
                return True

        name = self.account_id.name
        if not budget_lines:
            raise ValidationError(_('''No budget for ''') + name)
        if not self.confirmation_id.exceed_budget:
            raise ValidationError(_('''No enough budget for ''') + name)
        else:
            pass


class RejectWizard(models.TransientModel):
    _name = 'reject.wizard'

    origin = fields.Integer('')
    reject_reason = fields.Text(string='Reject Reason')
    origin_name = fields.Char('')

    def action_reject(self):
        origin_rec = self.env[self.origin_name].sudo().browse(self.origin)
        if dict(self._fields).get('reject_reason') is None:
            raise ValidationError(_('Sorry This object have no field named Selection Reason'))
        else:
            origin_rec.write({'reject_reason': self.reject_reason})
            if origin_rec.po_id:
                origin_rec.po_id.message_post(body=self.reject_reason)
            if origin_rec.invoice_id:
                origin_rec.invoice_id.message_post(body=self.reject_reason)
            return origin_rec.with_context({'reject_reason': self.reject_reason}).cancel()
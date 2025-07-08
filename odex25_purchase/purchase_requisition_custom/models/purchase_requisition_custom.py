# -*- coding: utf-8 -*-
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _


class PurchaseRequisitionLineCustom(models.Model):
    _inherit = 'purchase.requisition.line'

    product_id = fields.Many2one('product.product', string='Product', domain=lambda self: [('purchase_ok', '=', True)],
                                 required=True)
    # product_uom_id = fields.Many2one(related="product_id.uom_id")
    name = fields.Char(string="Description")
    department_id = fields.Many2one("hr.department")

    @api.model
    def create(self, vals):
        new_id = super(PurchaseRequisitionLineCustom, self).create(vals)
        return new_id


class PurchaseRequisitionCustom(models.Model):
    _inherit = 'purchase.requisition'

    # committee type
    attach_no = fields.Integer(compute='get_attachments')
    res_id = fields.Integer()
    res_model = fields.Char()

    committee_type_id = fields.Many2one('purchase.committee.type', string='Committee Type')
    state_blanket_order = fields.Selection(
        selection_add=[('purchase_manager', 'Purchase manager'), ('checked', 'Waiting Approval'),
                       ('committee', 'Committee'),
                       ('purchase_manager', 'Purchase manager'),
                       ('second_approve', 'Second Approval'),
                       ('legal_counsel', 'Legal Counsel'),
                       ('third_approve', 'Third Approval'),
                       ('accept', 'Accepted'),
                       ('open', 'Bid Selection'),
                       ('waiting', 'Waiting For Budget Confirmation'),
                       ('checked', 'Waiting Approval'),
                       ('done', 'Done'),
                       ('checked', 'Waiting Approval'),
                       ('approve', 'Approved'),
                       ('cancel', 'cancelled'),
                       ])
    state = fields.Selection([
        ('draft', 'Draft'),
        ('ongoing', 'Ongoing'),
        ('in_progress', 'Confirmed'),
        ('committee', 'Committee'),
        ('purchase_manager', 'Purchase manager'),
        ('second_approve', 'Second Approval'),
        ('legal_counsel', 'Legal Counsel'),
        ('third_approve', 'Third Approval'),
        ('accept', 'Accepted'),
        ('open', 'Bid Selection'),
        ('waiting', 'Waiting For Budget Confirmation'),
        ('checked', 'Waiting Approval'),
        ('done', 'Done'),
        ('checked', 'Waiting Approval'),
        ('approve', 'Approved'),
        ('cancel', 'cancelled')])
    type = fields.Selection([('project', 'Project'), ('operational', 'Operational')], default='operational')
    project_id = fields.Many2one('project.project', string='Project')
    sent_to_commitee = fields.Boolean('Is Sent to Commitee?', default=False)
    ordering_date = fields.Date(default=fields.Datetime.now)
    name = fields.Char(string='Agreement Reference', required=True, copy=False)
    department_id = fields.Many2one('hr.department')
    purpose = fields.Char()
    category_ids = fields.Many2many('product.category', string='Categories')
    account_analytic_id = fields.Many2one("account.analytic.account")
    purchase_commitee = fields.Boolean('Purchase Commitee?')
    committe_head = fields.Many2one('res.users', 'Committe Head')
    committe_members = fields.Many2many('res.users', string='Purchase Committee')
    min_approve = fields.Integer('No. of Selections')
    min_vote = fields.Integer('No. of Vots')
    actual_vote = fields.Integer('No. of Vots')
    request_id = fields.Many2one('purchase.request', 'Request Ref.', copy=False)
    purchase_cost = fields.Selection(
        [('department', 'Department'), ('default', 'Default Cost Center'), ('product_line', 'Product Line'),
         ('project', 'Project')], string='Purchase Cost', default='department')
    selected_purchase_id = fields.Many2one("purchase.order", compute="_compute_selected_purchase_order")
    is_purchase_budget = fields.Boolean(string="Is Purchase Budget", compute='_compute_purchase_budget')
    type_id_test = fields.Many2one('purchase.requisition.type', string="Agreement Type")
    Project_name = fields.Char(string='Project name')
    Chair_number = fields.Char(string='Chair number')
    agreement_data = fields.Date(string="Agreement data")
    city_name = fields.Char(string="City")
    days_count = fields.Char(string='days_count', compute='_compute_days')
    is_analytic = fields.Boolean("Use Analytic Account")
    change_state_line = fields.One2many('change.purchase.user.state', 'requisition_id')
    date_end = fields.Datetime(string='Agreement Deadline', tracking=True)
    check_request = fields.Boolean(compute='check_request_field')
    type_exclusive = fields.Selection(related='type_id.exclusive')

    def write(self, vals):
        res = super(PurchaseRequisitionCustom, self).write(vals)
        return res

    def get_attachments(self):
        # Check if multiple records are passed, and handle them in a loop
        if len(self) > 1:
            action = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
            action['domain'] = [
                ('res_model', '=', 'purchase.requisition'),
                ('res_id', 'in', self.ids),
            ]

            # Update attachment count for all records (if necessary)
            for record in self:
                related_ids = record.ids
                related_models = 'purchase.requisition'

                if record.res_id and record.res_model:
                    related_ids = record.ids + [record.res_id]
                    related_models = ['purchase.requisition', record.res_model]
                    action['domain'] = [
                        ('res_model', 'in', related_models),
                        ('res_id', 'in', related_ids),
                    ]

                # Context for creating new attachments for each record
                action['context'] = "{'default_res_model': '%s','default_res_id': %d}" % (record._name, record.id)

                # Update attachment count for each record
                record.attach_no = self.env['ir.attachment'].search_count([
                    ('res_model', 'in', related_models),
                    ('res_id', 'in', related_ids)
                ])

            return action

        # If only one record is passed, use the original logic
        self.ensure_one()

        action = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        action['domain'] = [
            ('res_model', '=', 'purchase.requisition'),
            ('res_id', 'in', self.ids),
        ]
        domain = [
            ('res_model', '=', 'purchase.requisition'),
            ('res_id', 'in', self.ids),
        ]
        related_ids = self.ids
        related_models = 'purchase.requisition'

        if self.res_id and self.res_model:
            related_ids = self.ids + [self.res_id]
            related_models = ['purchase.requisition', self.res_model]
            action['domain'] = [
                ('res_model', 'in', related_models),
                ('res_id', 'in', related_ids),
            ]
            domain = [
                ('res_model', 'in', related_models),
                ('res_id', 'in', related_ids),
            ]

        # Context for creating new attachments
        action['context'] = "{'default_res_model': '%s','default_res_id': %d}" % (self._name, self.id)

        # Update attachment count for smart button
        self.attach_no = self.env['ir.attachment'].search_count(domain)

        return action

    def action_purchase_orders_view(self):
        """Opens the purchase order list related to this requisition."""
        action = self.env.ref('purchase_requisition.action_purchase_requisition_list').sudo().read()[0]

        action['domain'] = [('requisition_id', '=', self.id)]

        # Modify context to pass required default values
        if self.state in ('approve', 'done'):
            action['context'] = dict(self.env.context,
                                     default_requisition_id=self.id,
                                     default_user_id=False,
                                     create=False
                                     )
        else:
            action['context'] = dict(self.env.context,
                                     default_requisition_id=self.id,
                                     default_user_id=False,
                                     create=True
                                     )
        return action

    def check_request_field(self):
        for rec in self:
            if rec.request_id:
                rec.check_request = True
            else:
                rec.check_request = False

    # agreement_name = fields.Char()
    # agreement_number = fields.Char()
    # agreement_date = fields.Date()
    # city = fields.Char()

    @api.onchange('purchase_cost')
    def _onchange_purchase_cost(self):
        if self.purchase_cost:
            if self.purchase_cost == 'project':
                self.type = 'project'
            else:
                self.type = 'operational'

    @api.onchange('type', 'project_id')
    def _onchange_project_id(self):
        if self.type != 'project':
            self.project_id = False

    def copy(self, default=None):
        data = super(PurchaseRequisitionCustom, self).copy(default)
        data.sent_to_commitee = False
        data.state = 'draft'
        return data

    @api.onchange('purchase_cost', 'line_ids', 'department_id')
    def on_project_type_department(self):
        for line in self.line_ids:
            if self.purchase_cost == 'project' and self.department_id:
                line.department_id = self.department_id

    @api.onchange('department_id', 'line_ids')
    def change_department(self):
        for line in self.line_ids:
            if self.purchase_cost in ['project', 'department'] and self.department_id:
                line.department_id = self.department_id

    def _compute_purchase_budget(self):
        purchase_budget = self.env.company.purchase_budget
        for rec in self:
            if purchase_budget:
                rec.is_purchase_budget = True
            else:
                rec.is_purchase_budget = False

    def action_skip_purchase_budget(self):
        """ Skip purchase budget"""
        purchase_orders = self.env['purchase.order'].search([('requisition_id', '=', self.id), ])
        for po_id in purchase_orders:
            # Deal with double validation process
            valid_amount = self.env.user.company_id.currency_id.compute(po_id.company_id.po_double_validation_amount,
                                                                        po_id.currency_id)
            if po_id.company_id.po_double_validation == 'one_step' or (
                    po_id.company_id.po_double_validation == 'two_step' and po_id.amount_total > valid_amount):
                po_id.write({'state': 'to approve'})
                self.write({'state': 'checked'})
            else:
                if po_id.email_to_vendor:
                    po_id.write({'state': 'sent'})
                else:
                    po_id.write({'state': 'draft'})
                po_id.write({'send_to_budget': False})
                self.write({'state': 'approve'})

    def _compute_days(self):
        self.days_count = _("Unknown")
        for rec in self:
            if rec.schedule_date and rec.ordering_date:
                schedule_date = fields.Date.from_string(rec.schedule_date)
                ordering_date = fields.Date.from_string(rec.ordering_date)
                diff_time = (schedule_date - ordering_date).days
                rec.days_count = diff_time

    def _compute_selected_purchase_order(self):
        for pr in self:
            if len(pr.purchase_ids) > 0:
                orders = pr.purchase_ids.filtered(lambda po: po.state in ['purchase', 'sign', 'done'])
                if len(orders) > 0:
                    pr.selected_purchase_id = orders[0]

    @api.constrains('min_approve')
    def min_approve_validation(self):
        if self.purchase_commitee and self.min_approve == 0:
            raise ValidationError(_("No. of Selections cannot be Zero"))

    @api.constrains('min_approve', 'min_vote')
    def check_min_vote_and_approve(self):
        if self.min_approve > len(self.committe_members):
            raise UserError(
                _("Minimum approves cannot be greater than members count = " + str(len(self.committe_members))))
        elif self.min_vote > len(self.committe_members):
            raise UserError(
                _("Minimum votes cannot be greater than members count = " + str(len(self.committe_members))))

    @api.model
    def get_seq_to_view(self):
        sequence = self.env['ir.sequence'].search([('code', '=', self._name)])
        return sequence.sequence.number_next_actual

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('purchase.requisition.purchase.seq') or '/'
        return super(PurchaseRequisitionCustom, self).create(vals)

    def action_quotation(self):
        """
            this function is to create new purchase order from the purchase agreement
            when pressing Quotation button in the workflow
        """
        # "default_state": 'wait',
        return {
            'name': "Request for Quotation",
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'form,tree',
            'domain': [('requisition_id', '=', self.id)],
            'context': {
                "default_requisition_id": self.id,
                "default_department_name": self.department_id.id,
                "default_category_ids": self.category_ids.ids,
                "default_purpose": self.purpose,
                "default_send_to_budget": True,
                "default_res_id": self.id,
                "default_res_model": 'purchase.requisition',
                "default_request_id": self.request_id.id if self.request_id else False},
        }

    def action_in_progress(self):
        """
            This Function validate the product quantity
        """
        super(PurchaseRequisitionCustom, self).action_in_progress()
        for rec in self.line_ids:
            if rec.product_qty <= 0:
                raise ValidationError(_("Product Quantity Can't Be Zero or less"))
        if self.purchase_commitee and len(self.committe_members) == 0:
            raise ValidationError(_("Please add Committe Members"))

    def action_approve(self):
        purchase_orders = self.env['purchase.order'].search(
            [('requisition_id', '=', self.id), ('state', '=', 'to approve')])
        po_order_approval = self.env.company.po_double_validation == 'two_step'
        for po_id in purchase_orders:
            # Deal with double validation process for first approve
            valid_amount = self.env.user.company_id.currency_id.compute(po_id.company_id.po_double_validation_amount,
                                                                        po_id.currency_id)
            if po_order_approval:

                if po_id.amount_total > valid_amount:
                    po_id.write({'state': 'to approve'})
                    self.write({'state': 'second_approve'})
                else:
                    # if po_id.email_to_vendor:
                    #     po_id.write({'state': 'sent'})
                    # else:
                    po_id.write({'state': 'draft'})
                    po_id.write({'send_to_budget': False})
                    self.write({'state': 'approve'})
            else:
                # if po_id.email_to_vendor:
                #     po_id.write({'state': 'sent'})
                # else:
                po_id.write({'state': 'draft'})
                po_id.write({'send_to_budget': False})
                self.write({'state': 'approve'})

    def second_approval(self):
        purchase_orders = self.env['purchase.order'].search([('requisition_id', '=', self.id)])
        po_order_approval = self.env.company.po_double_validation == 'two_step'
        for po_id in purchase_orders:
            # Deal with double validation process for second_approve
            valid_amount = self.env.user.company_id.currency_id.compute(po_id.company_id.second_approve,
                                                                        po_id.currency_id)
            if po_order_approval:
                if po_id.amount_total > valid_amount:
                    po_id.write({'state': 'to approve'})
                    self.write({'state': 'third_approve'})
                else:
                    if po_id.email_to_vendor:
                        po_id.write({'state': 'sent'})
                    else:
                        po_id.write({'state': 'draft'})
                    po_id.write({'send_to_budget': False})
                    self.write({'state': 'approve'})
            else:
                if po_id.email_to_vendor:
                    po_id.write({'state': 'sent'})
                else:
                    po_id.write({'state': 'draft'})

                po_id.write({'send_to_budget': False})
                self.write({'state': 'approve'})

    def third_approve(self):
        purchase_orders = self.env['purchase.order'].search([('requisition_id', '=', self.id)])
        for po_id in purchase_orders:
            if po_id.email_to_vendor:
                po_id.write({'state': 'sent'})
            else:
                po_id.write({'state': 'draft'})
            po_id.write({'send_to_budget': False})
            self.write({'state': 'approve'})

    def set_line_account_and_dept(self, line):
        department_id = self.department_id
        analytic_account = False
        if not line.account_analytic_id:
            if not self.is_analytic:
                analytic_account = self.department_id.analytic_account_id
            if not line.department_id:
                line.update({'department_id': department_id.id or False})
            line.update({'account_analytic_id': analytic_account.id or False})

    def action_budget(self):
        """
            This function create budget confirmation and check if the RFQ created
            and change the status of the document to the waiting
        """
        amount = 0
        if self.order_count == 0:
            raise ValidationError(_("Please create RFQ first"))
        # Find all RFQs as sign
        purchase_orders = self.env['purchase.order'].search([('requisition_id', '=', self.id), ('state', '=', 'sign')])
        if len(purchase_orders) == 0:
            raise ValidationError(_("Please Sign your RFQs first"))

        if not self.purchase_cost:
            raise ValidationError(_("No purchase cost for this agreement"))

        budget_confirmation_obj = self.env['budget.confirmation']
        date = fields.Date.from_string(self.ordering_date)
        for order in purchase_orders:
            move_lines = []
            for rec in order.order_line:
                analytic_account = rec.account_analytic_id

                if not analytic_account:
                    raise ValidationError(
                        _("Please put cost center to the product line") + ': {}'.format(rec.product_id.name))

                if not (
                        rec.product_id.property_account_expense_id.id and rec.product_id.property_account_expense_id.id or rec.product_id.categ_id.property_account_expense_categ_id.id):
                    raise ValidationError(_("This product has no expense account") + ': {}'.format(rec.product_id.name))

                try:
                    budget_lines = analytic_account.crossovered_budget_line.filtered(
                        lambda x:
                        x.crossovered_budget_id.state == 'done' and
                        fields.Date.from_string(x.date_from) <= date <= fields.Date.from_string(x.date_to))
                except Exception as e:
                    budget_lines = None
                if budget_lines:
                    budget_line_id = budget_lines[0].id
                    remain = abs(budget_lines[0].remain)
                    amount = amount + rec.price_unit
                    new_balance = remain - rec.price_unit
                    move_lines.append((0, 0, {
                        'amount': rec.price_subtotal,
                        'analytic_account_id': analytic_account.id,
                        'description': rec.product_id.name,
                        'budget_line_id': budget_line_id,
                        'remain': remain,
                        'new_balance': new_balance,
                        'account_id': rec.product_id.property_account_expense_id.id and rec.product_id.property_account_expense_id.id or rec.product_id.categ_id.property_account_expense_categ_id.id
                    }))

                else:
                    raise ValidationError(
                        _(''' No budget for this service ''') + ': {} - {}'.format(rec.product_id.name,
                                                                                   analytic_account.name))

            data = {
                'name': self.name,
                'date': self.ordering_date,
                'beneficiary_id': order.partner_id.id,
                'department_id': self.department_id.id,
                'type': 'purchase.order',
                'ref': self.name,
                'description': self.purpose,
                'total_amount': order.amount_untaxed,
                'lines_ids': move_lines,
                'po_id': order.id,
            }
            budget_id = budget_confirmation_obj.create(data)
            # Order to wait
            order.write({'state': 'waiting'})
            # Send Notifications
            subject = _('New Purchase Order')
            message = _(
                "New Budget Confirmation Has Been Created for Purchase Order %s to Beneficiary %s in total %s" % (
                    budget_id.name, budget_id.beneficiary_id.name, budget_id.total_amount))
            group = 'purchase.group_purchase_manager'
            author_id = self.env.user.partner_id.id or None
            self.env.user.partner_id.send_notification_message(subject=subject, body=message, author_id=author_id,
                                                               group=group)

        self.write({'state': 'waiting'})

    def to_committee(self):
        orders = self.env['purchase.order'].search([('requisition_id', '=', self.id)])
        if not orders:
            raise ValidationError(_("Enter Quotations First!"))

        # Send Notifications
        smart_link_agreement = '<a href="#" data-oe-id="{}" data-oe-model="purchase.requisition">{}#{}</a>'.format(
            self.id, self.name, self.id)
        for po in orders:
            smart_link_po = '<a href="#" data-oe-id="{}" data-oe-model="purchase.order">{}#{}</a>'.format(po.id,
                                                                                                          po.name,
                                                                                                          po.id)
            subject = _('New Purchase Order') + " - {}".format(po.name)
            message = _("This is Purchase Agreements, see here") + " {} .".format(
                smart_link_agreement) + "To evaluate this Purchase Order, please click here" + " {} .".format(
                smart_link_po)
            author_id = self.env.user.partner_id.id or None
            for member in self.committe_members:
                member.partner_id.send_notification_message(subject=subject, body=message, author_id=author_id)
        self.write({'state': 'committee', 'sent_to_commitee': True})

    def action_accept(self):
        if self.purchase_cost == 'project':
            if not self.project_id.analytic_account_id:
                raise ValidationError(_("No analytic account for the project"))
        for line in self.line_ids:
            self.set_line_account_and_dept(line)
        self.write({'state': 'accept'})

    def action_done(self):
        self.write({'state': 'done'})

    @api.onchange('committe_head')
    def on_change_com_head(self):
        if self.committe_head and not self.committee_type_id:
            self.committe_members = [self.committe_head.id]
        if not self.committe_head:
            self.committe_members = False

    def unlink(self):
        for rec in self:
            if rec.state not in ('draft'):
                raise ValidationError(_('Sorry! You Cannot Delete not Draft Document .'))
        return super(PurchaseRequisitionCustom, self).unlink()

    @api.onchange('committee_type_id')
    def onchange_committee_type_id(self):
        member_ids = self.committee_type_id.committe_members + self.committee_type_id.committe_head
        head = self.committee_type_id.committe_head
        self.committe_members = [(6, 0, member_ids.ids)]
        self.committe_head = head.id

    @api.constrains('committe_members')
    def check_member_committe_members(self):
        member_ids = self.committee_type_id.committe_members + self.committee_type_id.committe_head
        member_ids = member_ids.mapped('id')
        if self.purchase_commitee and len(self.committe_members) <= 0:
            raise ValidationError(_('Sorry, No Committee members'))
        if self.purchase_commitee and self.committee_type_id and len(self.committe_members) > len(member_ids):
            raise ValidationError(_('Committee members does not match in numbers'))
        if self.purchase_commitee and self.committee_type_id:
            for rec in self.committe_members:
                if rec.id not in member_ids:
                    raise ValidationError(_('This member is not belong to this committee:') + ' {} '.format(rec.name))


class StockPickingCustom(models.Model):
    _inherit = "stock.picking"

    @api.model
    def create(self, vals):
        defaults = self.default_get(['name', 'picking_type_id'])
        if vals.get('name', '/') == '/' and defaults.get('name', '/') == '/' and vals.get('picking_type_id',
                                                                                          defaults.get(
                                                                                              'picking_type_id')):
            vals['name'] = self.env['stock.picking.type'].browse(
                vals.get('picking_type_id', defaults.get('picking_type_id'))).sequence_id.next_by_id()
        # TDE FIXME: what ?
        # As the on_change in one2many list is WIP, we will overwrite the locations on the stock moves here
        # As it is a create the format will be a list of (0, 0, dict)
        if vals.get('name') == 'mosabtest':
            vals['name'] = self.env['stock.picking.type'].browse(
                vals.get('picking_type_id', defaults.get('picking_type_id'))).sequence_id.next_by_id()
        if vals.get('move_lines') and vals.get('location_id') and vals.get('location_dest_id'):
            for move in vals['move_lines']:
                if len(move) == 3 and move[0] == 0:
                    move[2]['location_id'] = vals['location_id']
                    move[2]['location_dest_id'] = vals['location_dest_id']
        res = super(StockPickingCustom, self).create(vals)
        res._autoconfirm_picking()
        return res


class CommitteeTypes(models.Model):
    _name = 'purchase.committee.type'

    name = fields.Char('Name')
    committe_members = fields.Many2many('res.users', string='Committee Members')
    committe_head = fields.Many2one('res.users', string='Committee Head')
    type_cat = fields.Many2many('product.category', string='Product Category')

    @api.model
    def create(self, vals):
        res = super(CommitteeTypes, self).create(vals)
        if res.committe_head.id not in res.committe_members.ids:
            res.committe_members = [(4, res.committe_head.id)]
        return res

    def write(self, vals):
        current_head = self.committe_head.id
        if 'committe_head' in vals and current_head in self.committe_members.ids:
            vals['committe_members'] = [(3, current_head), (4, vals['committe_head'])]
        return super(CommitteeTypes, self).write(vals)


class CommitteMembers(models.Model):
    _name = "committe.member"
    _description = "committe.member"

    po_id = fields.Many2one('purchase.order')
    req_id = fields.Many2one('purchase.request')
    user_id = fields.Many2one('res.users', "Member Name")
    selection_reason = fields.Char("Selection Reason")
    select = fields.Boolean(string="Select")
    refusing_reason = fields.Char("Refusing Reason")


class SelectReason(models.TransientModel):
    _name = "select.reason"
    _description = "select.reason"

    select_reason = fields.Text("select reason")
    order_id = fields.Integer("order id")

    def action_select(self):
        self.env['committe.member'].create({
            'po_id': self.order_id,
            'user_id': self.env.user.id,
            'selection_reason': self.select_reason,
            'select': True})
        order_id = self.env['purchase.order'].browse(self.order_id)
        order_id.select = True


class RefuseReason(models.TransientModel):
    _name = "refuse.reason"
    _description = "refuse.reason"

    refuse_reason = fields.Text("refuse reason")
    order_id = fields.Integer("order id")
    request_id = fields.Integer("Request id")

    def action_refuse(self):
        if self.order_id:
            order_id = self.env['purchase.order'].browse(self.order_id)
            order_id.select = True
            self.env['committe.member'].create({
                'po_id': self.order_id,
                'user_id': self.env.user.id,
                'refusing_reason': self.refuse_reason,
                'select': True})
        elif self.request_id:
            request_id = self.env['purchase.request'].search([('id', '=', self.request_id)])
            request_id.select = True
            self.env['committe.member'].create({
                'req_id': self.request_id,
                'user_id': self.env.user.id,
                'refusing_reason': self.refuse_reason,
                'select': True})
            body = _(
                "Purchase Request %s is Rejected By : %s  With Reject Reason : %s" % (
                    str(request_id.name), str(self.env.user.name), str(self.refuse_reason)))

            # Send Notifications
            subject = _('Reject Purchase Request')
            author_id = self.env.user.partner_id.id or None
            self.create_uid.partner_id.send_notification_message(subject=subject, body=body, author_id=author_id)
            request_id.message_post(body=body)
            request_id.write({'state': 'refuse'})


class RejectWizard(models.TransientModel):
    _name = 'reject.wizard'
    _description = 'reject.wizard'

    origin = fields.Integer('')
    reject_reason = fields.Text(string='Reject Reson')
    origin_name = fields.Char('')

    def action_reject(self):
        origin_rec = self.env[self.origin_name].sudo().browse(self.origin)
        if dict(self._fields).get('reject_reason') == None:
            raise ValidationError(_('Sorry This object have no field named Selection Reasoon'))
        else:
            return origin_rec.with_context({'reject_reason': self.reject_reason}).cancel()


class ChangePurchaseUserState(models.Model):
    _name = 'change.purchase.user.state'

    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'Confirmed'),
        ('committee', 'Committee'),
        ('purchase_manager', 'Purchase manager'),
        ('second_approve', 'Second Approval'),
        ('legal_counsel', 'Legal Counsel'),
        ('third_approve', 'Third Approval'),
        ('finance approve', 'Financial Approval'),
        ('cs approve', 'Common Services Approval'),
        ('general supervisor', 'General Supervisor Approval'),
        ('accept', 'Accepted'),
        ('open', 'Bid Selection'),
        ('waiting', 'Waiting For Budget Confirmation'),
        ('checked', 'Waiting Approval'),
        ('done', 'Done'),
        ('quality', 'Quality'),
        ('user_approve', 'User Approve'),
        ('refuse', 'Refused'),
        ('approve', 'Approved'),
        ('cancel', 'cancelled'),
    ],
    )
    requisition_id = fields.Many2one('purchase.requisition', "Requisition")

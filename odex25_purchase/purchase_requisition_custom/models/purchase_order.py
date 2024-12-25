from lxml import etree
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _
from odoo.tools.float_utils import float_is_zero
from dateutil.relativedelta import relativedelta

class AccountMove(models.Model):
    _inherit = 'account.move'

    purpose = fields.Char()

    @api.onchange('purchase_vendor_bill_id', 'purchase_id')
    def _onchange_purchase_auto_complete(self):
        super()._onchange_purchase_auto_complete()
        purchase_order_id = self.purchase_vendor_bill_id.purchase_order_id or self.purchase_id
        if purchase_order_id:
            self.purpose = purchase_order_id.purpose
        else:
            self.purpose = ''

    @api.model_create_multi
    def create(self, vals_list):
        moves = super(AccountMove, self).create(vals_list)
        for move in moves:
            if move.purchase_id:
                move.purpose = move.purchase_id.purpose
        return moves

    def write(self, vals):
        if vals.get('purchase_id'):
            po = self.env['purchase.order'].browse(vals['purchase_id'])
            vals['purpose'] = po.purpose
        super(AccountMove, self).write(vals)

class PurchaseOrderCustom(models.Model):
    _inherit = "purchase.order"

    billed_amount = fields.Float(store=True, compute='_compute_amount')
    remaining_amount = fields.Float(store=True, compute='_compute_amount')

    def read(self, records):
        return super(PurchaseOrderCustom, self.sudo()).read(records)

    @api.depends('invoice_ids','invoice_count')
    def _compute_amount(self):
        for order in self:
            billed_amount = 0.0
            for invoice in order.invoice_ids:
                billed_amount += invoice.amount_total

            currency = order.currency_id or order.partner_id.property_purchase_currency_id or \
                self.env.company.currency_id
            order.update({
                'billed_amount': currency.round(billed_amount),
                'remaining_amount': order.amount_total - billed_amount,
            })

    def copy(self, default=None):
        data = super(PurchaseOrderCustom, self).copy(default)
        data.email_to_vendor = False
        purchase_budget = self.env.company.purchase_budget
        if purchase_budget:
            data.is_purchase_budget = False
            data.state = 'wait'
        else:
            data.state = 'draft'

        return data
    attach_no = fields.Integer(compute='get_attachments')
    res_id = fields.Integer()
    res_model = fields.Char()
    
    state = fields.Selection([
        ('wait', 'Waiting To Be Signed'),
        ('unsign', 'UnSign'),
        ('sign', 'Sign'),
        ('waiting', 'Waiting For Budget Confirmation'),
        ('draft', 'RFQ'),
        ('sent', 'RFQ Sent'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
        ('budget_rejected', 'Rejected By Budget'),
        ('wait_for_send', 'Waiting For Send to Budget')], default='wait')
    department_id = fields.Many2one('hr.department')
    purpose = fields.Char()
    category_ids = fields.Many2many('product.category', string='Categories')
    committe_members = fields.One2many('committe.member', inverse_name='po_id')
    no_of_approve = fields.Integer("No. of Votes", compute="_compute_no_approve")
    request_id = fields.Many2one('purchase.request', 'Request Ref.')
    employee_id = fields.Many2one('hr.employee', related="request_id.employee_id")
    purchase_cost = fields.Selection(
        [('department', 'Department'), ('default', 'Default Cost Center'), ('product_line', 'Product Line'),
         ('project', 'Project')],
        string='Purchase Cost')
    state_of_delivery = fields.Char(string='Delivery State', compute="_compute_delviery_order")
    select = fields.Boolean(string="Select")
    auto_notification = fields.Boolean()
    responsible_id = fields.Many2one('res.users')
    notify_before = fields.Integer()
    start_date = fields.Date()
    end_date = fields.Date()
    cron_end_date = fields.Date(compute="get_cron_end_date", store=True)
    contract_name = fields.Char(string='Contract Name')
    period_type = fields.Selection(
        selection=[('day', 'Day(s)'), ('week', 'Week(s)'), ('month', 'Month(s)'), ('year', 'Year(s)')])
    type = fields.Selection(selection=[('ordinary', 'Ordinary'), ('contract', 'Contract'), ], default='ordinary',
                            string='Type')
    email_to_vendor = fields.Boolean('Email Sent to Vendor?', default=False)
    send_to_budget = fields.Boolean('Sent to Budget?', default=False)
    project_id = fields.Many2one('project.project', string='Project', compute="_get_project_data", store=True)
    is_purchase_budget = fields.Boolean(string="Is Purchase Budget", compute='_compute_budget')
    confirmation_ids = fields.One2many('budget.confirmation', 'po_id')
    recommendation_order = fields.Boolean(string='Recommend')
    parent_state = fields.Char(compute="_compute_parent_state", help="State of the parent purchase.requisition",
                               compute_sudo=True)
    purchase_commitee = fields.Boolean('Purchase Commitee?', compute="_compute_parent_state", compute_sudo=True)
    budget_amount = fields.Float(string="Approved Budget")
    is_signed = fields.Boolean()
    budget_id = fields.Many2one('crossovered.budget')
    already_voted = fields.Boolean(compute="_compute_already_voted")
    def get_attachments(self):
        # Check if multiple records are passed, and handle them in a loop
        if len(self) > 1:
            action = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
            action['domain'] = [
                ('res_model', '=', 'purchase.order'),
                ('res_id', 'in', self.ids),
            ]

            # Update attachment count for all records (if necessary)
            for record in self:
                related_ids = record.ids
                related_models = 'purchase.order'

                if record.res_id and record.res_model:
                    related_ids = record.ids + [record.res_id]
                    related_models = ['purchase.order', record.res_model]
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
            ('res_model', '=', 'purchase.order'),
            ('res_id', 'in', self.ids),
        ]
        domain = [
            ('res_model', '=', 'purchase.order'),
            ('res_id', 'in', self.ids),
        ]
        related_ids = self.ids
        related_models = 'purchase.order'

        if self.res_id and self.res_model:
            related_ids = self.ids + [self.res_id]
            related_models = ['purchase.order', self.res_model]
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


    def _prepare_invoice(self):
        res = super(PurchaseOrderCustom, self)._prepare_invoice()
        res.update({'purchase_id': self.id, 'res_id': self.id,'res_model': 'purchase.order'})
        return res

    @api.onchange('type')
    def auto_type_change(self):
        if self.type != 'contract':
            self.auto_notification = False
            self.responsible_id = False
            self.notify_before = 0
            self.start_date = None
            self.end_date = None
            self.contract_name = ''
            self.period_type = ''

            return {}

    @api.constrains('end_date', 'start_date', 'auto_notification')
    def start_notify_constrain(self):
        for rec in self:
            if rec.start_date and rec.end_date:
                if rec.start_date >= rec.end_date:
                    raise ValidationError(_("Start Date Should Be Less Than End Date"))

                if rec.auto_notification and rec.notify_before < 1:
                    raise ValidationError(_("Notify Before End Should Be Greater Than Zero"))

    @api.depends('end_date', 'notify_before', 'period_type')
    def get_cron_end_date(self):
        for rec in self:
            if rec.end_date and rec.period_type:
                end = fields.Datetime.from_string(rec.end_date)
                type = self.period_type
                date_to = False
                if rec.period_type == 'day':
                    date_to = (end + relativedelta(days=-rec.notify_before))
                elif rec.period_type == 'month':
                    date_to = (end + relativedelta(months=-rec.notify_before))
                elif rec.period_type == 'week':
                    date_to = (end + relativedelta(weeks=-rec.notify_before))
                elif rec.period_type == 'year':
                    date_to = (end + relativedelta(years=-rec.notify_before))
                rec.cron_end_date = date_to

    @api.model
    def cron_po_auto_notify(self):
        date = fields.Date.today()
        records = self.env['purchase.order'].sudo().search(
            [('state', 'not in', ['cancel', 'done']), ('cron_end_date', '<=', str(date)),
             ('auto_notification', '=', True)])
        for rec in records:
            template = self.env.ref('purchase_requisition_custom.auto_po_notify')
            template.send_mail(rec.id, force_send=True)

    def open_convert_po_contract(self):
        context = dict(self.env.context or {})
        context['default_purchase_id'] = self.id
        context['default_contract_name'] = self.contract_name
        context['default_responsible_id'] = self.responsible_id.id
        context['default_start_date'] = self.start_date
        context['default_end_date'] = self.end_date
        context['default_auto_notification'] = self.auto_notification
        context['purchase_id'] = self.id

        view = self.env.ref('purchase_requisition_custom.convert_to_contract_po_wizard')
        wiz = self.env['convert.po.contract.wizard']
        return {
            'name': _('Purchase To Contract'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'convert.po.contract.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': wiz.id,
            'context': context,
        }

    # End features on PO (related the cotract features)

    @api.depends('requisition_id')
    def _compute_parent_state(self):
        """ I use this function to compute state of requisition_id ,
         cuse we need it in domain to make some buttons visible or not, also purchase_commitee"""
        self.parent_state = False
        self.purchase_commitee = False
        for record in self.filtered('requisition_id'):
            record.parent_state = record.requisition_id.state
            record.purchase_commitee = record.requisition_id.purchase_commitee

    @api.constrains('recommendation_order')
    def check_recommendation_order(self):
        recommended_po = self.env['purchase.order'].search([
            ('requisition_id', '=', self.requisition_id.id), ('id', '!=', self.id), ('state', '!=', 'cancel'),
            ('recommendation_order', '=', True)])
        if recommended_po and self.recommendation_order:
            raise ValidationError(_("sorry choose one recommended order"))

    def open_confirmation(self):
        formview_ref = self.env.ref('account_budget_custom.view_budget_confirmation_form', False)
        treeview_ref = self.env.ref('account_budget_custom.view_budget_confirmation_tree', False)
        return {
            'name': ("Budget  Confirmation"),
            'view_mode': 'tree, form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'budget.confirmation',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': "[('id', 'in', %s)]" % self.confirmation_ids.ids,
            'views': [(treeview_ref and treeview_ref.id or False, 'tree'),
                      (formview_ref and formview_ref.id or False, 'form')],
            'context': {'create': False}
        }

    # get account_analytic related to department in order line
    @api.onchange('order_line')
    def on_type_cost_product(self):
        for line in self.order_line:
            if not line.account_analytic_id and line.department_name:
                line.account_analytic_id = line.department_name.analytic_account_id

    def button_draft(self):
        self.write({'state': 'wait'})

    def button_cancel(self):
        budgets = self.env['budget.confirmation'].search([
            ('po_id', '=', self.id),
            ('state', '=', 'done'),
        ])

        for rec in budgets:
            for line in rec.lines_ids:
                budget_post = self.env['account.budget.post'].search([]).filtered(
                    lambda x: line.account_id in x.account_ids.ids)
                analytic_account_id = line.analytic_account_id

                budget_lines = analytic_account_id.crossovered_budget_line.filtered(
                    lambda x: x.general_budget_id in budget_post and
                              x.crossovered_budget_id.state == 'done' and
                              x.date_from <= rec.date <= x.date_to)

                # Revert reserve of budget_lines
                amount = budget_lines.reserve
                amount -= line.amount
                budget_lines.write({'reserve': amount})

        self.budget_amount = 0
        super(PurchaseOrderCustom, self).button_cancel()

    def action_sign_purchase_orders(self):
        for rec in self:
            if rec.state not in ['sign', 'purchase', 'to approve', 'sent', 'done', 'cancel', 'budget_rejected',
                                 'wait_for_send', 'waiting']:
                rec.action_sign()

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(PurchaseOrderCustom, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                               submenu=submenu)
        if (view_type == 'form' or view_type == 'tree') and self.env.user.has_group(
                'purchase_requisition_custom.committe_member') and not (
                self.env.user.has_group('purchase.group_purchase_manager') or self.env.user.has_group(
            'purchase.group_purchase_user')):
            root = etree.fromstring(res['arch'])
            root.set('edit', 'false')
            root.set('create', 'false')
            root.set('duplicate', 'false')
            root.set('delete', 'false')
            res['arch'] = etree.tostring(root)
        else:
            pass

        return res

    def _compute_budget(self):
        purchase_budget = self.env.company.purchase_budget
        for rec in self:
            if purchase_budget:
                rec.is_purchase_budget = True
            else:
                rec.is_purchase_budget = False

    @api.model
    def default_get(self, fields):
        res = super(PurchaseOrderCustom, self).default_get(fields)
        purchase_budget = self.env.company.purchase_budget
        if purchase_budget:
            res['is_purchase_budget'] = True

        else:
            res['is_purchase_budget'] = False
        return res

    @api.model
    def create(self, vals):
        requisition_id = vals.get('requisition_id', False)
        purchase_cost = vals.get('purchase_cost', False)
        if not purchase_cost:
            vals['purchase_cost'] = 'product_line'

        if requisition_id:
            vals['send_to_budget'] = True
        return super(PurchaseOrderCustom, self).create(vals)

    # def button_approve(self,force=False):
    #     res = super(PurchaseOrderCustom, self).button_approve(force=force)
    #     for rec in self:
    #         if rec.requisition_id and rec.requisition_id.state not in ['approve','in_progress']:
    #             raise ValidationError(_("Purchase agreement not approved"))
    #         else:
    #             # You can Approve
    #             for line in self.order_line:
    #                 analytic_account_id = line.account_analytic_id
    #                 budget_post = self.env['account.budget.post'].search([]).filtered(
    #                     lambda
    #                         x: line.product_id.property_account_expense_id.id and line.product_id.property_account_expense_id.id or line.product_id.categ_id.property_account_expense_categ_id.id in x.account_ids.ids)
    #                 budget_lines = analytic_account_id.crossovered_budget_line.filtered(
    #                     lambda x: x.general_budget_id in budget_post and
    #                               x.crossovered_budget_id.state == 'done' and
    #                               fields.Date.from_string(x.date_from) <= fields.Date.from_string(
    #                         rec.date_order) <= fields.Date.from_string(x.date_to))
    #     return res


    def print_quotation(self):
        if self.state in ['wait']:
            self.write({'state': "sent"})
        return self.env.ref('purchase.report_purchase_quotation').report_action(self)

    def action_rfq_send(self):
        res = super(PurchaseOrderCustom, self).action_rfq_send()
        if self.state == 'wait':
            self.state = 'sent'
        return res

    @api.returns('mail.message', lambda value: value.id)
    def message_post(self, **kwargs):
        if self.env.context.get('mark_rfq_as_sent'):
            self.filtered(lambda o: o.state == 'wait').write({'state': 'sent'})
        return super(PurchaseOrderCustom, self.with_context(mail_post_autofollow=True)).message_post(**kwargs)

    def action_approve_po(self):
        for rec in self:
            if rec.requisition_id and rec.requisition_id.state != 'approve':
                rec.requisition_id.write({'state': 'approve'})
            rec.write({'state': 'draft'})

    @api.constrains('state')
    def _state_on_change(self):
        for obj in self:
            if obj.state == 'sent':
                obj.email_to_vendor = True

    @api.depends('requisition_id.project_id')
    def _get_project_data(self):
        for rec in self:
            if rec.requisition_id.project_id:
                rec.project_id = rec.requisition_id.project_id.id

    def action_skip_budget(self):
        """ Skip purchase budget"""
        for po_id in self:
            if po_id.state in ('wait_for_send', 'wait') or po_id.request_id:
                # Deal with double validation process
                valid_amount = self.env.user.company_id.currency_id.compute(
                    po_id.company_id.po_double_validation_amount, po_id.currency_id)
                # second_amount = self.env.user.company_id.currency_id.compute(po_id.company_id.second_approve, po_id.currency_id)
                if po_id.company_id.po_double_validation == 'one_step' \
                        or (po_id.company_id.po_double_validation == 'two_step' \
                            and po_id.amount_total > valid_amount):
                    po_id.write({'state': 'to approve'})
                else:
                    if po_id.email_to_vendor:
                        po_id.write({'state': 'sent'})
                    else:
                        po_id.write({'state': 'draft'})

                    po_id.write({'send_to_budget': False})

    # @api.depends('name')
    def _compute_delviery_order(self):
        precision = self.env['decimal.precision'].precision_get('Product Unit of Measure')
        for order in self:
            if order.state not in ('purchase', 'done'):
                order.state_of_delivery = 'No'
                continue

            if any(
                    not float_is_zero(line.product_qty - line.qty_received, precision_digits=precision)
                    for line in order.order_line.filtered(lambda l: not l.display_type)
            ):
                order.state_of_delivery = 'Partially Received'
            elif (
                    all(
                        float_is_zero(line.product_qty - line.qty_received, precision_digits=precision)
                        for line in order.order_line.filtered(lambda l: not l.display_type)
                    )
                    and order.picking_ids
            ):
                order.state_of_delivery = ' Fully Received '
            else:
                order.state_of_delivery = 'Not Received'

    @api.depends('committe_members')
    def _compute_no_approve(self):
        for rec in self:
            rec.no_of_approve = len(rec.committe_members)

    def action_select_all(self):
        for line in self.order_line:
            line.choosen = True
        self._amount_all()

    @api.constrains('requisition_id', 'partner_id')
    def PreventSameVendor(self):
        """
            Constrain to prevent the same vendor in the order for the same requisition
        """
        orders = self.env['purchase.order'].search([
            ('id', '!=', self.id),
            ('requisition_id', '=', self.requisition_id.id),
            ('requisition_id', '!=', False),
            ('partner_id', '=', self.partner_id.id)
        ])
        if len(orders) != 0:
            raise ValidationError(_("This Vendor have order before"))

    # test

    @api.model
    def _prepare_picking(self):
        if not self.group_id:
            self.group_id = self.group_id.create({
                'name': self.name,
                'partner_id': self.partner_id.id
            })
        if not self.partner_id.property_stock_supplier.id:
            raise UserError(_("You must set a Vendor Location for this partner %s") % self.partner_id.name)
        return {
            'picking_type_id': self.picking_type_id.id,
            'partner_id': self.partner_id.id,
            'date': self.date_order,
            'origin': self.name,
            'location_dest_id': self._get_destination_location(),
            'location_id': self.partner_id.property_stock_supplier.id,
            'company_id': self.company_id.id,
        }

    '''
        override the method that calculate total amount without taxes to calculate only choosen  line
    '''

    def _amount_all(self):
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line:
                if line.choosen:
                    amount_untaxed += line.price_subtotal
                    amount_tax += line.price_tax
            order.update({
                'amount_untaxed': order.currency_id.round(amount_untaxed),
                'amount_tax': order.currency_id.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
            })

    def action_sign(self):
        if self.requisition_id.state == 'approve':
            raise ValidationError(_("Sorry you cannot sin this RFQ The requisition already has been approved"))
        if self.requisition_id.purchase_commitee and self.requisition_id.actual_vote < self.requisition_id.min_vote:
            raise ValidationError(_("Sorry The minimum number of committee member is not satsfied"))
        if self.requisition_id.purchase_commitee and self.no_of_approve < self.requisition_id.min_approve:
            raise ValidationError(
                _("Sorry You cannot sign this quotation ,YOU NEED MORE COMMITTE MEMBERS TO choose it"))
        if len(self.order_line.filtered(lambda line: line.choosen == True)) <= 0:
            raise ValidationError(_('Choose At Least on product to purchase'))
        if self.requisition_id.type_id.exclusive == 'exclusive':
            orders = self.env['purchase.order'].search([
                ('requisition_id', '=', self.requisition_id.id),
                ('id', '!=', self.id)
            ])
            if len(orders) != 0:
                for order in orders:
                    order.action_unsign()
        for rec in self.order_line:
            if rec.price_unit <= 0 and rec.choosen:
                raise ValidationError(_("Unit Price can't be Zero Or less"))
        if self.amount_total == 0:
            raise ValidationError(_("Total Amount Can't be Zero"))
        self.write({'state': 'sign', 'is_signed': True})
        self.requisition_id.state = 'purchase_manager'

    def button_confirm(self):
        for order in self:
            if order.state not in ['draft', 'sent', 'sign','wait']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order._approval_allowed():
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
            if order.partner_id not in order.message_partner_ids:
                order.message_subscribe([order.partner_id.id])
            for line in order.order_line:
                analytic_account = line.account_analytic_id
                budget_lines = analytic_account.crossovered_budget_line.filtered(
                    lambda x:
                    x.crossovered_budget_id.state == 'done' and
                    fields.Date.from_string(x.date_from) <= fields.Date.from_string(
                        order.date_order) <= fields.Date.from_string(x.date_to))
                amount = budget_lines.purchase_remain
                amount += line.price_subtotal
                budget_lines.write({'purchase_remain': amount})
                budget_lines.write({'reserve': abs(line.price_subtotal - budget_lines.reserve)})

            if order.requisition_id.id:
                order.requisition_id.state = 'done'
            if order.request_id:
                order.request_id.write({'state': 'done'})
        return True

    def action_unsign(self):
        """
            Move document to Wait state
        """
        self.write({'state': 'wait', 'is_signed': False})
    @api.depends('committe_members')
    def _compute_already_voted(self):
        for rec in self:
            rec.already_voted = False
            for member in rec.committe_members:
                if member.user_id.id == self.env.user.id and member.select == True:
                    rec.already_voted = True

    def action_select(self):
        for member in self.committe_members:
            if member.user_id.id == self.env.user.id and member.select == True:
                raise ValidationError(_('You have already select this Quotation'))
        self.requisition_id.actual_vote += 1
        return {
            'type': 'ir.actions.act_window',
            'name': 'Select Reason',
            'res_model': 'select.reason',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_order_id': self.id}
        }

    def action_refuse(self):
        for member in self.committe_members:
            if member.user_id.id == self.env.user.id and member.select == True:
                raise ValidationError(_('You have already refused this Quotation'))
            self.requisition_id.actual_vote += 1
        return {
            'type': 'ir.actions.act_window',
            'name': 'Refuse Reason',
            'res_model': 'refuse.reason',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_order_id': self.id}
        }

    def action_budget(self):
        confirmation_lines = []
        amount = 0

        if self.amount_total <= 0:
            raise ValidationError(_("Total Amount MUST be greater than 0 !!!"))

        analytic_account = False
        if self.purchase_cost == 'default':
            analytic_account = self.env.user.company_id.purchase_analytic_account
        elif self.purchase_cost == 'department':
            analytic_account = self.department_id.analytic_account_id
        elif self.purchase_cost == 'project':
            analytic_account = self.project_id.analytic_account_id
            if not analytic_account:
                raise ValidationError(_("No analytic account for the project"))
        elif self.purchase_cost == 'product_line':
            pass  # No analytic account assigned yet, it will be assigned later
        else:
            raise ValidationError(_("No analytic account for the purchase"))

        for order in self:
            for rec in order.order_line:
                if rec.choosen:
                    if self.purchase_cost == 'product_line':
                        analytic_account = rec.account_analytic_id
                        if not analytic_account:
                            raise ValidationError(
                                _("Please put cost center to the product line") + ': {}'.format(rec.product_id.name))
                    account_id = rec.product_id.property_account_expense_id and rec.product_id.property_account_expense_id or rec.product_id.categ_id.property_account_expense_categ_id
                    if not account_id:
                        raise ValidationError(
                            _("This product has no expense account") + ': {}'.format(rec.product_id.name))
                    budget_post = self.env['account.budget.post'].search([]).filtered(lambda x: account_id in x.account_ids)
                    if len(budget_post.ids) > 1:
                        raise ValidationError(
                            _("The Expense account %s is assigned to more than one budget position %s")%(account_id.name,[x.name for x in budget_post]))
                    if analytic_account:
                        budget_lines = self.env['crossovered.budget.lines'].search(
                            [('analytic_account_id', '=', analytic_account.id),
                             ('general_budget_id','in',budget_post.ids),
                             ('crossovered_budget_id.state', '=', 'done'),
                             ('crossovered_budget_id.date_from', '<=', self.date_order),
                             ('crossovered_budget_id.date_to', '>=', self.date_order)])

                        self.budget_id = budget_lines.mapped('crossovered_budget_id').id
                        if budget_lines:
                            remain = abs(budget_lines.remain)
                            amount += rec.price_subtotal
                            new_balance = remain - amount
                            confirmation_lines.append((0, 0, {
                                'amount': rec.price_subtotal,
                                'analytic_account_id': analytic_account.id,
                                'description': rec.product_id.name,
                                'budget_line_id': budget_lines.id,
                                'remain': remain,
                                'new_balance': new_balance,
                                'account_id': rec.product_id.property_account_expense_id.id
                                              or rec.product_id.categ_id.property_account_expense_categ_id.id
                            }))
                        else:
                            confirmation_lines = []
                    else:
                        raise ValidationError(_("Analytic account not set"))

        data = {
            'name': self.name,
            'date': self.date_order,
            'beneficiary_id': self.partner_id.id,
            'department_id': self.department_id.id,
            'type': 'purchase.order',
            'ref': self.name,
            'description': self.purpose,
            'total_amount': self.amount_untaxed,
            'lines_ids': confirmation_lines,
            'po_id': self.id
        }
        self.env['budget.confirmation'].create(data)
        self.write({'state': 'waiting'})

    def budget_resend(self):
        self.action_budget()
        self.write({'state': 'waiting'})


class PurchaseOrderLineCustom(models.Model):
    _inherit = 'purchase.order.line'

    attachment_ids = fields.Many2many('ir.attachment')
    choosen = fields.Boolean(string='Purchase', default=True)
    department_name = fields.Many2one("hr.department", string="Department Name")
    date_end = fields.Date(string="Date End")

    def _create_stock_moves(self, picking):
        '''
            override _create_stock_moves method to create move for only choosen lines
        '''
        moves = self.env['stock.move']
        done = self.env['stock.move'].browse()
        with self.env.norecompute():
            for line in self:
                if line.choosen:
                    for val in line._prepare_stock_moves(picking):
                        done += moves.create(val)
        self.recompute()
        return done


class Attachment(models.Model):
    _inherit = "ir.attachment"

    def unlink(self):
        for record in self:
            if record.res_model == 'purchase.order':
                purchase_order = record.env['purchase.order'].search([
                    ('id', '=', record.res_id)
                ])
                for rec in purchase_order.order_line:
                    if record.id in rec.attachment_ids.ids:
                        rec.write({'attachment_ids': (2, record.id)})
        return super(Attachment, self).unlink()

    def getLine(self, order):
        """
            this function return the line with the least amount of attachment in it
        """
        line = None
        for rec in order.order_line:
            if rec == order.order_line[0]:
                holder = len(rec.attachment_ids.ids)
            if len(rec.attachment_ids.ids) == 0:
                return rec
            elif len(rec.attachment_ids.ids) <= holder:
                line = rec
                holder = len(rec.attachment_ids.ids)
            else:
                continue
        return line


class ProductCustom(models.Model):
    _inherit = 'product.product' 

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        product_ids = []
        if args is None:
            args = []
        res = super(ProductCustom, self)._name_search(name, args=args, operator=operator, limit=limit,
                                                      name_get_uid=name_get_uid)
        if name:
            product_ids = list(self._search([('description', 'ilike', name)] + args, limit=limit))
        if product_ids:
            res += product_ids
        return res

    def action_notify_new_product(self, product):
        # Send Notifications
        subject = _('New Product') + ' - {}'.format(product.name)
        message = _('New product was added. Product Name:') + ' {} '.format(product.name) + '\n' + _(
            'Sale Price: ') + '{}'.format(product.list_price) + '\n' + _('Description: ') + '{}'.format(
            product.description) + '\n' + _('On Date: ') + '{}'.format(fields.Date.today()) + '\n' + _(
            'Created By: ') + '{}'.format(self.env.user.name)
        # group = 'purchase.group_purchase_manager'
        author_id = self.env.user.partner_id.id or None
        self.env.user.partner_id.send_notification_message(subject=subject, body=message, author_id=author_id)

    @api.model
    def create(self, vals):
        res = super(ProductCustom, self).create(vals)
        if 'import_file' not in self.env.context:
            self.action_notify_new_product(res)

        return res


class AccountInvoice(models.Model):
    _inherit = "account.move"

    purchase_id = fields.Many2one('purchase.order', readonly=False, store=True)

    @api.onchange('purchase_id')
    def purchase_order_change(self):
        modules = self.env['ir.module.module'].sudo().search([('state', '=', 'installed'),
                                                              ('name', '=', 'contract')])
        if modules:
            self.contract_id = self.purchase_id.contract_id.id
        if not self.purchase_id:
            return {}
        if not self.partner_id:
            self.partner_id = self.purchase_id.partner_id.id

        vendor_ref = self.purchase_id.partner_ref
        if vendor_ref and (not self.reference or (
                vendor_ref + ", " not in self.reference and not self.reference.endswith(vendor_ref))):
            self.reference = ", ".join([self.reference, vendor_ref]) if self.reference else vendor_ref

        new_lines = self.env['account.move.line']
        for line in self.purchase_id.order_line - self.invoice_line_ids.mapped('purchase_line_id'):
            if line.choosen:
                data = self._prepare_invoice_line_from_po_line(line)
                new_line = new_lines.new(data)
                new_line._set_additional_fields(self)
                new_lines += new_line

        self.invoice_line_ids += new_lines
        self.payment_term_id = self.purchase_id.payment_term_id
        self.env.context = dict(self.env.context, from_purchase_order_change=True)
        self.purchase_id = False
        return {}

# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class ProjectInvoice(models.Model):
    _name = "project.invoice"
    _inherit = ['mail.thread']
    _description = "Project Invoice Request"

    name = fields.Char(string='Description',tracking=True,)
    phase_id = fields.Many2one('project.phase', string="Stage")
    partner_project_id = fields.Many2one('res.partner', string="Partner")
    invoice_id = fields.Many2one('account.move', string="Invoice")
    amount = fields.Float(string="Invoice Amount", compute="compute_amount", store=True,tracking=True,)
    to_invoice = fields.Boolean(string="To invoice", default=False)
    project_id = fields.Many2one('project.project', string="Project")
    sale_order_id = fields.Many2one('sale.order', related='project_id.sale_order_id', store=True)
    company_id = fields.Many2one(related='project_id.company_id', string='Company', store=True, readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Confirmed'),
        ('request', 'Requested'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ],tracking=True, string='Status', readonly=True, copy=False, index=True, default='draft')
    plan_date = fields.Date(string='Due Date',tracking=True,)
    # related to invoice_date
    actual_date = fields.Date(string='Issue Date', compute_sudo=True , compute='_compute_indo_invoice_id')
    plan_payment_date = fields.Date(string='Payment Date',tracking=True,)
    # related date of first payment created from invoice
    actual_payment_date = fields.Date(string='Actual Payment date', compute='get_first_payment_date')
    project_invline_ids = fields.One2many('project.invoice.line', 'project_invoice_id', string='Lines',
        domain=[('is_downpayment', '=', False)])
    project_downinv_ids = fields.One2many('project.invoice.line', 'project_invoice_id', string='Lines',
        domain=[('is_downpayment', '=', True)])
    currency_id = fields.Many2one(related="project_id.currency_id", store=True)
    payment_amount = fields.Monetary(string='Paid Amount',store=True, compute="_compute_payment_amount")
    residual_amount = fields.Monetary('Remaining Amount',store=True, compute_sudo=True , compute='_compute_indo_invoice_id')
    invoice_type = fields.Selection([('project', 'Project'), ('consultant','Consultant'),
        ('variation_order', 'Variation Order')], string='Invoice Type', default='project')
    has_downpayment = fields.Boolean(compute="_check_downpayment")
    payment_state = fields.Selection(selection=[
        ('not_paid', 'Not Paid'),
        ('in_payment', 'In Payment'),
        ('paid', 'Paid'),
        ('partial', 'Partially Paid'),
        ('reversed', 'Reversed'),
        ('invoicing_legacy', 'Invoicing App Legacy')],compute_sudo=True , compute='_compute_indo_invoice_id')
    project_type = fields.Selection(related='project_id.type')


    allowed_internal_user_ids = fields.Many2many('res.users', 'project_invoice_allowed_internal_users_rel',
                                                 string="Allowed Internal Users", default=lambda self: self.env.user, domain=[('share', '=', False)])
    allowed_portal_user_ids = fields.Many2many('res.users', 'project_invoice_allowed_portal_users_rel', string="Allowed Portal Users", domain=[('share', '=', True)])
    
    @api.onchange("project_invline_ids")
    def get_price_unit_value_test(self):
        for rec in self.project_invline_ids:
            if rec.price_unit==0.00:
                rec.price_unit = rec.project_invoice_id.project_id.contract_value_untaxed

    
    @api.depends('invoice_id','invoice_id.invoice_payments_widget','name')
    def _compute_indo_invoice_id(self):
        for record in self:
            record.actual_date = record.invoice_id.invoice_date
            record.residual_amount = record.invoice_id.amount_residual
            record.payment_state = record.invoice_id.payment_state
            
    @api.depends('project_id', 'project_id.is_down_payment', 'project_downinv_ids')
    def _check_downpayment(self):
        for rec in self:
            rec.has_downpayment = False
            if rec.project_downinv_ids:
                rec.has_downpayment = True
            if rec.project_id and rec.project_id.is_down_payment:
                rec.has_downpayment = True

    @api.constrains('plan_date', 'plan_payment_date')
    def _check_plan_dates(self):
        for rec in self:
            if rec.plan_date and rec.plan_payment_date:
                if rec.plan_payment_date < rec.plan_date:
                    raise ValidationError(_("Planned Collection date cannot be earlier than Planned Issue date."))

    def name_get(self):
        result = []
        for record in self.sudo():
            name = '%s' % (record.name and record.name or record.phase_id.name or '/')
            result.append((record.id, name))
        return result

    @api.onchange('phase_id')
    def _onchange_phase(self):
        for rec in self:
            if not rec.name:
                rec.name = rec.phase_id.display_name

    def get_first_payment_date(self):
        invoice_payments = []
        payment = self.env['account.payment'].sudo().search([])
        for rec in self:
            payment = payment.filtered(lambda x: rec.invoice_id.id in x.reconciled_invoice_ids.ids)

            if payment:
                payment_date = payment.mapped('date')

                rec.actual_payment_date = min(payment_date)
            else:
                rec.actual_payment_date = False

    @api.depends('invoice_id', 'invoice_id.amount_residual', 'invoice_id.invoice_payments_widget','name')
    def _compute_payment_amount(self):
        for rec in self:
            rec.payment_amount = rec.invoice_id.amount_total - rec.residual_amount

    def create_invoice(self):
        action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_out_invoice_type")
        form_view = [(self.env.ref('account.view_move_form').id, 'form')]

        invoice_vals = self.with_company(self.company_id)._prepare_invoice()
        invoice_line_vals = []
        for line in self.project_invline_ids:
            invoice_line_vals.append(
                (0, 0, line._prepare_invoice_line()
                 ))
        invoice_vals['invoice_line_ids'] = invoice_line_vals
        invoice_id = self.env['account.move'].sudo().with_context(default_move_type='out_invoice').create(invoice_vals)
        if abs(sum(self.project_downinv_ids.mapped('price_total'))) > abs(
                sum(self.project_invline_ids.mapped('price_total'))):
            raise ValidationError(_("Downpayment amount can't be greater than invoiced amount"))
        self.invoice_id = invoice_id.id
        # self.project_id.purchase_order_id.invoice_id = invoice_id.id
        # if self.project_id.type == 'expense' and self.project_id.purchase_order_id:
        #     self.project_id.purchase_order_id.invoice_ids |= invoice_id
            # self.project_id.purchase_order_id.invoice_ids | = [4,invoice_id.id]
        self.state = 'done'
        user_ids = self.env.ref('account.group_account_manager').users
        self.env['mail.message'].create({
            'message_type': "notification",
            'body': _("Invoice request created for project %s  and need your action") % self.project_id.project_no,
            'subject': _("Invoice Request "),
            'partner_ids': [(6, 0, user_ids.mapped('partner_id').ids)],
            'notification_ids': [(0, 0, {'res_partner_id': user.partner_id.id, 'notification_type': 'inbox'})
                                 for user in user_ids if user_ids],
            'model': self._name,
            'res_id': self.id,
            'author_id': self.env.user.partner_id and self.env.user.partner_id.id
        })
        
        action['views'] = form_view
        action['res_id'] = invoice_id.id
        return action

    def _prepare_invoice(self):
        """
        Prepare the dict of values to create the new invoice for a variation order. This method may be
        overridden to implement custom invoice generation (making sure to call super() to establish
        a clean extension chain).
        """
        invoice_vals = {}
        self.ensure_one()
        journal = self.env['account.move'].sudo().with_context(default_move_type='out_invoice')._get_default_journal()
         # Checking for a partner in the current model and defaulting if not available
        partner_id = self.partner_project_id.id if self.partner_project_id else (self.invoice_type == 'consultant' and self.project_id.consultant_id.id or self.project_id.partner_id.id)

        if not journal:
            raise UserError(_('Please define an accounting sales journal for the company %s (%s).') % (
                self.company_id.name, self.company_id.id))
        if self.project_id.type == 'revenue':
            journal = self.env['account.move'].sudo().with_context(default_move_type='out_invoice')._get_default_journal()
            invoice_vals = {
                'move_type': 'out_invoice',
                'currency_id': self.currency_id.id,
                'ref': self.project_id.project_no,
                'partner_id':partner_id,
                'partner_shipping_id': self.project_id.partner_id.id,
                'partner_bank_id': self.company_id.partner_id.bank_ids.filtered(
                    lambda bank: bank.company_id.id in (self.company_id.id, False))[:1].id,
                'journal_id': journal.id,
                'invoice_line_ids': [],
                'company_id': self.company_id.id,
                'invoice_date_due': self.plan_payment_date,
                'res_model':'project.invoice',
                'res_id':self.id
            }
        elif self.project_id.type == 'expense':
            # journal = self.env['account.move'].sudo().with_context(default_move_type='in_invoice')._get_default_journal()
            journal = self.env['account.journal'].sudo().search([('type','=', 'purchase')], limit=1)
            invoice_vals = {
                'move_type': 'in_invoice',
                'currency_id': self.currency_id.id,
                'ref': self.project_id.project_no,
                'partner_id':partner_id,
                'partner_shipping_id': self.project_id.partner_id.id,
                'partner_bank_id': self.company_id.partner_id.bank_ids.filtered(
                    lambda bank: bank.company_id.id in (self.company_id.id, False))[:1].id,
                'journal_id': journal.id,
                'invoice_line_ids': [],
                'purchase_id': self.invoice_type== 'consultant' and False or self.project_id.purchase_order_id.id ,
                'company_id': self.company_id.id,
                'invoice_date_due': self.plan_payment_date,
                'res_model':'project.invoice',
                'res_id':self.id
            }
        return invoice_vals




    def action_confirm(self):
        self.ensure_one()
        self._set_qty_invoiced()
        if not self.plan_date:
            raise UserError(_("Kindly Enter Planned Issue Date For this Invoice Request"))
        self.state = 'confirm'
        # for rec in self:
        #     return rec.message_post(body=f'Invoice Data /: {rec.name},{rec.state}')





    def action_request(self):
        self.ensure_one()
        if self.project_id.status not in ['open']:
            raise ValidationError(_("You cannot Request Invoice for Project that is not in Open status!"))
        self._set_qty_invoiced()
        self.state = 'request'
        user_ids = self.env.ref('project_base.group_project_create_invoice').users
        self.env['mail.message'].create({
            'message_type': "notification",
            'body': _("Invoice request created for project %s  and need your action") % self.project_id.project_no,
            'subject': _("Invoice Request "),
            'partner_ids': [(6, 0, user_ids.mapped('partner_id').ids)],
            'notification_ids': [(0, 0, {'res_partner_id': user.partner_id.id, 'notification_type': 'inbox'})
                                 for user in user_ids if user_ids],
            'model': self._name,
            'res_id': self.id,
            'author_id': self.env.user.partner_id and self.env.user.partner_id.id
        })
        


    def _set_qty_invoiced(self):
        for rec in self:
            for line in rec.project_invline_ids:
                line.qty_invoiced = line.order_line_id.qty_invoiced

    def action_cancel(self):
        self.ensure_one()
        self.state = 'cancel'

    def action_set_to_draft(self):
        self.ensure_one()
        if self.invoice_id and self.invoice_id.state!='draft':
                raise UserError(_("Kindly The invoice is not in draft state, so it cannot be unlinked."))

        if self.invoice_id:
            self.invoice_id.sudo().write({'posted_before':False})
            self.invoice_id.sudo().unlink()
        self.state = 'draft'
        
    def action_get_invoice(self):
        self.ensure_one()
        view_id = False
        if self.invoice_type == 'variation_order':
            view_id = self.env.ref('project_base.project_invoice_vo_form_view').id
        action_window = {
            "type": "ir.actions.act_window",
            "res_model": "project.invoice",
            "name": "Invoice",
            'view_mode': 'form',
            'view_id': view_id,
            'res_id': self.id,
            "context": {"create": False, 'active_id': self.id, 'active_ids': self.ids, 'id': self.id},
            "target": 'new',
        }
        return action_window

    @api.depends('project_invline_ids', 'project_invline_ids.product_uom_qty', 'project_downinv_ids',
                 'project_downinv_ids.product_uom_qty')
    def compute_amount(self):
        for rec in self:
            rec.amount = sum(rec.project_invline_ids.mapped('price_total')) - abs(
                sum(rec.project_downinv_ids.mapped('price_total')))


class ProjectInvoiceLine(models.Model):
    _name = "project.invoice.line"
    _description = "Project Invoice Line"
    _rec_name = "product_id"

    project_invoice_id = fields.Many2one('project.invoice', string='Project Invoice', required=True, ondelete='cascade',
                                         index=True, copy=False)
    product_id = fields.Many2one('product.product',string='Product')
    product_uom_qty = fields.Float(string='Percentage',digits='Product Unit of Measure',required=True, default=0.0)
    amount = fields.Monetary("Amount")
    product_uom = fields.Many2one('uom.uom', string='Unit of Measure', )
    price_unit = fields.Float('Unit Price', digits='Project  Amount')
    discount = fields.Float(string='Discount (%)', digits='Discount')
    price_subtotal = fields.Monetary(string='Subtotal', store=True)
    price_tax = fields.Float(string='Total Tax', compute="_compute_amount", store=True)
    price_total = fields.Monetary('Total with Taxes', compute="_compute_amount", store=True)
    tax_id = fields.Many2many('account.tax', string='Taxes')
    currency_id = fields.Many2one('res.currency', string='Currency', related="project_invoice_id.currency_id",
                                  store=True)
    order_line_id = fields.Many2one('sale.order.line', string="Sale Line")
    is_downpayment = fields.Boolean(related="order_line_id.is_downpayment", string="Is a down payment", store=True)
    qty_invoiced = fields.Float(string='Invoiced Quantity', readonly=True, digits='Product Unit of Measure')
    name = fields.Char()
    account_id = fields.Many2one(comodel_name='account.account',)

    @api.onchange("project_invoice_id.project_invline_ids")
    def get_price_unit_value(self):
        for rec in self:
            rec.price_unit = rec.project_invoice_id.project_id.contract_value_untaxed
   

    
            
    @api.onchange("price_unit")
    def get_project_invoice_id(self):
        for rec in self:
            rec.product_id = rec.project_invoice_id.project_id.purchase_line_id.product_id
            rec.tax_id = rec.project_invoice_id.project_id.purchase_line_id.taxes_id

    @api.onchange('amount')
    def _onchange_amount(self):
        if self.amount:
            if self.price_unit > 0:
                self.product_uom_qty = self.amount / self.price_unit
            else:
                self.product_uom_qty = 0

    @api.onchange('product_uom_qty')
    def _onchange_qty(self):
        if self.product_uom_qty:
            self.amount = self.product_uom_qty * self.price_unit

    @api.onchange('order_line_id')
    def _onchange_order_line_id(self):
        ''' set all invoice line field.
        '''
        if self.order_line_id:
            self.product_id = self.order_line_id.product_id.id
            self.product_uom_qty = 1
            self.product_uom = self.order_line_id.product_uom.id
            self.price_unit = self.project_invoice_id.project_id.sale_order_amount
            self.tax_id = self.order_line_id.tax_id.ids
            self.qty_invoiced = self.order_line_id.qty_invoiced

    @api.depends('product_uom_qty', 'discount', 'price_unit', 'tax_id')
    def _compute_amount(self):
        """
        Compute the amounts of the IV line.
        """
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.currency_id, line.product_uom_qty, product=line.product_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                # 'price_subtotal': taxes['total_excluded'],
            })

    @api.onchange('product_uom_qty','price_unit')
    def onchange_price_subtotal(self):
        self.price_subtotal =  self.price_unit*self.product_uom_qty

    @api.onchange('price_subtotal','price_unit')
    def onchange_product_uom_qty(self):
        if self.price_unit!=0:
            self.product_uom_qty =  self.price_subtotal/self.price_unit
    def _prepare_invoice_line(self, **optional_values):
        """
        Prepare the dict of values to create the new invoice line for a project invoice line.

        :param qty: float quantity to invoice
        :param optional_values: any parameter that should be added to the returned invoice line
        """
        self.ensure_one()
        # Convert to string to avoid TypeError
        name = str(self.name) if self.name else ''
        project_name = str(self.project_invoice_id.project_id.name) if self.project_invoice_id and self.project_invoice_id.project_id.name else ''
        res = {
                'name': name + '/' + project_name,
                'account_id': self.project_invoice_id.project_id.category_id.account_id and  self.project_invoice_id.project_id.category_id.account_id.id or False,
                'product_id': self.product_id.id,
                'product_uom_id': self.product_uom.id,
                'quantity': self.product_uom_qty,
                'discount': self.discount,
                'price_unit': self.price_unit,
                'tax_ids': [(6, 0, self.tax_id.ids)],
                'analytic_account_id': self.project_invoice_id.project_id.category_id.analytic_account_id and  self.project_invoice_id.project_id.category_id.analytic_account_id.id or False,
                # 'analytic_account_id': self.project_invoice_id.project_id.analytic_account_id.id
                }
        if self.project_invoice_id.project_id.purchase_order_id and self.project_invoice_id.project_id.type == 'expense'  :
            res['analytic_account_id'] =  self.project_invoice_id.project_id.purchase_line_id.account_analytic_id.id
            res['purchase_line_id'] = self.project_invoice_id.project_id.purchase_line_id.id
            # res['account_id'] = self.project_invoice_id.project_id.purchase_line_id.id
        return res

    @api.constrains('product_id', 'product_uom_qty', 'amount')
    def check_product_uom_qty(self):
        for rec in self.filtered(lambda l: not l.is_downpayment):
            total_qty = sum(rec.order_line_id.project_invoiceline_ids.mapped('product_uom_qty'))
            total_amount = sum(rec.order_line_id.project_invoiceline_ids.mapped('amount'))
            if total_qty > rec.order_line_id.product_uom_qty:
                if total_amount > rec.order_line_id.price_subtotal:
                    raise ValidationError(
                        _("The total quantities/Amounts of project invoices must be equal quantities/Amounts in contract item: %s ") % (
                            rec.order_line_id.name))
        for rec in self.filtered(lambda l: l.is_downpayment):
            total_amount = 0.0
            for line in rec.order_line_id.project_invoiceline_ids:
                total_amount += abs(line.amount)
            if total_amount > rec.order_line_id.price_unit:
                raise ValidationError(
                    _("The total amount of Downpayment must not exceed it's amount in contract item: %s ") % (
                        rec.order_line_id.name))


class AccountMove(models.Model):
    _inherit = "account.move"

    project_invoice_id = fields.Many2one('project.project', string='Project Invoice')
    sale_order_id = fields.Many2one('sale.order', 'Sale')


class AccountMove(models.Model):
    _inherit = "account.move.line"

    @api.onchange('product_id')
    def onchange_product_downpayment(self):
        downpayment_line = self.move_id.sale_order_id.mapped('order_line').filtered(lambda l: l.is_downpayment)
        if downpayment_line and self.product_id == downpayment_line.product_id:
            self.sale_line_ids = [(4, downpayment_line.id)]

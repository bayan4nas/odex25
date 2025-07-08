from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta, date
from odoo.tools.misc import get_lang
from odoo.addons.purchase.models.purchase import PurchaseOrder as Purchase


class PurchaseRequest(models.Model):
    _name = 'purchase.request'
    _description = 'Purchase Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    @api.model
    def _default_emp(self):
        emp = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])
        if emp:
            return emp
        else:
            raise ValidationError(_("this user has no related employee!"))

    def copy(self, default=None):
        data = super(PurchaseRequest, self).copy(default)
        data.state = 'draft'
        data.purchase_create = False
        return data

    @api.model
    def _get_picking_type(self, company_id):
        picking_type = self.env['stock.picking.type'].search(
            [('code', '=', 'incoming'), ('warehouse_id.company_id', '=', company_id)])
        if not picking_type:
            picking_type = self.env['stock.picking.type'].search(
                [('code', '=', 'incoming'), ('warehouse_id', '=', False)])
        return picking_type[:1]

    @api.model
    def _default_picking_type(self):
        return self._get_picking_type(self.env.context.get('company_id') or self.env.company.id)

    @api.onchange('company_id')
    def _onchange_company_id(self):
        p_type = self.picking_type_id
        if not (p_type and p_type.code == 'incoming' and (
                p_type.warehouse_id.company_id == self.company_id or not p_type.warehouse_id)):
            self.picking_type_id = self._get_picking_type(self.company_id.id)

    name = fields.Char(string='Name', copy=False, default=lambda self: '/')
    employee_id = fields.Many2one(comodel_name='hr.employee', string='Employee', default=lambda s: s._default_emp().id)
    department_id = fields.Many2one('hr.department', 'Department')
    line_ids = fields.One2many(comodel_name='purchase.request.line', inverse_name='request_id', copy=True)
    date = fields.Date(string='Date', default=fields.Date.context_today, copy=False)
    state = fields.Selection(
        [('draft', 'Draft'), ('direct_manager', 'Direct Manager'),
         ('waiting', 'In Purchase'), ('done', 'Done'), ('cancel', 'Cancel'), ('refuse', 'Refuse')], default="draft",
        tracking=True, )
    product_category_ids = fields.Many2many('product.category', string='Items Categories',
                                            compute='_compute_product_category_ids',
                                            store=True)
    purchase_purpose = fields.Char("Purpose")
    note = fields.Text(string='Note', copy=False)
    partner_id = fields.Many2one(string='Vendor', comodel_name='res.partner', copy=False)
    type_id = fields.Many2one('purchase.requisition.type', string="Agreement Type", copy=False)
    requisition_id_ids = fields.One2many("purchase.requisition", "request_id")
    purchase_ids = fields.One2many("purchase.order", "request_id")

    is_requisition = fields.Boolean(default=False)

    company_id = fields.Many2one('res.company', 'Company', required=True, index=True,
                                 default=lambda self: self.env.company)
    picking_type_id = fields.Many2one('stock.picking.type', 'Deliver To', states=Purchase.READONLY_STATES,
                                      required=True, default=_default_picking_type,
                                      domain="['|', ('warehouse_id', '=', False), ('warehouse_id.company_id', '=', company_id)]",
                                      help="This will determine operation type of incoming shipment")

    purchase_create = fields.Boolean(string='Purchase Create', copy=False)
    by_purchase = fields.Boolean('Requested by Purchase')
    type = fields.Selection([('project', 'Project'), ('operational', 'Operational')], default='operational')
    edit_partner_id = fields.Boolean(compute="compute_edit_partner_id")
    use_analytic = fields.Boolean("Use Analytic")
    account_analytic_id = fields.Many2one("account.analytic.account", )
    # committe_members = fields.One2many('committe.member', inverse_name='po_id')
    is_creator = fields.Boolean(string='Is Creator', compute='_compute_is_creator')
    select = fields.Boolean(string="Select")
    reject_reason = fields.Text(string='Reject Reson')

    @api.depends('line_ids.product_id')
    def _compute_product_category_ids(self):
        for rec in self:
            categories = rec.line_ids.mapped('product_id.categ_id')
            rec.product_category_ids = categories

    @api.depends('create_uid')
    def _compute_is_creator(self):
        for record in self:
            record.is_creator = (record.create_uid == self.env.user)

    def read(self, records):
        return super(PurchaseRequest, self.sudo()).read(records)

    def open_purchase(self):
        formview_ref = self.env.ref('purchase.purchase_order_form', False)
        treeview_ref = self.env.ref('purchase.purchase.purchase_order_tree', False)
        return {
            'name': _("Purchase Request"),
            'view_mode': 'tree, form',
            'view_type': 'form',
            'view_id': False,
            'res_model': 'purchase.order',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': "[('id', 'in', %s)]" % self.purchase_ids.ids,
            'views': [(treeview_ref and treeview_ref.id or False, 'tree'),
                      (formview_ref and formview_ref.id or False, 'form')],

            'context': {'create': False}
        }

    def compute_edit_partner_id(self):
        """Compute For Group Edit Partner Id"""
        for rec in self:
            if self.env.user.has_group("purchase.group_purchase_user") or self.env.user.has_group(
                    "purchase.group_purchase_manager"):
                rec.edit_partner_id = True
            else:
                rec.edit_partner_id = False

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'stock.request.order') or _('New')
        res = super(PurchaseRequest, self).create(vals)
        return res

    def open_requisition(self):
        formview_ref = self.env.ref('purchase_requisition.view_purchase_requisition_form', False)
        treeview_ref = self.env.ref('purchase_requisition.view_purchase_requisition_tree', False)
        return {
            'name': _("Purchase Agreement"),
            'view_mode': 'tree, form',
            'view_id': False,
            'view_type': 'form',
            'res_model': 'purchase.requisition',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'domain': "[('id', 'in', %s)]" % self.requisition_id_ids.ids,
            'views': [(treeview_ref and treeview_ref.id or False, 'tree'),
                      (formview_ref and formview_ref.id or False, 'form')],
            'context': {'create': False}
        }

    # test empty department
    @api.onchange('employee_id', 'department_id', 'line_ids')
    def onchange_emp_depart(self):
        for line in self.line_ids:
            if self.employee_id and not self.department_id:
                raise ValidationError(_("Please Select department for employee"))

    @api.onchange('employee_id', 'by_purchase')
    def change_employee_id(self):
        if self.employee_id and self.by_purchase:
            self.department_id = self.employee_id.department_id.id
        else:
            self.employee_id = self._default_emp().id
            self.department_id = self._default_emp().department_id.id

    def action_submit(self):
        if len(self.line_ids) == 0:
            raise ValidationError(_("Can't Confirm Request With No Item!"))
        self.write({'state': 'direct_manager'})

    def action_confirm(self):
        if len(self.line_ids) == 0:
            raise ValidationError(_("Can't Confirm Request With No Item!"))
        if not self.department_id:
            raise ValidationError(_("Please Select department for employee"))

        self.write({'state': 'wait_for_send'})

    # def action_select(self):
    #     for member in self.committe_members:
    #         if member.user_id.id == self.env.user.id and member.select == True:
    #             raise ValidationError(_('You have already select this Quotation'))
    #     self.requisition_id.actual_vote += 1
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Select Reason',
    #         'res_model': 'select.reason',
    #         'view_mode': 'form',
    #         'target': 'new',
    #         'context': {'default_request_id': self.id}
    #     }
    def action_refuse(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Refuse Reason',
            'res_model': 'refuse.reason',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_request_id': self.id}
        }

    def action_done(self):
        self.write({'state': 'done'})

    def action_draft(self):
        self.write({'state': 'draft'})

    def unlink(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_("You cant delete record not in draft state!"))
        res = super().unlink()
        return res

    def create_requisition(self):
        self.is_requisition = True
        if not self.employee_id.department_id:
            raise ValidationError(_("Choose A Department For this Employee!"))
        line_ids = []
        for line in self.line_ids:
            line_ids.append((0, 6, {
                'product_id': line.product_id.id,
                'department_id': line.request_id.department_id.id or False,
                'product_qty': line.qty,
                'name': line.product_id.name,
                'account_analytic_id': line.account_id.id,
            }))
        requisition_id = self.env['purchase.requisition'].with_context(skip_category_constraint=True).sudo().create({
            'category_ids': self.product_category_ids.ids,
            'type_id_test': self.type_id.id,
            'department_id': self.employee_id.department_id.id,
            'type': self.type,
            'purpose': self.purchase_purpose,
            'request_id': self.id,
            'user_id': self.employee_id.user_id.id,
            'line_ids': line_ids,
            'res_id': self.id,
            'res_model': "purchase.request",

        })
        self.write({'purchase_create': True})

        return {
            'name': "Request for Quotation",
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.requisition',
            'view_mode': 'form',
            'res_id': requisition_id.id,
        }

    def create_purchase_order2(self):
        if not self.partner_id:
            raise UserError(_("You must set a Vendor this PO"))
        # if not self.partner_id :
        #     raise ValidationError("Please Insert ")
        if self.use_analytic:
            analytic_account = self.account_analytic_id.id
        else:
            analytic_account = self.department_id.analytic_account_id.id
        line_ids = []
        for line in self.line_ids:
            line_ids.append((0, 6, {
                'product_id': line.product_id.id,
                'product_qty': line.qty,
                'name': line.description or line.product_id.name,
                'department_name': self.employee_id.department_id.id,
                'account_analytic_id': analytic_account,
                'date_planned': datetime.today(),
                'price_unit': 0,
            }))

        purchase_order = self.env['purchase.order'].sudo().create({
            'category_ids': self.product_category_ids.ids,
            'origin': self.name,
            'request_id': self.id,
            'partner_id': self.partner_id.id,
            'department_id': self.department_id.id,
            'purpose': self.purchase_purpose,
            'purchase_cost': 'product_line',
            'order_line': line_ids,
            # 'res_model':"purchase.request",
            # 'res_id': self.id,  # Reference to the current purchase order

        })
        self.write({'purchase_create': True})

        return {
            'name': "Purchase orders from employee",
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'res_id': purchase_order.id,
            # 'context': {"default_res_id": self.id, "default_res_model":'purchase.request' }
        }


class PurchaseRequestLine(models.Model):
    _name = 'purchase.request.line'
    _description = 'purchase request line'

    account_id = fields.Many2one(related='request_id.department_id.analytic_account_id', copy=False)
    request_id = fields.Many2one(comodel_name='purchase.request', string='Request Ref.')
    product_id = fields.Many2one(comodel_name='product.product', string='Item')
    description = fields.Char("Description")
    qty = fields.Integer(string='Qty')
    uom_id = fields.Many2one('uom.uom',
                             related='product_id.uom_po_id', readonly=True)

    def _product_id_change(self):
        if not self.product_id:
            return

        product_lang = self.product_id.with_context(
            lang=get_lang(self.env, self.partner_id.lang).code,
            partner_id=self.partner_id.id,
            company_id=self.company_id.id)
        self.name = self._get_product_purchase_description(product_lang)

    @api.constrains('qty')
    def qty_validation(self):
        for rec in self:
            if rec.qty <= 0:
                raise ValidationError(_("Item Quantity MUST be at Least ONE!"))


class Employee(models.Model):
    _inherit = 'hr.employee'

    def name_get(self):
        get_all = self.env.context.get('get_all', False)
        department = self.env.context.get('department', False)
        domain = []
        if department:
            domain += [('department_id', '=', department)]
        if get_all:
            employees = self.env['hr.employee'].sudo().search(domain)
            result = [(employee.id, employee.name) for employee in employees]
            return result
        else:
            return super(Employee, self).name_get()

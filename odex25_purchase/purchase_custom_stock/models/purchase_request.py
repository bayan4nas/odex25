from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta, date
from odoo.tools.misc import get_lang
from odoo.addons.purchase.models.purchase import PurchaseOrder as Purchase


class PurchaseRequest(models.Model):
    _inherit = 'purchase.request'


    warehouse_id = fields.Many2one("stock.warehouse", string= "Warehouse" ,copy=False)
    view_location_id = fields.Many2one(related="warehouse_id.view_location_id", string= "Warehouse",copy=False )
    location_id = fields.Many2one("stock.location", string= "Location",domain="[('id', 'child_of', view_location_id),('usage', '=', 'internal')]",copy=False )
    picking_id=fields.Many2one("stock.picking",copy=False)
    edit_locations=fields.Boolean(string="Edit Locations",compute='compute_edit_locations',copy=False)
    state = fields.Selection(
        [('draft', 'Draft'), ('direct_manager', 'Direct Manager'),('secretary_general', 'Secretary General'),
         ('sector_head_approval', 'Sector Head Approval'),('warehouse', 'Warehouses Department'),('wait_for_send', 'Wait For Sent'),
         ('initial', 'Initial Engagement'),
         ('waiting', 'In Purchase'),('employee', 'Employee Delivery'),('done', 'Done'), ('cancel', 'Cancel'), ('refuse', 'Refuse')], default="draft",
        tracking=True,copy=False )
    show_emp_button=fields.Boolean(compute='show_employee_button',copy=False)
    show_approve_warehouse=fields.Boolean("Approve Warehouse",compute='show_approve_warehouse_button')
    total_sum = fields.Float(string="Total Sum", compute="_compute_total_sum", store=True)

    # @api.depends('line_ids.line_total')
    def _compute_total_sum(self):
        for record in self:
            record.total_sum = sum(line.line_total for line in record.line_ids)

    def action_secretary_general(self):
        self.state = "sector_head_approval"

    def action_sector_head_approval(self):
        if any(self.line_ids.filtered(lambda line: line.product_id.type == "product")):
            self.write({'state': 'warehouse'})
        else:
            for rec in self.line_ids:
                rec.write({"qty_purchased": rec.qty})

            init_active = self.env['ir.module.module'].search(
                [('name', '=', 'initial_engagement_budget'), ('state', '=', 'installed')], limit=1)
            init_budget = True if init_active else False
            self.write({'state': 'wait_for_send' if init_budget else 'waiting'})

    def show_employee_button(self):
        """show only for the create employee"""
        for rec in self:
            rec.show_emp_button=False
            if rec.create_uid.id == self.env.user.id and rec.state == 'employee':
                rec.show_emp_button=True

    @api.depends("warehouse_id")
    def show_approve_warehouse_button(self):
        """show only for the show aaprove warhouse employee"""
        for rec in self:
            rec.show_approve_warehouse=False
            if rec.warehouse_id.manager_id.user_id.id == self.env.user.id and rec.state == 'warehouse':
                rec.show_approve_warehouse=True


    def compute_edit_locations(self):
        """Compute For Group Edit Warehouse/Locations"""
        for rec in self:
            if self.env.user.has_group("stock.group_stock_user") or self.env.user.has_group(
                    "stock.group_stock_manager") :
                rec.edit_locations = True
            else:
                rec.edit_locations = False

    def action_confirm(self):
        init_active = self.env['ir.module.module'].search(
            [('name', '=', 'initial_engagement_budget'), ('state', '=', 'installed')], limit=1)
        init_budget = True if init_active else False

        if len(self.line_ids) == 0:
            raise ValidationError(_("Can't Confirm Request With No Item!"))
        if not self.department_id:
            raise ValidationError(_("Please Select department for employee"))

        direct_manager = self.sudo().department_id.manager_id
        if direct_manager and direct_manager.user_id and self.env.user.id != direct_manager.user_id.id:
            raise ValidationError(_("only %s Direct Manager can approve the order" % self.sudo().employee_id.name))

        if self.total_sum > 10000:
            self.state = 'secretary_general'
        else:
            self.state = 'sector_head_approval'

    def create_requisition(self):
        """inherit for take in considiration available qty """
        self.is_requisition = True
        if not self.sudo().employee_id.department_id:
            raise ValidationError(_("Choose A Department For this Employee!"))
        line_ids = []
        for line in self.line_ids.filtered(lambda line: line.qty_purchased > 0):
            line_ids.append((0, 6, {
                'product_id': line.product_id.id,
                'department_id': line.request_id.sudo().department_id.id or False,
                'product_qty': line.qty_purchased,
                'name': line.product_id.name,
                'account_analytic_id': line.account_id.id,
            }))
        requisition_id = self.env['purchase.requisition'].sudo().create({
            'category_ids': self.product_category_ids.ids,
            'type_id_test': self.type_id.id,
            'department_id': self.sudo().employee_id.department_id.id,
            'type': self.type,
            'purpose': self.purchase_purpose,
            'request_id': self.id,
            'user_id': self.sudo().employee_id.user_id.id,
            'line_ids': line_ids,
            'res_id': self.id,
            'res_model':"purchase.request",

        })
        self.write({'purchase_create': True,'state':'employee'})

        return {
            'name': "Request for Quotation",
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.requisition',
            'view_mode': 'form',
            'res_id': requisition_id.id,
        }

    def create_purchase_order2(self):
        if not self.partner_id :
            raise ValidationError(_("Please Insert a Vendor"))
        line_ids = []
        for line in self.line_ids.filtered(lambda line: line.qty_purchased > 0):
            line_ids.append((0, 6, {
                'product_id': line.product_id.id,
                'product_qty': line.qty_purchased,
                'name':line.description or line.product_id.name,
                'department_name': self.sudo().employee_id.department_id.id,
                'account_analytic_id': line.account_id.id,
                'date_planned': datetime.today(),
                'price_unit': 0,
            }))

        purchase_order = self.env['purchase.order'].sudo().create({
            'category_ids': self.product_category_ids.ids,
            'origin': self.name,
            'request_id': self.id,
            'partner_id': self.partner_id.id,
            'purpose': self.purchase_purpose,
            'purchase_cost': 'product_line',
            'order_line': line_ids,
            'res_model':"purchase.request",
            'res_id': self.id,  # Reference to the current purchase order

        })
        self.write({'purchase_create': True,'state':'employee'})

        return {
            'name': "Purchase orders from employee",
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'res_id': purchase_order.id}

    def action_confirm_picking(self):
        if len(self.line_ids) == 0:
            raise ValidationError(_("Can't Confirm Request With No Item!"))
        if not self.department_id:
            raise ValidationError(_("Please Select department for employee"))
        picking_id= self.env.ref('purchase_custom_stock.stock_picking_type_stock')

        available=False
        if any(self.line_ids.filtered(lambda line: line.product_id.type == 'product' )):
            storable_product_lines=self.line_ids.filtered(lambda line: line.product_id.type == 'product' )
            non_storable_product = self.line_ids - storable_product_lines
            if any(storable_product_lines.filtered(lambda line: line.available_qty > 0)):
                available = True
            if any(storable_product_lines.filtered(lambda store_line: store_line.qty > store_line.available_qty)):
                context = {}
                view = self.env.ref('purchase_custom_stock.purchase_request_picking_wizard_view_form')
                wiz = self.env['purchase.request_picking.wizard']
                context['default_request_id'] = self.id
                context['default_is_available'] = available
                storable_product = self.line_ids.filtered(lambda line: line.product_id.type == 'product')
                context['default_request_line_ids'] = [
                    (6, 0, self.line_ids.ids)]

                return {
                    'name': _('Picking Options'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'purchase.request_picking.wizard',
                    'views': [(view.id, 'form')],
                    'view_id': view.id,
                    'target': 'new',
                    'context': context,
                }
            else:
                picking_vals = {
                    "picking_type_id": self.env.ref('purchase_custom_stock.stock_picking_type_stock').id,
                    "origin": self.name,
                    "location_id": self.location_id.id,
                    "location_dest_id": picking_id.default_location_dest_id.id
                }
                move_vals = []
                for line in storable_product_lines:
                    move_vals.append((0, 0, {
                        "product_id": line.product_id.id,
                        "name": line.product_id.name,
                        "product_uom": line.product_id.uom_id.id,
                        'product_uom_qty': line.qty,

                    }))
                    line.qty_purchased = 0
                picking_vals.update({'move_lines': move_vals})
                picking_id = self.env['stock.picking'].create(picking_vals)
                self.picking_id = picking_id.id
                if non_storable_product:
                    for rec in non_storable_product:
                        rec.qty_purchased = rec.qty
                    self.write({'state': 'waiting'})
                else:
                    self.write({'state': 'employee'})
        else:
            for line in self.line_ids:
                line.qty_purchased = line.qty
            self.write({'state': 'waiting'})




    def open_picking(self):

        return {
            'name': _("Picking Request"),
            'view_mode': 'form',
            'view_type': 'form',
            'res_model': 'stock.picking',
            'res_id':self.picking_id.id,
            'type': 'ir.actions.act_window',
            'target':'current',
        }

    def action_available_qty(self):
        for rec in self:
            if not rec.location_id:
                raise ValidationError(_("Please Insert Location first"))
            for line in rec.line_ids:
                line.available_qty = self.env['stock.quant'].search(
                    [('product_id', '=', line.product_id.id), ('location_id', '=', rec.location_id.id)],
                    limit=1).available_quantity
                line.qty_purchased=line.qty-line.available_qty

    def write(self, vals):
        """Override Send Notification On state"""
        res = super(PurchaseRequest, self).write(vals)

        if 'state' in vals:
            if vals['state'] == 'direct_manager':
                direct_manager = self.sudo().department_id.manager_id
                if direct_manager and direct_manager.user_id:
                    if self.env.user.partner_id.lang == 'ar_001':
                        body = 'عزيزى  %s موافقتك مطلوبة على %s ' % (direct_manager.name, self.name)
                    else:
                        body = 'Dear %s your approval is required on %s ' % (direct_manager.name, self.name)
                    self.message_notify(body=body,
                                        partner_ids=[direct_manager.user_id.partner_id.id])

            elif vals['state'] == 'warehouse':
                warehouse = self.env['stock.warehouse'].sudo().search([('department_id', '=', self.department_id.id)])
                stock_employee = False
                if warehouse and warehouse.manager_id:
                    stock_employee = warehouse.manager_id

                if stock_employee and stock_employee.user_id.partner_id.id:
                    if self.env.user.partner_id.lang == 'ar_001':
                        body = 'عزيزى  %s موافقتك مطلوبة على %s ' % (stock_employee.name, self.name)
                    else:
                        body = 'Dear %s your approval is required on %s ' % (stock_employee.name, self.name)
                    self.message_notify(body=body,
                                        partner_ids=[stock_employee.user_id.partner_id.id])

            elif vals['state'] == 'waiting':
                purchase_group = self.env.ref('purchase.group_purchase_manager')
                purchase_users = self.env['res.users'].search([('groups_id', '=', purchase_group.id)])
                for user in purchase_users:
                    purchase_employee = self.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
                    if self.env.user.partner_id.lang == 'ar_001':
                        body = 'عزيزى  %s موافقتك مطلوبة على %s ' % (purchase_employee.name, self.name)
                    else:
                        body = 'Dear %s your approval is required on %s ' % (purchase_employee.name, self.name)
                    if purchase_employee and user.partner_id.id:
                        self.message_notify(body=body,
                                            partner_ids=[user.partner_id.id])

            elif vals['state'] == 'employee':
                if self.sudo().employee_id and self.sudo().employee_id.user_id:
                    if self.env.user.partner_id.lang == 'ar_001':
                        body = 'عزيزى  %s يرجى تاكيد استلامك على  %s ' % (self.sudo().employee_id.name, self.name)
                    else:
                        body = 'Dear %s please confirm Your receipt on %s ' % (self.sudo().employee_id.name, self.name)

                    self.message_notify(body=body,
                                        partner_ids=[self.sudo().employee_id.user_id.partner_id.id])

        return res





class PurchaseRequestLine(models.Model):
    _inherit = 'purchase.request.line'
    _description = 'purchase request line'

    qty_purchased = fields.Integer(string='Purchase Qty',copy=False)
    qty = fields.Integer(string='Demand Qty')
    available_qty = fields.Integer(string='Available Qty',copy=False)


    @api.constrains('qty')
    def qty_validation(self):
        for rec in self:
            if rec.qty <= 0:
                raise ValidationError(_("Item Quantity MUST be at Least ONE!"))



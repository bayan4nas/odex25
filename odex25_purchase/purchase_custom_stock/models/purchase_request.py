from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError, Warning
from datetime import datetime, timedelta, date
from odoo.tools.misc import get_lang
from odoo.addons.purchase.models.purchase import PurchaseOrder as Purchase


class PurchaseRequest(models.Model):
    _inherit = 'purchase.request'

    warehouse_id = fields.Many2one("stock.warehouse", string="Warehouse", copy=False)
    view_location_id = fields.Many2one(related="warehouse_id.view_location_id", string="Warehouse", copy=False)
    location_id = fields.Many2one("stock.location", string="Location",
                                  domain="[('id', 'child_of', view_location_id),('usage', '=', 'internal')]",
                                  copy=False)
    picking_id = fields.Many2one("stock.picking", copy=False)
    edit_locations = fields.Boolean(string="Edit Locations", compute='compute_edit_locations', copy=False)
    state = fields.Selection(
        [('draft', 'Draft'), ('direct_manager', 'Direct Manager'), ('warehouse', 'Warehouses Department'),
         ('wait_for_send', 'Wait For Sent'),
         ('initial', 'Initial Engagement'),
         ('waiting', 'In Purchase'), ('employee', 'Employee Delivery'), ('done', 'Done'), ('cancel', 'Cancel'),
         ('refuse', 'Refuse')], default="draft",
        tracking=True, copy=False)
    show_emp_button = fields.Boolean(compute='show_employee_button', copy=False)
    show_approve_warehouse = fields.Boolean("Approve Warehouse", compute='show_approve_warehouse_button')
    has_asset_product_line = fields.Boolean(string="Has Asset Product", compute="_compute_has_asset_product_line",
                                            store=True)
    show_asset_release_button = fields.Boolean(string="Show Asset Release Button",
                                               compute="_compute_show_asset_release_button")
    asset_request_line_ids = fields.One2many('asset.custody.line', 'purchase_request_id')
    asset_assign_count = fields.Integer(compute='_asset_assign_count', string='Asset Assignment')
    asset_release_count = fields.Integer(compute='_asset_release_count', string='Asset Release')
    all_assets_released = fields.Boolean(string="All Assets Released", compute="_compute_all_assets_released")
    asset_custody_complete = fields.Boolean(compute='_compute_asset_custody_complete',
                                            string='Asset Custody Complete',
                                            help='True when all asset products have custody lines and operations in done state'
                                            )

    def _asset_assign_count(self):
        self.asset_assign_count = len(
            self.env['asset.custody.line'].search([('purchase_request_id', '=', self.id)]))

    def _asset_release_count(self):
        self.asset_release_count = len(
            self.env['asset.custody.line'].search([('purchase_request_id', '=', self.id)]))

    @api.depends('line_ids.product_id')
    def _compute_has_asset_product_line(self):
        for rec in self:
            rec.has_asset_product_line = any(
                rec.line_ids.filtered(lambda line: line.product_id.asset_ok)
            )

    def _compute_show_asset_release_button(self):
        for rec in self:
            operations = self.env['account.asset.operation'].search([
                ('purchase_request_id', '=', rec.id),
                ('type', '=', 'assignment')
            ])
            states = operations.mapped('state')
            if operations and set(states).issubset({'done', 'cancel'}) and 'done' in states:
                rec.show_asset_release_button = True
            else:
                rec.show_asset_release_button = False

    @api.depends('asset_request_line_ids')
    def _compute_all_assets_released(self):
        for rec in self:
            rec.all_assets_released = False
            if not rec.asset_request_line_ids:
                continue
            asset_ids = rec.asset_request_line_ids.mapped('asset_id.id')
            if not asset_ids:
                continue
            release_ops = self.env['account.asset.operation'].search([
                ('purchase_request_id', '=', rec.id),
                ('asset_id', 'in', asset_ids),
                ('type', '=', 'release'),
                ('state', '=', 'done')
            ])
            released_asset_ids = release_ops.mapped('asset_id.id')
            rec.all_assets_released = all(asset_id in released_asset_ids for asset_id in asset_ids)

    @api.depends('line_ids', 'asset_request_line_ids')
    def _compute_asset_custody_complete(self):
        for record in self:
            asset_custody_complete = True
            asset_products = record.line_ids.filtered(lambda l: l.product_id.asset_ok)
            if not asset_products:
                record.asset_custody_complete = False
                continue
            for line in asset_products:
                required_qty = int(line.qty)
                existing_custody_count = self.env['asset.custody.line'].search_count([
                    ('purchase_request_id', '=', record.id),
                    ('asset_id.product_id', '=', line.product_id.id)
                ])

                if existing_custody_count != required_qty:
                    asset_custody_complete = False
                    break
            if asset_custody_complete and record.asset_request_line_ids:
                for custody_line in record.asset_request_line_ids:
                    done_ops_count = self.env['account.asset.operation'].search_count([
                        ('purchase_request_id', '=', record.id),
                        ('type', '=', 'assignment'),
                        ('asset_id', '=', custody_line.asset_id.id),
                        ('state', '=', 'done')
                    ])

                    if done_ops_count == 0:
                        asset_custody_complete = False
                        break

            record.asset_custody_complete = asset_custody_complete

    def show_employee_button(self):
        """show only for the create employee"""
        for rec in self:
            rec.show_emp_button = False
            if rec.create_uid.id == self.env.user.id and rec.state == 'employee':
                rec.show_emp_button = True

    @api.depends("warehouse_id", "line_ids", "state")
    def show_approve_warehouse_button(self):
        """show only for the show aaprove warhouse employee"""
        for rec in self:
            rec.show_approve_warehouse = False
            if (rec.warehouse_id.manager_id.user_id.id == self.env.user.id or any(
                    rec.line_ids.filtered(lambda line: line.product_id.asset_ok))) and rec.state == 'warehouse':
                rec.show_approve_warehouse = True

    def compute_edit_locations(self):
        """Compute For Group Edit Warehouse/Locations"""
        for rec in self:
            if self.env.user.has_group("stock.group_stock_user") or self.env.user.has_group(
                    "stock.group_stock_manager"):
                rec.edit_locations = True
            else:
                rec.edit_locations = False

    def action_confirm(self):
        init_active = self.env['ir.module.module'].sudo().search(
            [('name', '=', 'initial_engagement_budget'), ('state', '=', 'installed')], limit=1)
        init_budget = self.initial_engagement_activate
        if len(self.line_ids) == 0:
            raise ValidationError(_("Can't Confirm Request With No Item!"))
        if not self.department_id:
            raise ValidationError(_("Please Select department for employee"))
        employee_direct_manager = self.sudo().employee_id.parent_id
        if employee_direct_manager and employee_direct_manager.user_id and self.env.user.id != employee_direct_manager.user_id.id:
            raise ValidationError(_("only %s Direct Manager can approve the order" % self.sudo().employee_id.name))
        if any(self.line_ids.filtered(lambda line: line.product_id.type == "product" or line.product_id.asset_ok)):
            self.write({'state': 'warehouse'})
        else:
            for rec in self.line_ids:
                rec.write({"qty_purchased": rec.qty})
            self.write({'state': 'wait_for_send' if init_budget else 'waiting'})

    def create_requisition(self):
        """inherit for take in considiration available qty """
        self.is_requisition = True
        if not self.sudo().employee_id.department_id:
            raise ValidationError(_("Choose A Department For this Employee!"))
        line_ids = []
        for line in self.line_ids.filtered(lambda line: line.qty_purchased > 0):
            account_analytic_id = self.account_analytic_id.id if self.use_analytic and self.account_analytic_id else line.account_id.id
            line_ids.append((0, 6, {
                'product_id': line.product_id.id,
                'department_id': line.request_id.sudo().department_id.id or False,
                'product_qty': line.qty_purchased,
                'name': line.product_id.name,
                'account_analytic_id': account_analytic_id,
                'product_uom_id': line.uom_id.id
            }))
        requisition_vals = {
            'category_ids': self.product_category_ids.ids,
            'type_id_test': self.type_id.id,
            'department_id': self.sudo().employee_id.department_id.id,
            'type': self.type,
            'purpose': self.purchase_purpose,
            'request_id': self.id,
            'user_id': self.sudo().employee_id.user_id.id,
            'line_ids': line_ids,
            'res_id': self.id,
            'res_model': "purchase.request",
        }
        if self.use_analytic and self.account_analytic_id:
            requisition_vals['purchase_cost'] = 'product_line'
        requisition_id = self.env['purchase.requisition'].with_context(skip_category_constraint=True).sudo().create(requisition_vals)
        self.write({'purchase_create': True, 'state': 'employee'})

        return {
            'name': "Request for Quotation",
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.requisition',
            'view_mode': 'form',
            'res_id': requisition_id.id,
        }

    def create_purchase_order2(self):
        if not self.partner_id:
            raise ValidationError(_("Please Insert a Vendor"))
        line_ids = []
        for line in self.line_ids.filtered(lambda line: line.qty_purchased > 0):
            account_analytic_id = self.account_analytic_id.id if self.use_analytic and self.account_analytic_id else line.account_id.id
            line_ids.append((0, 6, {
                'product_id': line.product_id.id,
                'product_qty': line.qty_purchased,
                'name': line.description or line.product_id.name,
                'department_name': self.sudo().employee_id.department_id.id,
                'account_analytic_id': account_analytic_id,
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
            'res_model': "purchase.request",
            'res_id': self.id,  # Reference to the current purchase order

        })
        self.write({'purchase_create': True, 'state': 'employee'})

        return {
            'name': "Purchase orders from employee",
            'type': 'ir.actions.act_window',
            'res_model': 'purchase.order',
            'view_mode': 'form',
            'res_id': purchase_order.id,
            }

    def action_confirm_picking(self):
        if not self.line_ids:
            raise ValidationError(_("Can't Confirm Request With No Item!"))
        if not self.department_id:
            raise ValidationError(_("Please Select department for employee"))
        picking_id = self.env.ref('purchase_custom_stock.stock_picking_type_stock')

        available = False
        if any(self.line_ids.filtered(lambda line: line.product_id.type in ['product', 'consu'])):
            storable_product_lines = self.line_ids.filtered(lambda line: line.product_id.type == 'product')
            asset_product_lines = self.line_ids.filtered(lambda line: line.product_id.asset_ok)
            consu_product_not_asset_lines = self.line_ids.filtered(
                lambda line: line.product_id.type == 'consu' and not line.product_id.asset_ok)
            non_storable_product = self.line_ids - storable_product_lines - asset_product_lines - consu_product_not_asset_lines
            if any(storable_product_lines.filtered(lambda line: line.available_qty > 0)) or any(
                    consu_product_not_asset_lines.filtered(lambda line: line.available_qty > 0)) or any(
                asset_product_lines.filtered(lambda line: line.available_qty > 0)):
                available = True
            if any(storable_product_lines.filtered(
                    lambda store_line: store_line.qty > store_line.available_qty)) or any(
                asset_product_lines.filtered(lambda asset_line: asset_line.qty > asset_line.available_qty)) or any(
                consu_product_not_asset_lines.filtered(lambda asset_line: asset_line.qty > asset_line.available_qty)):
                if self.has_asset_product_line:
                    self.create_asset_custody_lines()
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
                product_lines = storable_product_lines + consu_product_not_asset_lines
                if product_lines:
                    move_vals = []
                    for line in product_lines:
                        move_vals.append((0, 0, {
                            "product_id": line.product_id.id,
                            "name": line.product_id.name,
                            "product_uom": line.product_id.uom_id.id,
                            'product_uom_qty': line.qty,

                        }))
                        line.qty_purchased = 0
                    picking_vals = {
                        "picking_type_id": self.env.ref('purchase_custom_stock.stock_picking_type_stock').id,
                        "origin": self.name,
                        "location_id": self.location_id.id,
                        "location_dest_id": picking_id.default_location_dest_id.id,
                        'move_lines': move_vals,
                    }
                    picking_id = self.env['stock.picking'].create(picking_vals)
                    self.picking_id = picking_id.id
                if self.has_asset_product_line:
                    self.create_asset_custody_lines()
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
            'res_id': self.picking_id.id,
            'type': 'ir.actions.act_window',
            'target': 'current',
        }

    def action_available_qty(self):
        for rec in self:
            for line in rec.line_ids:
                if line.product_id.asset_ok:
                    asset_count = self.env['account.asset'].search_count([
                        ('product_id', '=', line.product_id.id),
                        ('status', 'in', ['new', 'available']), ('asset_type', '=', 'purchase')
                    ])
                    line.available_qty = asset_count
                    line.qty_purchased = line.qty - asset_count
                else:
                    if not rec.location_id:
                        raise ValidationError(_("Please Insert Location first"))
                    line.available_qty = self.env['stock.quant'].search(
                        [('product_id', '=', line.product_id.id), ('location_id', '=', rec.location_id.id)],
                        limit=1).available_quantity
                    line.qty_purchased = line.qty - line.available_qty

    def write(self, vals):
        """Ovveride Send Notification On state"""
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
                # stock_group = self.env.ref('stock.group_stock_manager')
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
                    # self.message_post(body=body,
                    #                   message_type='notification',
                    #                   author_id=self.env.user.partner_id.id, sticky=True,
                    #                   subtype_id=self.env.ref("mail.mt_comment").id,
                    #                   partner_ids=[stock_employee.user_id.partner_id.id])
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
                        # self.message_post(body=body,
                        #                   message_type='notification',
                        #                   author_id=self.env.user.partner_id.id, sticky=True,
                        #                   subtype_id=self.env.ref("mail.mt_comment").id,
                        #                   partner_ids=[user.partner_id.id])
            elif vals['state'] == 'employee':
                if self.sudo().employee_id and self.sudo().employee_id.user_id:
                    if self.env.user.partner_id.lang == 'ar_001':
                        body = 'عزيزى  %s يرجى تاكيد استلامك على  %s ' % (self.sudo().employee_id.name, self.name)
                    else:
                        body = 'Dear %s please confirm Your receipt on %s ' % (self.sudo().employee_id.name, self.name)

                    self.message_notify(body=body,
                                        partner_ids=[self.sudo().employee_id.user_id.partner_id.id])
                    # self.message_post(
                    #     body=body,
                    #     message_type='notification',
                    #     author_id=self.env.user.partner_id.id, sticky=True,
                    #     subtype_id=self.env.ref("mail.mt_comment").id,
                    #     partner_ids=[self.sudo().employee_id.user_id.partner_id.id])
        return res

    def create_asset_operation(self):
        self.ensure_one()
        AssetOperation = self.env['account.asset.operation']
        operations_created = False
        for asset in self.asset_request_line_ids:
            exists = AssetOperation.search_count([
                ('purchase_request_id', '=', self.id),
                ('type', '=', 'assignment'),
                ('asset_id', '=', asset.asset_id.id),
                ('state', '!=', 'cancel')
            ])
            if exists:
                continue
            data = {
                'date': self.date,
                'asset_id': asset.asset_id.id,
                'return_date': asset.return_date,
                'type': 'assignment',
                'custody_type': asset.custody_type,
                'custody_period': asset.custody_period,
                'state': 'draft',
                'user_id': self.env.uid,
                'new_employee_id': self.employee_id.id,
                'new_department_id': self.department_id.id,
                'purchase_request_id': self.id,

            }
            AssetOperation.create(data)
            operations_created = True
        return operations_created

    def create_asset_custody_lines(self):
        Asset = self.env['account.asset']
        CustodyLine = self.env['asset.custody.line']
        custody_lines = []
        products_with_issues = []

        existing_asset_ids = self.asset_request_line_ids.mapped('asset_id.id')

        for line in self.line_ids.filtered(lambda l: l.product_id.asset_ok):
            required_qty = int(line.qty)

            already_assigned = CustodyLine.search_count([
                ('purchase_request_id', '=', self.id),
                ('asset_id.product_id', '=', line.product_id.id)
            ])
            remaining_qty = required_qty - already_assigned
            if remaining_qty <= 0:
                continue
            available_assets = Asset.search([
                ('product_id', '=', line.product_id.id),
                ('status', 'in', ['new', 'available']),
                ('asset_type', '=', 'purchase'),
                ('id', 'not in', existing_asset_ids)
            ], limit=remaining_qty)

            if not available_assets:
                products_with_issues.append(line.product_id.name)
                continue

            for asset in available_assets:
                # asset.status = 'reserved'
                custody_lines.append({
                    'purchase_request_id': self.id,
                    'asset_id': asset.id,
                    'type': 'assignment',
                    'custody_type': 'personal',
                    'custody_period': 'temporary',
                    'date': self.date or fields.Date.today(),
                })

        if custody_lines:
            CustodyLine.create(custody_lines)
            self.create_asset_operation()
        if products_with_issues:
            warning_message = _("No available assets found for the following products: {}").format(
                ", ".join(products_with_issues)
            )
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Asset Availability Warning'),
                    'message': warning_message,
                    'sticky': True,
                    'type': 'warning',
                }
            }

        return True

    def asset_operation_release(self):
        for asset in self.asset_request_line_ids:
            data = {
                'name': asset.asset_id.name,
                'date': self.date,
                'asset_id': asset.asset_id.id,
                'type': 'release',
                'custody_type': asset.custody_type,
                'custody_period': asset.custody_period,
                'state': 'draft',
                'user_id': self.env.uid,
                'current_employee_id': self.employee_id.id,
                'new_employee_id': self.employee_id.id,
                'current_department_id': self.department_id.id,
                'purchase_request_id': self.id,

            }
            self.env['account.asset.operation'].create(data)

    def return_account_asset_operation(self):
        self.ensure_one()
        context = {}
        view = self.env.ref('purchase_custom_stock.asset_operation_return_wizard_view_form')
        assigned_operations = self.env['account.asset.operation'].search([
            ('purchase_request_id', '=', self.id),
            ('type', '=', 'assignment'),
            ('state', '=', 'done')
        ])
        released_asset_ids = self.env['account.asset.operation'].search([
            ('purchase_request_id', '=', self.id),
            ('type', '=', 'release'),
            ('state', '!=', 'cancel')
        ]).mapped('asset_id.id')
        available_operations = assigned_operations.filtered(
            lambda op: op.asset_id.id not in released_asset_ids
        )

        operation_vals = []
        for op in available_operations:
            operation_vals.append((0, 0, {
                'name': op.asset_id.name,
                'date': self.date,
                'asset_id': op.asset_id.id,
                'type': 'release',
                'custody_type': op.custody_type,
                'custody_period': op.custody_period,
                'state': 'draft',
                'user_id': self.env.uid,
                'current_employee_id': self.employee_id.id,
                'new_employee_id': self.employee_id.id,
                'current_department_id': self.department_id.id,
                'purchase_request_id': self.id,
            }))
        context['default_purchase_request_id'] = self.id
        context['default_operation_ids'] = operation_vals

        return {
            'name': _('Return Assets'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'asset.operation.return.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': context,
        }


class PurchaseRequestLine(models.Model):
    _inherit = 'purchase.request.line'
    _description = 'purchase request line'

    qty_purchased = fields.Integer(string='Purchase Qty', copy=False)
    qty = fields.Integer(string='Demand Qty')
    available_qty = fields.Integer(string='Available Qty', copy=False)

    @api.constrains('qty')
    def qty_validation(self):
        for rec in self:
            if rec.qty <= 0:
                raise ValidationError(_("Item Quantity MUST be at Least ONE!"))

    @api.constrains('expected_price')
    def expected_price_validation(self):
        for rec in self:
            if rec.request_id.initial_engagement_activate == True and rec.expected_price <= 0:
                raise ValidationError(_("Expected Price MUST be at Least ONE!"))

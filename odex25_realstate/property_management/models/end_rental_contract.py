# -*- coding: utf-8 -*-

from odoo import models, fields, api, exceptions, tools, _


class EndOfRent(models.Model):
    _name = 'end.of.rent'
    _description = "Rental Contract End"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Reference Description")
    date = fields.Date(string="Date", default=fields.Date.context_today)
    contract_state = fields.Selection([('before', 'Before Contract Ending'),
                                       ('after', 'After Contract Ending')], string="Before/After Contract Finishing")
    contract_id = fields.Many2one('rental.contract', string="Contract")
    property_id = fields.Many2one('internal.property', related="contract_id.property_id", string="Property", store=True)
    unit_ids = fields.Many2many('re.unit', related="contract_id.unit_ids", string="Unit/Units")
    state = fields.Selection([('draft', 'Draft'),
                              ('check', 'Checked'),
                              ('done', 'Done'),
                              ('cancel', 'Cancelled')],
                             string='Status', default='draft')
    evacuation_date = fields.Date(string="Evacuation date")
    maintenance = fields.Boolean(string="Need Maintenance ?")
    maintenance_cost = fields.Float(string="Maintenance Cost", compute="_get_total_amount", store=True)
    hand_cost = fields.Float(string="Hand Cost")
    total_amount = fields.Float(string="Total Amount", compute="_get_total_amount", store=True)
    rent_amount = fields.Float(string="Rent Amount", related="contract_id.cal_rent_amount")
    service_amount = fields.Float(string="Service Amount", related="contract_id.service_amount")
    water_amount = fields.Float(string="Water Amount", related="contract_id.water_cost")
    insurance_amount = fields.Float(string="Insurance Amount", related="contract_id.insurance_amount")
    remain_amount = fields.Float(string="Remain Insurance Amount", compute="get_remain_amount", store=True)
    electric_meter = fields.Float(string="Electric Read")
    electric_amount = fields.Float(string="Electric Amount")
    electric_payment_no = fields.Float(string="Electric Payment No")
    end_line_ids = fields.One2many('end.rent.line', 'end_rent_id', string="Damage Line")
    rent_payment_ids = fields.One2many('rent.payment', 'contract_id', related="contract_id.rent_payment_ids")
    user_id = fields.Many2one('res.users', string="Responsible", default=lambda self: self.env.user.id)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    maintenance_id = fields.Many2one('property.management.maintenance', string="Maintenance")
    note = fields.Text(string="Note")
    invoice_id = fields.Many2one('account.move', string="Invoice")

    def _prepare_out_refund_invoice_values(self, end, amount):
        self.contract_id.partner_id.property_account_receivable_id = end.contract_id.accrued_account_id.id
        invoice_vals = {
            'ref': end.name,
            'move_type': 'out_refund',
            'invoice_origin': _('Insurance Refund') + ' ' + end.name + ' ' + end.contract_id.partner_id.name,
            'invoice_user_id': end.user_id.id,
            'invoice_date': end.date,
            'narration': end.note,
            'partner_id': end.contract_id.partner_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': end.name + ' - ' + str(end.date),
                'price_unit': amount,
                'quantity': 1.0,

            })],
        }
        return invoice_vals

    def _prepare_invoice_values(self, end, amount):
        self.contract_id.partner_id.property_account_receivable_id = end.contract_id.debit_account_id.id
        invoice_vals = {
            'ref': end.name,
            'move_type': 'out_invoice',
            'invoice_origin': _('Maintenance For') + ' ' + end.name + ' ' + end.contract_id.partner_id.name,
            'invoice_user_id': end.user_id.id,
            'invoice_date': end.date,
            'narration': end.note,
            'partner_id': end.contract_id.partner_id.id,
            'invoice_line_ids': [(0, 0, {
                'name': end.name + ' - ' + str(end.date),
                'price_unit': amount,
                'quantity': 1.0,
                'account_id': end.contract_id.revenue_account_id.id,

            })],
            'line_ids': [(0, 0, {'account_id': end.contract_id.debit_account_id.id, 'debit': 0.0, 'credit': amount,
                                 'name': end.name + ' - ' + str(end.date),
                                 'quantity': 1}),
                         (0, 0,
                          {'account_id': end.contract_id.accrued_account_id.id, 'debit': amount, 'credit': 0.0,
                           'quantity': 1})]
        }
        return invoice_vals

    @api.depends('insurance_amount', 'total_amount')
    def get_remain_amount(self):
        for rec in self:
            rec.remain_amount = rec.insurance_amount - rec.total_amount

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_cancel(self):
        if self.state not in ['check', 'done']:
            self.write({'state': 'cancel'})

    def action_done(self):
        for rec in self:
            if (rec.remain_amount > 0.0) or (rec.remain_amount > 0.0 and rec.maintenance):
                invoice_vals = rec._prepare_out_refund_invoice_values(rec, rec.remain_amount)
                invoice = self.env['account.move'].sudo().create(invoice_vals).with_user(self.env.uid)
                rec.invoice_id = invoice.id
                rec.write({'state': 'done'})
            elif (rec.insurance_amount == 0.0 or rec.remain_amount == 0.0) and not rec.maintenance:
                rec.write({'state': 'done'})
            elif (rec.insurance_amount == 0.0 or rec.remain_amount == 0.0) and rec.maintenance:
                invoice_vals = rec._prepare_invoice_values(rec, abs(rec.remain_amount))
                invoice = self.env['account.move'].sudo().create(invoice_vals).with_user(self.env.uid)
                if len(invoice.invoice_line_ids) > 1:
                    line_id = invoice.invoice_line_ids[1].id
                    commands = [(2, line_id, 0)]
                    invoice.write({'invoice_line_ids': commands})
                rec.invoice_id = invoice.id
                rec.write({'state': 'done'})

            elif (rec.remain_amount < 0.0) or (rec.remain_amount < 0.0 and rec.maintenance):
                invoice_vals = rec._prepare_invoice_values(rec, abs(rec.remain_amount))
                invoice = self.env['account.move'].sudo().create(invoice_vals).with_user(self.env.uid)
                if len(invoice.invoice_line_ids) > 1:
                    line_id = invoice.invoice_line_ids[1].id
                    commands = [(2, line_id, 0)]
                    invoice.write({'invoice_line_ids': commands})
                rec.invoice_id = invoice.id
                rec.write({'state': 'done'})
            if rec.contract_state == 'before':
                for rent_payment in rec.rent_payment_ids:
                    if rent_payment.due_date > rec.date and rent_payment.state != 'paid':
                        rent_payment.write({'state': 'cancel'})
                    elif rent_payment.due_date < rec.date and rent_payment.state != 'paid':
                        rent_payment.write({'state': 'cancel'})
            for unit in rec.contract_id.unit_ids:
                unit.write({'state': 'available'})
            rec.contract_id.write({'state': 'close'})

    def action_check(self):
        for rec in self:
            if rec.contract_state == 'before':
                for rent_payment in rec.rent_payment_ids:
                    if rent_payment.state == 'due':
                        raise exceptions.ValidationError(_('You have Payment in due state, kindly review them first.'))

            if not rec.maintenance_id and rec.maintenance:
                vals = {
                    'name': _('Maintenance for EOC to %s') % rec.contract_id.name,
                    'contract_id': rec.contract_id.id,
                    'property_id': rec.property_id.id,
                    'unit_ids': [(4, unit.id) for unit in rec.unit_ids],
                    'end_line_ids': [(4, line.id) for line in rec.end_line_ids],
                    'partner_id': rec.contract_id.partner_id.id,
                    'end_rent_id': rec.id,
                    'maintenance_type': 'end_contract',
                    'hand_cost': rec.hand_cost,
                    'total_amount': rec.hand_cost + rec.maintenance_cost,
                    'date': rec.date,
                    'state': 'draft', }
                maintenance_id = self.env['property.management.maintenance'].create(vals)
                rec.maintenance_id = maintenance_id.id
        self.write({'state': 'check'})

    @api.depends('maintenance_cost', 'hand_cost', 'end_line_ids', 'end_line_ids.total')
    def _get_total_amount(self):
        for rec in self:
            if rec.end_line_ids:
                rec.maintenance_cost = sum([line.total for line in rec.end_line_ids])
            rec.total_amount = rec.maintenance_cost + rec.hand_cost


class EndRentLine(models.Model):
    _name = "end.rent.line"
    _description = "End Of Rent Line"

    end_rent_id = fields.Many2one('end.of.rent', string='End Contract')
    maintenance_id = fields.Many2one('property.management.maintenance', string="Maintenance")
    product_id = fields.Many2one('product.product', string='Description')
    qty = fields.Integer(string='Quantity', default=1)
    cost = fields.Float(string='Cost')
    total = fields.Float(string='Total', compute='get_total', store=True)
    note = fields.Char(string='Note')

    def _get_available_quantity(self, lot_id=None, package_id=None, owner_id=None, strict=False,
                                allow_negative=False):
        self.ensure_one()
        location_id = self.env['stock.location'].search([('usage', '=', 'internal')], limit=1)
        return self.env['stock.quant']._get_available_quantity(self.product_id, location_id, lot_id=lot_id,
                                                               package_id=package_id, owner_id=owner_id, strict=strict,
                                                               allow_negative=allow_negative)

    @api.depends('qty', 'cost')
    def get_total(self):
        for record in self:
            record.total = record.qty * record.cost

    @api.onchange('product_id')
    def onchange_product(self):
        self.cost = self.product_id.standard_price and self.product_id.standard_price > 0 or self.product_id.lst_price


class PropertyManagementMaintenance(models.Model):
    _name = "property.management.maintenance"
    _description = "Property Maintenance"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    @api.onchange('contract_id')
    def onchange_contract_id(self):
        if self.contract_id:
            return {'domain':
                        {'property_id': [('id', '=', self.contract_id.property_id.id)],
                         'unit_ids': [('id', 'in', self.contract_id.unit_ids.ids)]}}
        else:
            if not self.contract_id:
                self.property_id = False
                self.unit_ids = False

    name = fields.Char(string="Description")
    date = fields.Date(string="Date", default=fields.Date.context_today)
    maintenance_type = fields.Selection([('normal', 'Normal'),
                                         ('end_contract', 'End of contract')], string='Maintenance Type',
                                        default='normal')
    end_rent_id = fields.Many2one('end.of.rent', string="Rent End")
    contract_id = fields.Many2one('rental.contract', string="Contract")
    property_id = fields.Many2one('internal.property', string="Property")
    partner_id = fields.Many2one('res.partner', string="Partner", domain=[('is_tenant', '=', True)])
    vendor_id = fields.Many2one('res.partner', string="Vendor")
    unit_ids = fields.Many2many('re.unit', string="Unit/Units")
    maintenance_cost = fields.Float(string="Maintenance Cost", compute="_get_total_amount", store=True)
    total_amount = fields.Float(string="Total Amount", compute="_get_total_amount", store=True)
    hand_cost = fields.Float(string="Hand Cost")
    end_line_ids = fields.One2many('end.rent.line', 'maintenance_id', string="Damage Line")
    user_id = fields.Many2one('res.users', string="Responsible", default=lambda self: self.env.user.id)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    renter_invoice = fields.Boolean(string="Invoice Renter ?")
    note = fields.Text(string="Note")
    state = fields.Selection([('draft', 'Draft'),
                              ('submit', 'Submitted'),
                              ('done', 'Done'),
                              ('cancel', 'Cancel')], string='Status', default='draft')
    invoice_id = fields.Many2one('account.move', string="Invoice")
    request_id = fields.Many2one('sale.order', string="Request Item")

    def action_rest_draft(self):
        self.write({'state': 'draft'})

    @api.onchange('renter_invoice')
    def rest_values(self):
        if self.partner_id:
            self.partner_id = False

    def _prepare_invoice_values(self, maintenance, amount):
        # Check if unit_ids is not empty before accessing the first element
        unit_name = self.unit_ids[0].name if self.unit_ids else ' '
        origin = _(
            'Maintenance Order') + ' ' + maintenance.name + ' ' + self.property_id.name + '  ' + unit_name + ' ' + maintenance.partner_id.name if maintenance.partner_id else \
            _('Maintenance Order') + ' ' + maintenance.name + ' ' + self.property_id.name + '  ' + unit_name + ' ' + maintenance.vendor_id.name
        line_data = []
        for line in maintenance.end_line_ids:
            line_data.append((0, 0, {
                'product_id': line.product_id.id,
                'name': origin + ' - ' + str(maintenance.date),
                'account_id': line.product_id.property_account_expense_id.id,
                'analytic_account_id': maintenance.property_id.account_analy_id.id if maintenance.property_id.account_analy_id else False,
                'quantity': line.qty,
                'price_unit': line.cost,
            }))
        line_data.append((0, 0, {
            'name': _(
                'Hand Cost') + maintenance.name + ' ' + self.property_id.name + '  ' + unit_name + ' ' + maintenance.partner_id.name if maintenance.partner_id else \
                _('Hand Cost') + ' ' + maintenance.name + ' ' + self.property_id.name + '  ' + unit_name + ' ' + maintenance.vendor_id.name,
            'quantity': 1.0,
            'price_unit': self.hand_cost,
            'account_id': maintenance.contract_id.revenue_account_id.id,
            'analytic_account_id': maintenance.property_id.account_analy_id.id if maintenance.property_id.account_analy_id else False,
            # 'tax_ids': [(6, 0, [maintenance.tax_id.id])] if maintenance.tax_id else False,  # Assigning tax_id to tax_ids
        }))
        invoice_vals = {
            'ref': maintenance.name,
            'move_type': 'in_invoice',
            'invoice_origin': origin,
            'invoice_user_id': maintenance.user_id.id,
            'invoice_date': maintenance.date,
            'narration': maintenance.note,
            'partner_id': maintenance.partner_id.id if maintenance.partner_id else maintenance.vendor_id.id,
            'invoice_line_ids': line_data
        }
        return invoice_vals

    def action_submit(self):
        self.write({'state': 'submit'})

    def action_done(self):
        line_ids = []
        for rec in self:
            invoice_vals = rec._prepare_invoice_values(rec, abs(rec.total_amount))
            if rec.end_rent_id and rec.end_rent_id.state != 'done':
                raise exceptions.ValidationError(_('Please confirm end of rent first '))
            # if not rec.end_rent_id:
            invoice = self.env['account.move'].sudo().create(invoice_vals).with_user(self.env.uid)
            rec.invoice_id = invoice.id
            for line in rec.end_line_ids:
                line_ids.append((0, 0, {
                    'product_id': line.product_id.id,
                    'name': rec.name,
                    'product_uom_qty': line.qty,
                    'price_unit': line.cost,

                }))
            #     check_quantity = line._get_available_quantity()
            #     if check_quantity < line.qty:
            #         raise exceptions.ValidationError(_("Required quantity is more than available quantity"))
            # request_vals = {
            #     'partner_id': rec.vendor_id.id,
            #     'date_order': rec.date,
            #     'from_property': True,
            #     'order_line': line_ids,
            #     'name': self.env['ir.sequence'].next_by_code('ir.property') or ('/')
            # }
            # request_id = self.env['sale.order'].sudo().create(request_vals).with_user(self.env.uid)
            rec.write({'state': 'done'})

    def action_cancel(self):
        self.write({'state': 'cancel'})

    @api.model
    def create(self, values):
        if values.get('maintenance_type'):
            if values['maintenance_type'] == 'end_contract' and self.env.context.get(
                    'active_model') == 'property.management.maintenance':
                raise exceptions.ValidationError(_("End of contract maintenance cannot be created from here."))
        return super(PropertyManagementMaintenance, self).create(values)

    @api.depends('maintenance_cost', 'hand_cost')
    def _get_total_amount(self):
        for rec in self:
            if rec.end_line_ids:
                rec.maintenance_cost = sum([line.total for line in rec.end_line_ids])
            rec.total_amount = rec.maintenance_cost + rec.hand_cost

    @api.depends('maintenance_cost', 'hand_cost', 'end_line_ids', 'end_line_ids.cost', 'end_line_ids.total')
    def _get_total_amount(self):
        for rec in self:
            # تأكد من إعادة حساب maintenance_cost باستخدام المجموع الصحيح لجميع الأسطر
            rec.maintenance_cost = sum(line.total for line in rec.end_line_ids)
            rec.total_amount = rec.maintenance_cost + rec.hand_cost

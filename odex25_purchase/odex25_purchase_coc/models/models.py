# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime
from odoo.exceptions import ValidationError


class POCustom(models.Model):
    _inherit = 'purchase.order'

    need_coc = fields.Boolean(string='Need CoC?')
    coc_id = fields.Many2one(comodel_name='purchase.coc', string='CoC Ref')
    # state = fields.Selection(selection_add=[("coc", "Waiting For CoC")])
    coc = fields.Boolean(string='CoC Created')
    coc_created = fields.Boolean('COC Created')
    coc_ids = fields.One2many(comodel_name='purchase.coc', inverse_name='po_id', string='CoCs')
    coc_count = fields.Integer(string='Cocs', compute="_compute_coc_count")

    @api.depends('coc_ids')
    def _compute_coc_count(self):
        for rec in self:
            rec.coc_count = len(rec.coc_ids)
    
    def button_confirm(self):
        super_action = super(POCustom, self).button_confirm()
        service_products = self.order_line.filtered(lambda line: line.product_id.type == "service")
        if service_products:
            self.action_create_coc()
        return super_action

    def action_view_coc(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'CertificateOf Completion',
            'res_model': 'purchase.coc',
            'view_mode': 'tree,form',
            'target': 'current',
            'domain': [('po_id', '=', self.id)],
            'context': {'create': False}
        }

    def action_create_coc(self):
        coc = None
        coc = self.env['purchase.coc'].create({
            'vendor_id': self.partner_id.id,
            'date': datetime.today(),
            'po_id': self.id,
            'state': 'draft'
        })
        for line in self.order_line.filtered(lambda line: line.product_id.type == 'service' and line.choosen == True):
            line.coc_id = coc.id
        self.coc_id = coc.id
        self.coc_created = True

    def action_create_invoice(self):
        for rec in self:
            if rec and rec.coc_ids.filtered(lambda coc: coc.coc_stage == 'before_bill' and coc.state != 'approve'):
                raise ValidationError(_("Sorry You cannot Create Bill untill CoC Created and Approved."))
        return super(POCustom, self).action_create_invoice()

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    coc_id = fields.Many2one('purchase.coc')


class AccountInvoiceCustom(models.Model):
    _inherit = 'account.move'


    def action_post(self):
        if self.move_type == 'in_invoice':
            context = self.env.context
            print("context",context)
            po = self.env['purchase.order'].search([('id', '=', context.get('active_id', False))])
            print(po.coc_ids.filtered(lambda coc: coc.coc_stage == 'befor_bill_valid' and coc.state != 'approve'))
            if po and po.coc_ids.filtered(lambda coc: coc.coc_stage == 'befor_bill_valid' and coc.state != 'approve'):
                raise ValidationError(_("Sorry You cannot Validate Bill untill CoC Created and Approved."))
            else:
                return super(AccountInvoiceCustom, self).action_post()
        else:
            return super(AccountInvoiceCustom, self).action_post()
   
    def action_confirm(self):
        if self.move_type == 'in_invoice':
            context = self.env.context
            print("context",context)
            po = self.env['purchase.order'].search([('id', '=', context.get('active_id', False))])
            print(po.coc_ids.filtered(lambda coc: coc.coc_stage == 'befor_bill_valid' and coc.state != 'approve'))
            if po and po.coc_ids.filtered(lambda coc: coc.coc_stage == 'befor_bill_valid' and coc.state != 'approve'):
                raise ValidationError(_("Sorry You cannot Validate Bill untill CoC Created and Approved."))
            else:
                return super(AccountInvoiceCustom, self).action_confirm()
        else:
            return super(AccountInvoiceCustom, self).action_confirm()

    def action_register_payment(self):
        if self.move_type == 'in_invoice':
            context = self.env.context
            po = self.env['purchase.order'].search([('id', '=', context.get('active_id', False))])
            if po and po.coc_ids.filtered(lambda coc: coc.coc_stage == 'before_payment' and coc.state != 'approve'):
                raise ValidationError(_("Sorry You cannot Pay For This Vendor untill CoC Created and Approved."))
            else:
                return super(AccountInvoiceCustom, self).action_register_payment()
        else:
            return super(AccountInvoiceCustom, self).action_register_payment()
    @api.model
    def create(self, vals):
        if 'res_id' in vals:
            del vals['res_id']
        if 'res_model' in vals:
            del vals['res_model']
        res = super(AccountInvoiceCustom, self).create(vals)
        return res
class PurchaseCoC(models.Model):
    _name = 'purchase.coc'
    _description = 'Purchase CoC'

    name = fields.Char(string='Name')
    coc_stage = fields.Selection(string='CoC Stage', selection=[('before_bill', 'Before Bill'),
                                                                ('befor_bill_valid', 'Before Bill Validation'),
                                                                ('before_payment', 'Before Payment')]
                                                                ,default='before_bill')
    po_id = fields.Many2one(comodel_name='purchase.order', string='Po Ref.')
    vendor_id = fields.Many2one(comodel_name='res.partner', string='Vendor', related="po_id.partner_id")
    date = fields.Date(string='Date')
    note = fields.Text(string='Note')
    state = fields.Selection(string='', selection=[('draft', 'Draft'), ('confirm', 'Confirm'), ('approve', 'Approve'),
                                                   ('cancel', 'Reject')])
    po_line_ids = fields.One2many('purchase.order.line', 'coc_id', string='PO Lines')
    reject_reason = fields.Char(string='Reject Reason')

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code(self._name)
        return super(PurchaseCoC, self).create(vals)

    def action_confirm(self):
        self.write({
            'state': 'confirm'
        })

    def action_approve(self):
        self.write({
            'state': 'approve'
        })
        # This code is commented because the exchange request module is not needed and
        # will cause a problem when we uninstall the exchange request module
        # if self.po_id and self.po_id.requisition_id and self.po_id.requisition_id.exchange_request:
        #     self.po_id.requisition_id.exchange_request.write({
        #         'state' : 'done'
        #     })

    def action_cancel(self):
        if self.env.context['lang'] in['ar_SY','ar_001']:
            action_name = 'حدد سبب الرفض'
        else:
            action_name = 'Specify Reject Reason'
        return {
            'type': 'ir.actions.act_window',
            'name': action_name,
            'res_model': 'reject.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_origin': self.id, 'default_origin_name': self._name}
        }

    def cancel(self):
        self.write({
            'state': 'cancel',
            'reject_reason': self.env.context.get('reject_reason')
        })
        self.po_id.message_post(body=_(
            'Coc Rejected By %s .  With Reject Reason : %s' % (str(self.env.user.name), str(self.reject_reason))))

    def action_draft(self):
        self.write({
            'state': 'draft'
        })


class RejectWizard(models.TransientModel):
    _name = 'reject.wizard.coc'

    origin = fields.Integer('')
    reject_reason = fields.Text(string='Reject Reson')
    origin_name = fields.Char('')

    def action_reject(self):
        origin_rec = self.env[self.origin_name].sudo().browse(self.origin)
        if dict(origin_rec._fields).get('reject_reason') == None:
            raise ValidationError(_('Sorry This object have no field named Selection Reasoon'))
        else:
            return origin_rec.with_context({'reject_reason': self.reject_reason}).cancel()

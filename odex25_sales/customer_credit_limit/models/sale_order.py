# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    allow = fields.Boolean(string='Allow Sale')
    credit_limit = fields.Float(string='Credit Limit', related='partner_id.credit_limit')
    customer_balance = fields.Float(string='Customer Balance', readonly=True)

    def write(self, vals):
        if 'partner_id' in vals:
            partner = self.env['res.partner'].browse(vals['partner_id'])
            self.customer_balance = partner.credit - partner.debit
        return super(SaleOrder, self).write(vals)

    @api.onchange('partner_id')
    def get_allow_sale(self):
        self.allow = self.partner_id.allow

    def _action_confirm(self):
        for rec in self:
            if not rec.allow:
                if rec.partner_id.block and not rec.partner_id.allow and rec.partner_type == 'postpaid':
                    raise ValidationError(
                        _("This Partner Is Blocked From Doing Sale Due To Delay In Payments,To Unlock It Stop Block From Sale Order Or Customer Profile"))
                if rec.partner_id.credit_limit > 0 and rec.partner_type == 'postpaid':
                    last_total = rec.partner_id.credit + rec.amount_total
                    limit = rec.partner_id.credit_limit - rec.partner_id.credit
                    msg = (_("You Can Create Orders With Total %d")) % limit if limit > 0 else (
                        _(" You Need To Pay Old Invoices "))
                    if rec.partner_id.credit >= rec.partner_id.credit_limit or last_total > rec.partner_id.credit_limit:
                        raise ValidationError(
                            _("This Partner Has limit Credit Which Is %s ,%s") % (rec.partner_id.credit_limit, msg))
        return super(SaleOrder, self)._action_confirm()

    @api.constrains('discount_amount')
    def check_discount_value(self):
        percent_limit = 0.0
        amount_limit = 0.0
        if self.amount_untaxed:
            percent = (self.discount_amount / self.amount_untaxed) * 100

        if self.env.user.has_group('customer_credit_limit.discount_firt_level'):
            percent_limit = float(self.env['ir.config_parameter'].sudo().get_param('percent_limit_a'))
            amount_limit = float(self.env['ir.config_parameter'].sudo().get_param('amount_limit_a'))

        elif self.env.user.has_group('customer_credit_limit.discount_second_level'):
            percent_limit = float(self.env['ir.config_parameter'].sudo().get_param('percent_limit_b'))
            amount_limit = float(self.env['ir.config_parameter'].sudo().get_param('amount_limit_b'))

        elif self.env.user.has_group('customer_credit_limit.discount_third_level'):
            percent_limit = float(self.env['ir.config_parameter'].sudo().get_param('percent_limit_c'))
            amount_limit = float(self.env['ir.config_parameter'].sudo().get_param('amount_limit_c'))

        elif self.env.user.has_group('customer_credit_limit.discount_fourth_level'):
            percent_limit = float(self.env['ir.config_parameter'].sudo().get_param('percent_limit_d'))
            amount_limit = float(self.env['ir.config_parameter'].sudo().get_param('amount_limit_d'))

        if self.discount_method == 'per' and self.discount_amount > percent_limit:
            raise ValidationError(_('You cannot exceed percent limit which is %s.') % percent_limit)

        if self.discount_method == 'fix':
            if self.discount_amount > amount_limit:
                raise ValidationError(_('You cannot exceed amount limit which is %s .') % amount_limit)

            elif percent > percent_limit:
                raise ValidationError(_('You cannot exceed amount limit which is %s .') % percent_limit)

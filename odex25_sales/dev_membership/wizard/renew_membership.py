# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################
from odoo import api, fields, models, _
from dateutil.relativedelta import relativedelta
from datetime import datetime
from odoo.exceptions import ValidationError


class RenewMembership(models.TransientModel):
    _name = "renew.membership"
    _description = "Renew Membership"
    
    
    @api.model
    def default_get(self, fields_list):
        res = super(RenewMembership,self).default_get(fields_list)
        active_id = self._context.get('active_id')
        membership = self.env['dev.membership'].browse(active_id)
        if membership:
            res.update({
                'membership_id':membership.id or False,
                'product_id':membership.product_id and membership.product_id.id or False,
                'duration':membership.duration,
                'interval':membership.interval,
                'from_date':membership.to_date + relativedelta(days=+1)
            })
        return res
        

    membership_id = fields.Many2one('dev.membership', string='Expire Membership')
    product_id = fields.Many2one('product.product', string='Membership', required=True, domain="[('is_membership', '=', True)]")
    from_date = fields.Date('Join Date', required='1')
    membership_fees = fields.Float('Membership Fees')
    duration = fields.Integer(string="Duration")
    interval = fields.Selection(string="Interval", selection=([('days', 'Days'),
                                                         ('month', 'Month'),
                                                         ('year', 'Year')]), default='month')
    
    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.write({
                'duration':self.product_id.duration or 0,
                'interval':self.product_id.interval or False,
                'membership_fees':self.product_id.list_price or 0.0,
            })

    @api.constrains('membership_fees')
    def _check_subscription_fee(self):
        for record in self:
            if record.membership_fees < record.product_id.list_price:
                raise ValidationError(_('Membership fees cannot be less than the default value in Setting of membrship type.'))

    @api.onchange('duration')
    def _onchange_duration(self):
        if self.duration and self.interval and self.membership_fees:
            self.membership_fees = self.duration*self.membership_fees
    @api.constrains('duration')
    def _check_duration(self):
        for record in self:
            if  record.product_id.duration==1 and record.membership_fees < record.product_id.list_price :
                raise ValidationError(_('Membership fees cannot be less than the default value in Setting of membrship type.'))
            elif record.product_id.duration>1 and  record.membership_fees*record.duration < record.product_id.list_price*record.duration :
                raise ValidationError(_('Membership fees cannot be less than the default value in Setting of membrship type.'))


    def action_renew_membership(self):
        mem_pool = self.env['dev.membership'].sudo()
        new_membership = mem_pool.create({
            'partner_id':self.membership_id.partner_id and self.membership_id.partner_id.id or False,
            'product_id':self.product_id and self.product_id.id or False,
            'membership_fees':self.membership_fees or 0.0,
            'duration':self.duration or 0.0,
            'from_date':self.from_date or False,
            'description':self.product_id and self.product_id.description or '',
        })
        if new_membership:
            new_membership.onchange_from_date()
            self.membership_id.membership_id = new_membership.id
                                                         

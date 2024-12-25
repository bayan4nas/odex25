# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

from odoo import fields, models, api,_
from datetime import datetime


class Partner(models.Model):
    _inherit = 'res.partner'

    is_member = fields.Boolean(string='Is Member')
    membership_count = fields.Integer(string="Membership Count", compute="_get_membership_count")
    active_membership_id = fields.Many2one('dev.membership', string='Membership', compute='check_active_membership')
    membrship_level = fields.Many2one('membership.level',string='Membrship level',store=True,compute='_compute_membership_level')
    nationality_id = fields.Many2one('res.country', string="Nationality",default=lambda self: self.env.user.company_id.country_id)
    is_membership_expire = fields.Boolean('Expire Membership',store=True, compute='check_active_membership')
    memebership_status = fields.Char('Membership Status',store=True,compute='check_memebership_status')
    membrship_no = fields.Char('Membership Number')
    birth_date  = fields.Date(string='Birth Date')
    join_date  = fields.Date(string='Join Date')
    memebership_end_date  = fields.Date(string='Memebership End Date',store=True, compute='check_active_membership')
    age = fields.Integer(string='Age',compute='_compute_age')
    employer  = fields.Char(string='Employer',)
    product_id = fields.Many2one('product.product', string="Membership Type",store=True,compute="check_active_membership")
    gender = fields.Selection(
        selection=[("male", "Male"), ("female", "Female")], default="male",string='Gender'
    )
    @api.depends('birth_date')
    def _compute_age(self):
        for rec in self:
            rec.age = 0
            if rec.birth_date:
                rec.age = (datetime.today().year-rec.birth_date.year)


    def check_active_membership(self):
        for partner in self:
            partner.active_membership_id = False
            partner.is_membership_expire = False
            partner.memebership_end_date = False
            partner.product_id = False
            if partner.membership_count > 0:
                c_date = datetime.now().date()
                membership_id = self.env['dev.membership'].sudo().search([('partner_id', '=', partner.id),('state', '=', 'active'),('from_date', '<=', c_date), ('to_date', '>=', c_date)], order='to_date desc', limit=1)
                if membership_id:
                    partner.active_membership_id = membership_id and membership_id.id or False
                    last_membership_id = self.env['dev.membership'].sudo().search([
                        ('partner_id', '=', partner.id),
                        ('state', '=', 'active'),
                        ('product_id', '=', membership_id.product_id.id)], order='to_date desc', limit=1)
                    if last_membership_id:
                        partner.memebership_end_date = last_membership_id.to_date
                        partner.product_id = last_membership_id.product_id.id
                else:
                    partner.is_membership_expire = True
                    last_membership_id = self.env['dev.membership'].sudo().search([('partner_id', '=', partner.id),('state', 'in', ('expire', 'cancel'))], order='to_date desc', limit=1)
                    if last_membership_id:
                        partner.memebership_end_date = last_membership_id.to_date
                        partner.product_id = last_membership_id.product_id.id
    @api.depends('active_membership_id')
    def _compute_membership_end(self):
        for partner in self:
            partner.memebership_end_date = False
            if partner.membership_count > 0:
                if partner.active_membership_id:
                	membership_id = self.env['dev.membership'].sudo().search([
                	    ('partner_id', '=', partner.id),
                        ('state', '=', 'active'),
                        ('product_id', '=', partner.active_membership_id.product_id.id)], order='to_date desc', limit=1)
                	if membership_id:
                	    partner.memebership_end_date = membership_id.to_date
                else:
                    membership_id = self.env['dev.membership'].sudo().search([
                	    ('partner_id', '=', partner.id),
                        ('state', 'in', ('expire','cancel'))], order='to_date desc', limit=1)
                    if membership_id:
                	    partner.memebership_end_date = membership_id.to_date
                    
    @api.depends('active_membership_id')             
    def _compute_membership_level(self):
        for partner in self:
            partner.membrship_level = False
            if partner.membership_count > 0:
                membership_id = self.env['dev.membership'].sudo().search([
                	    ('partner_id', '=', partner.id),
                	    ('state', 'in', ('active','expire','cancel'))], order='to_date desc', limit=1)
                if membership_id:
                        partner.membrship_level = membership_id.membrship_level

    @api.depends('active_membership_id')
    def check_memebership_status(self):
        for partner in self:
            partner.memebership_status = ''
            if partner.membership_count == 0:
                partner.memebership_status = (_('No Membership'))
            else:
                if partner.active_membership_id:
                    partner.memebership_status = partner.active_membership_id.product_id.name
                else:
                    last_membership = self.env['dev.membership'].search(
                        [('partner_id', '=', partner.id)], order='to_date desc', limit=1)

                    if last_membership:
                        if last_membership.state == 'draft':
                            partner.memebership_status = (_('Membership Waiting'))
                        elif last_membership.state == 'cancel':
                            partner.memebership_status = (_('Membership Cancelled'))
                        elif last_membership.state == 'confirm':
                            if not last_membership.invoice_id and not last_membership.is_free:
                                partner.memebership_status = (_('Membership Waiting for Invoice'))
                            elif last_membership.invoice_id.payment_state in ['paid', 'in_payment']:
                                partner.memebership_status = (_('Membership Paid'))
                            elif last_membership.invoice_id.payment_state not in ['paid', 'in_payment']:
                                partner.memebership_status = (_('Membership Waiting for Payment'))
                    # If no active or draft memberships exist, check for expiration
                    if not partner.memebership_status and partner.is_membership_expire:
                        partner.memebership_status = (_('Membership Expire'))


    
    def _get_membership_count(self):
        for rec in self:
            membership_count = self.env['dev.membership'].search_count([('partner_id', '=', rec.id)])
            rec.membership_count = membership_count

    def view_membership(self):
        ctx = dict(create=False, search_default_state=1)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Membership',
            'res_model': 'dev.membership',
            'domain': [('partner_id', '=', self.id)],
            'view_mode': 'tree,form',
            'target': 'current',
            'context': ctx,
        }

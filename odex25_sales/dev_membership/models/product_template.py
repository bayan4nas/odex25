# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

from odoo import fields,api, models,_


class ProductTemplate(models.Model):
    _inherit = "product.template"
    _order='sequence_no'

    type_no = fields.Char("Number",  tracking=True,copy=False)
    sequence_no = fields.Integer(string="Sequence", help="Define the display order")
    company_id = fields.Many2one('res.company', string='Company', readonly=True,
        default=lambda self: self.env.company)
    gender = fields.Selection(
        selection=[("male", "Male"), ("female", "Female")], default="male",string='Gender')

    membership_benefits = fields.Text(
        string="Membership Benefits",
        required=False)
    is_membership = fields.Boolean(string="Is Membership")
    duration = fields.Integer(string="Duration")
    interval = fields.Selection(string="Interval", selection=([('days', 'Days'),
                                                               ('month', 'Month'),
                                                               ('year', 'Year')]), default='year')

    membership_count = fields.Integer(string="Membership Count", compute="_get_membership_count")
    is_free = fields.Boolean(string="Is Free")
    nominee = fields.Boolean(string="Nominee")
    join_period = fields.Integer(string="Join Period")
    nationality_ids = fields.Many2many('res.country', 'country_group_rel', 'devmember_id', 'country_id', 'Nationality')
    age = fields.Integer(string="Age", default=18)
    max_age = fields.Integer(string="Max Age", default=55)

    
    def view_membership(self):
        ctx = dict(create=False)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Membership',
            'res_model': 'dev.membership',
            'domain': [('product_id.name', '=', self.name)],
            'view_mode': 'tree,form',
            'target': 'current',
            'context': ctx,
        }

    def _get_membership_count(self):
        for rec in self:
            membership_count = self.env['dev.membership'].search_count([('product_id.name', '=', rec.name)])
            rec.membership_count = membership_count
            
    @api.model
    def default_get(self, fields):
        res = super(ProductTemplate, self).default_get(fields)
        company_nationality = self.env.user.company_id.country_id
        if 'nationality_id' in fields and company_nationality:
            res['nationality_id'] = company_nationality.id
        return res
# todo end
class ProductProduct(models.Model):
    _inherit = "product.product"

    def view_membership(self):
        ctx = dict(create=False)
        return {
            'type': 'ir.actions.act_window',
            'name': 'Membership',
            'res_model': 'dev.membership',
            'domain': [('product_id.name', '=', self.name)],
            'view_mode': 'tree,form',
            'target': 'current',
            'context': ctx,
        }

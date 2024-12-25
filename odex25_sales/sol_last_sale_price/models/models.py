# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class SO(models.Model):
    _inherit = "sale.order"
    
    @api.onchange("partner_id")
    def _get_last_sale_price_order(self):
        self.order_line._get_last_sale_price()
    
    @api.model_create_multi
    @api.returns('self', lambda value: value.id)
    def create(self, vals_list):
        res = super(SO, self).create(vals_list)
        res._get_last_sale_price_order()
        return res

class SOL(models.Model):
    _inherit = "sale.order.line"
    
    last_sale_price = fields.Float("Last UP", readonly=True)
    
    @api.onchange("product_id")
    def _get_last_sale_price(self):
        for sol in self:
            last_sol = self.sudo().search([('product_id','=',sol.product_id.id),
                                    ('order_partner_id','=',sol.order_partner_id.id),
                                    ('company_id','in',(self.env.user.company_id.id,False)),
                                    ('order_id.state','in',('sale','done'))],order="id desc",limit=1)
            
            if last_sol:
                sol.last_sale_price = last_sol.currency_id._convert(last_sol.price_unit,sol.currency_id,sol.company_id,fields.Date.today())
            else :
                sol.last_sale_price = False
                
    @api.model_create_multi
    @api.returns('self', lambda value: value.id)
    def create(self, vals_list):
        res = super(SOL, self).create(vals_list)
        res._get_last_sale_price()
        return res
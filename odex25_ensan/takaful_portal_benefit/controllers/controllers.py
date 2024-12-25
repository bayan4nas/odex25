# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class TakafulWebsite(http.Controller):
    
    @http.route('/complete_info', type='http', auth='public', website=True)
    def complete_info(self, **kw):
        return http.request.render("takaful_portal_benefit.user_data")
    
    @http.route(['/benefit_profile'], type='http', auth="public", website=True)
    def benefit_profile(self, **post):
        benefit = request.env['grant.benefit'].sudo().search([('user_id', '=', request.session.uid)])
        vals = {
            'data': benefit,
        }
        return request.render("takaful_portal_benefit.profile", vals)

    @http.route('/loan', type='http', auth='public', website=True)
    def loan(self, **kw):
        return http.request.render("takaful_portal_benefit.loan")
    
    # Services Routes

    @http.route(['/food_remain'], type='http', auth="public", website=True)
    def food_remain(self, **post):
        foods = request.env['benefit.food.basket'].sudo().search([])
        vals = {
            'foods': foods,
        }
        return request.render("takaful_portal_benefit.benefit_food_remain", vals)
    
    @http.route('/food_basket', type='http', auth='public', website=True)
    def food_basket(self, **kw):
        return http.request.render("takaful_portal_benefit.food_basket")
    
    @http.route('/zakat', type='http', auth='public', website=True)
    def myZakat(self, **kw):
        return http.request.render("takaful_portal_benefit.zakat")
    
    @http.route(['/families_loan'], type='http', auth="public", website=True)
    def families_loan(self, **post):
        families = http.request.env['benefit.loans'].sudo().search([])
        vals = {
            'families': families,
        }
        return request.render("takaful_portal_benefit.families_loan", vals)
    
    @http.route('/clubs', type='http', auth='public', website=True)
    def allClubs(self, **kw):
        return http.request.render("takaful_portal_benefit.my_clubs")
    
    @http.route('/urgent_needs', type='http', auth='public', website=True)
    def urgent_needs(self, **kw):
        return http.request.render("takaful_portal_benefit.urgent_needs")
    
    @http.route('/applications', type='http', auth='public', website=True)
    def applications(self, **kw):
        uom_id = http.request.env['uom.uom'].sudo().search([])
        product_status = http.request.env['item.status'].sudo().search([])
        vals={
            "uom_id":uom_id,
            "product_status":product_status
        }
        return http.request.render("takaful_portal_benefit.apps_furnatures",vals)


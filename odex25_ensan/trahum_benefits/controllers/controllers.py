# -*- coding: utf-8 -*-
# from odoo import http


# class TrahumBenefits(http.Controller):
#     @http.route('/trahum_benefits/trahum_benefits/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/trahum_benefits/trahum_benefits/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('trahum_benefits.listing', {
#             'root': '/trahum_benefits/trahum_benefits',
#             'objects': http.request.env['trahum_benefits.trahum_benefits'].search([]),
#         })

#     @http.route('/trahum_benefits/trahum_benefits/objects/<model("trahum_benefits.trahum_benefits"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('trahum_benefits.object', {
#             'object': obj
#         })

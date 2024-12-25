# -*- coding: utf-8 -*-
# from odoo import http

# class OdexTakafulBase(http.Controller):
#     @http.route('/odex_takaful_base/odex_takaful_base/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/odex_takaful_base/odex_takaful_base/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('odex_takaful_base.listing', {
#             'root': '/odex_takaful_base/odex_takaful_base',
#             'objects': http.request.env['odex_takaful_base.odex_takaful_base'].search([]),
#         })

#     @http.route('/odex_takaful_base/odex_takaful_base/objects/<model("odex_takaful_base.odex_takaful_base"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('odex_takaful_base.object', {
#             'object': obj
#         })
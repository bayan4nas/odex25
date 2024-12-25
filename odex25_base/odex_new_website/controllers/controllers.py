# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class OdexNewWebsite(http.Controller):
    @http.route('/', type='http', auth='public', website=True)
    def home(self, **kw):
        return request.render("odex_new_website.home")
    
    @http.route('/courses', type='http', auth='public', website=True)
    def courses(self, **kw):
        return request.render("odex_new_website.courses")

#     @http.route('/odex_new_website/odex_new_website/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('odex_new_website.listing', {
#             'root': '/odex_new_website/odex_new_website',
#             'objects': http.request.env['odex_new_website.odex_new_website'].search([]),
#         })

#     @http.route('/odex_new_website/odex_new_website/objects/<model("odex_new_website.odex_new_website"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('odex_new_website.object', {
#             'object': obj
#         })

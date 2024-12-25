# -*- coding: utf-8 -*-
from odoo import http

# class Empowerment(http.Controller):
#     @http.route('/empowerment/empowerment/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/empowerment/empowerment/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('empowerment.listing', {
#             'root': '/empowerment/empowerment',
#             'objects': http.request.env['empowerment.empowerment'].search([]),
#         })

#     @http.route('/empowerment/empowerment/objects/<model("empowerment.empowerment"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('empowerment.object', {
#             'object': obj
#         })
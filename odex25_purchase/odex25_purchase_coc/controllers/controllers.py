# -*- coding: utf-8 -*-
from odoo import http

# class OdexPurchaseCoc(http.Controller):
#     @http.route('/odex25_purchase_coc/odex25_purchase_coc/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/odex25_purchase_coc/odex25_purchase_coc/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('odex25_purchase_coc.listing', {
#             'root': '/odex25_purchase_coc/odex25_purchase_coc',
#             'objects': http.request.env['odex25_purchase_coc.odex25_purchase_coc'].search([]),
#         })

#     @http.route('/odex25_purchase_coc/odex25_purchase_coc/objects/<model("odex25_purchase_coc.odex25_purchase_coc"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('odex25_purchase_coc.object', {
#             'object': obj
#         })
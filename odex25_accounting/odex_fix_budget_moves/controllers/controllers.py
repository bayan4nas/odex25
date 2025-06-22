# -*- coding: utf-8 -*-
# from odoo import http


# class OdexFixBudgetMoves(http.Controller):
#     @http.route('/odex_fix_budget_moves/odex_fix_budget_moves/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/odex_fix_budget_moves/odex_fix_budget_moves/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('odex_fix_budget_moves.listing', {
#             'root': '/odex_fix_budget_moves/odex_fix_budget_moves',
#             'objects': http.request.env['odex_fix_budget_moves.odex_fix_budget_moves'].search([]),
#         })

#     @http.route('/odex_fix_budget_moves/odex_fix_budget_moves/objects/<model("odex_fix_budget_moves.odex_fix_budget_moves"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('odex_fix_budget_moves.object', {
#             'object': obj
#         })

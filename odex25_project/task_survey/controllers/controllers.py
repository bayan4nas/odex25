# -*- coding: utf-8 -*-
# from odoo import http


# class TaskSurvey(http.Controller):
#     @http.route('/task_survey/task_survey/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/task_survey/task_survey/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('task_survey.listing', {
#             'root': '/task_survey/task_survey',
#             'objects': http.request.env['task_survey.task_survey'].search([]),
#         })

#     @http.route('/task_survey/task_survey/objects/<model("task_survey.task_survey"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('task_survey.object', {
#             'object': obj
#         })

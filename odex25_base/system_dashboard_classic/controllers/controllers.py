# # -*- coding: utf-8 -*-
# # Part of Odoo. See LICENSE file for full copyright and licensing details.

# from odoo import http, _
# from odoo.http import request
# from odoo.tools.safe_eval import safe_eval


# class BaseDashboard(http.Controller):

#     @http.route(['/system/dashboard'], type='http', auth="user", website=True)
#     def system_dashboard(self, **kw):
#         values = []
#         base = request.env['base.dashbord'].sudo().search([])
       
#         for models in base:
#             for model in models:
#                 for line in model.board_ids:
#                     if request.uid in line.group_id.users.ids:
#                         state_click  = safe_eval(line.state)
#                         state_follow = safe_eval(line.state)

#                         #get only state from list of list ex:[['state', '=', 'confrim']] return draft,so it become record to confrim
#                         state = state_click[-1][-1]
#                         #get state to follow ,which is not in curent state so replace = with !=
#                         state_follow [-1][-2] = '!='
                        
#                         state_to_click = request.env[line.model_name].sudo().search_count(state_click)
#                         state_to_follow = request.env[line.model_name].sudo().search_count(state_follow)
#                         values.append({
#                             'type':'user', # to differentiate between user has record to click on or employee has requests to see
#                             'name':line.model_id.name, #  name in card ex: Leave
#                             'user':request.env.user, # user data on user card,use user.name to get his name
#                             'model': line.model_name,# to be passed to js as field res_model
#                             'count_state_click':state_to_click, #count of state to click on card
#                             'count_state_follow':state_to_follow,#count of state to follow on card
#                             'state': 'records to ' + '' + state, # title of card ex:records to confirm 
#                             'domain_to_click': state_click, # to be passed to js for his records on field called domain on action window
#                             'domain_to_follow':state_follow ,  # to be passed to js for records to follow up on field called domain on action window
#                        })

#                     #if user has no record to click but needs to create new records or see his requests
#                     else:
#                         values.append({
#                             'type':'service',
#                             'name':line.model_id.name,
#                             'user':request.env.user,
#                             'model': line.model_name, 

#                         })

        
#         print("values========================",values)
#         return request.render("system_dashboard.portal_template", {'values':values})

        
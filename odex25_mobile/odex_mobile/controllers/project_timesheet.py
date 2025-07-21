# -*- coding: utf-8 -*-
import werkzeug
from odoo import http,tools
from datetime import datetime
from odoo.http import request, Response
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.exceptions import UserError
import base64
from ..validator import validator
from ..http_helper import http_helper
import json
import logging
import calendar
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
_logger = logging.getLogger(__name__)
import re
from odoo.tools.translate import _

class ProjectController(http.Controller):
    # Project
    @http.route(['/rest_api/v1/projects'], type='http', auth='none', csrf=False, methods=['GET'])
    def get_project(self, **kw):
        http_method, body, headers, token = http_helper.parse_request()
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])
        user = validator.verify(token)
        if not user:
            return http_helper.response(code=400,message=_("You are not allowed to perform this operation. please check with one of your team admins"),success=False)
        try:
            # projects = http.request.env['project.project'].search(['|',('privacy_visibility', '=', 'employees'),('members','in',user.id)])
            projects = http.request.env['project.project'].search([])
            li = []
            if projects:
                for pro in projects:
                    value = {'id':pro.id,'name':pro.name,}
                    li.append(value)
            return http_helper.response(message="Data Found", data={'projects':li})
        except Exception as e:
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)


    # Task
    @http.route(['/rest_api/v1/projects/<string:project_id>/tasks'], type='http', auth='none', csrf=False, methods=['GET'])
    def get_task(self, project_id,**kw):
        http_method, body, headers, token = http_helper.parse_request()
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])
        user = validator.verify(token)
        if not user:
            return http_helper.response(code=400,message=_("You are not allowed to perform this operation. please check with one of your team admins"),success=False)
        try:
            projects = http.request.env['project.project'].search([('id','=',project_id)])
            tasks = projects.sudo().mapped('task_ids')
            li = []
            if tasks:
                for t in tasks:
                    value = {'id':t.id,'name':t.name,'state':t.stage_id.name}
                    li.append(value)
            return http_helper.response(message="Data Found", data={'tasks':li})
        except Exception as e:
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)


    # Timesheet

    @http.route(['/rest_api/v1/timesheets'], type='http', auth='none', csrf=False, methods=['GET'])
    def get_timesheet(self,approvel=None,page=None,**kw):
        page = page if page else 1
        page, offset, limit, prev = validator.get_page_pagination(page)
        http_method, body, headers, token = http_helper.parse_request()
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])
        user = validator.verify(token)
        if not  user:
            return http_helper.response(code=400,message=_("You are not allowed to perform this operation. please check with one of your team admins"),success=False)
        employee = http.request.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
        if not employee:
            return http_helper.response(code=400,message=_("You are not allowed to perform this operation. please check with one of your team admins"),success=False)
        try:
            if approvel:
                if user.has_group('hr_timesheet.group_timesheet_manager'):
                    timesheet = http.request.env['hr_timesheet.sheet'].search([('state','!=','draft')],offset=offset,limit=limit)
                    count = http.request.env['hr_timesheet.sheet'].search_count([('state','!=','draft')])
                else:
                    timesheet = False
                    count = 0
            else:
                timesheet = http.request.env['hr_timesheet.sheet'].search([('employee_id','=',employee.id)],offset=offset,limit=limit)
                count = http.request.env['hr_timesheet.sheet'].search_count([('employee_id','=',employee.id)])
            li = []
            if timesheet:
                for t in timesheet:
                    value = {'employee_id':t.employee_id.id,'employee_name':t.employee_id.name,'id':t.id,'employee':t.employee_id.name,'state_name':t.state,'state':validator.get_state_name(t,t.state),'period':t.display_name,'start_date': str(t.date_start),'end_date':str(t.date_end),'total_hours':t.total_time}
                    value['lines'] = False

                    lines = []
                    if t.line_ids:
                        for line in t.timesheet_ids:
                            data = {
                                'id':line.id,
                                'date':str(line.date),
                                'time':line.unit_amount,
                                'project_id':line.project_id.id,
                                'project_name':line.project_id.name,
                                'task_name':line.task_id.name,
                                'task_id':line.task_id.id,
                                'description':line.name,
                            }
                            lines.append(data)
                        value['lines'] = lines
                    li.append(value)
            next = validator.get_page_pagination_next(page, count)
            perv_page = "/rest_api/v1/timesheets?approvel=%s&page=%s" % (approvel, prev) if prev else False
            url = "/rest_api/v1/timesheets?approvel=%s&page=%s" % (approvel, next) if next else False
            data = {'links': {'prev': perv_page, 'next': url, }, 'count': count, 'results': {'timesheets':li,'groups':['group_timesheet_manager']}}
            return http_helper.response(message="Data Found", data=data)
        except Exception as e:
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)


    #         create timesheet

    @http.route(['/rest_api/v1/timesheets'], type='http', auth='none', csrf=False, methods=['POST'])
    def get_create_timesheet(self, **kw):
        data = kw.get('lines',{})
        if data:
            data = json.loads(data)
        http_method, body, headers, token = http_helper.parse_request()
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])
        if not'start_date' or not body['end_date'] :
            return http_helper.response(code=400, message="Enter  Start Date and End Date for Timesheet", success=False)
        # if  not data:
        #     return http_helper.response(code=400, message="Enter All Lines for Timesheet", success=False)
        user = validator.verify(token)
        if not user:
            return http_helper.response(code=400,message=_("You are not allowed to perform this operation. please check with one of your team admins"),success=False)
        employee = http.request.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
        if not employee:
            return http_helper.response(code=400,message=_("You are not allowed to perform this operation. please check with one of your team admins"),success=False)
        try:
            timesheet = http.request.env['hr_timesheet.sheet'].create({
                'employee_id':employee.id,
                'date_start': body['start_date'] ,
                'date_end':body['end_date'],
                'timesheet_ids':[ (0, 0, {
                    'date':l['date'],
                    'employee_id':employee.id,
                    'project_id':l['project_id'],
                    'task_id':l['task_id'] if 'task_id' in l else False,
                    'name':l['description'],
                    'unit_amount':l['time']  if 'time' in l else 0,
                }) for l in data]
            })
            if timesheet:
                li = []
                value = {'id': timesheet.id, 'state': validator.get_state_name(timesheet,timesheet.state),
                         'state_name':timesheet.state,'period': timesheet.display_name,
                         'start_date': str(timesheet.date_start), 'end_date': str(timesheet.date_end),
                         'total_hours':timesheet.total_time}
                lines = []
                value['lines'] = False

                if timesheet.timesheet_ids:
                    for line in timesheet.timesheet_ids:
                        data = {
                            'id': line.id,
                            'date': str(line.date),
                            'time': line.unit_amount,
                            'project_id': line.project_id.id,
                            'project_name': line.project_id.name,
                            'task_name': line.task_id.name,
                            'task_id': line.task_id.id,
                            'description': line.name,
                        }
                        lines.append(data)
                value['lines'] = lines
                li.append(value)
                return http_helper.response(message=_("Created successfully"), data={'timesheets': li})
        except Exception as e:
            http.request._cr.rollback()
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)

        # Edit time sheet

    @http.route(['/rest_api/v1/timesheets/<string:id>'], type='http', auth='none', csrf=False, methods=['PUT'])
    def get_edit_timesheet(self,id, **kw):
        data = kw.get('lines', {})
        if data:
            data = json.loads(data)
        http_method, body, headers, token = http_helper.parse_request()
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])
        if not body['start_date'] or not body['end_date']:
            return http_helper.response(code=400, message=_("Enter Start date and End  Date for Timesheet"), success=False)
        # if not data:
        #     return http_helper.response(code=400, message="Enter Lines for Timesheet", success=False)
        user = validator.verify(token)
        if not user:
            return http_helper.response(code=400,message=_("You are not allowed to perform this operation. please check with one of your team admins"),success=False)
        employee = http.request.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
        if not employee:
            return http_helper.response(code=400,message=_("You are not allowed to perform this operation. please check with one of your team admins"),success=False)
        try:
            timesheet = http.request.env['hr_timesheet.sheet'].search([('id','=',id)],limit=1)
            if timesheet:
                timesheet.write({
                    'employee_id':timesheet.employee_id.id,
                    'date_start': body['start_date'],
                    'date_end': body['end_date'],
                })
                if data:
                    for l in  data:
                        self.get_timesheet_line(timesheet,l)
                li=[]
                value = {'id': timesheet.id, 'state': validator.get_state_name(timesheet,timesheet.state),
                         'state_name':timesheet.state,'period': timesheet.display_name,
                         'start_date': str(timesheet.date_start), 'end_date': str(timesheet.date_end),
                         'total_hours':timesheet.total_time}
                lines = []
                value['lines'] = False
                if timesheet.timesheet_ids:
                    for line in timesheet.timesheet_ids:
                        data = {
                            'id': line.id,
                            'date': str(line.date),
                            'time': line.unit_amount,
                            'project_id': line.project_id.id,
                            'project_name': line.project_id.name,
                            'task_name': line.task_id.name,
                            'task_id': line.task_id.id,
                            'description': line.name,
                        }
                        lines.append(data)
                    value['lines'] = lines
                li.append(value)
                return http_helper.response(message="Updated successfully", data={'timesheets': li})
        except Exception as e:
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)

    def get_timesheet_line(self,sheet,line):
        vals = {
            'date': line['date'],
            'employee_id': sheet.employee_id.id,
            'project_id': line['project_id'],
            'task_id':line['task_id'] if 'task_id' in line else False,
            'name':line['description'] if 'description' in line else False,
            'unit_amount':line['time']  if 'time' in line else 0,
        }
        if  'line_id' in line:
            record = http.request.env['account.analytic.line'].search([('id','=',line['line_id'])],limit=1)
            if record:
                record.write(vals)
        else:
            vals.update({'sheet_id':sheet.id,})
            record = http.request.env['account.analytic.line'].create(vals)



   # Delete time sheet line

    @http.route(['/rest_api/v1/timesheets/<string:timesheetId>/lines/<string:lineId>'], type='http', auth='none', csrf=False, methods=['DELETE'])
    def delete_timesheet_line(self,timesheetId,lineId, **kw):
        http_method, body, headers, token = http_helper.parse_request()
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])
        user = validator.verify(token)
        if not user:
            return http_helper.response(code=400,message=_("You are not allowed to perform this operation. please check with one of your team admins"),success=False)
        employee = http.request.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
        if not employee:
            return http_helper.response(code=400,message=_("You are not allowed to perform this operation. please check with one of your team admins"),success=False)
        try:
            record = http.request.env['account.analytic.line'].search([('id','=',lineId)])
            if record and record.sheet_id.state == 'draft':
                record.unlink()
                return http_helper.response(message=_("Deleted successfully"),data={})
            else:
                return http_helper.response(code=400,message=_("You  can not perform this operation. please check with one of your team admins"),
                                            success=False)
        except Exception as e:
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)


   # Submit time sheet

    @http.route(['/rest_api/v1/timesheets/<string:timesheetId>'], type='http', auth='none', csrf=False, methods=['PATCH'])
    def confirm_timesheet(self,timesheetId,refused=None, **kw):
        http_method, body, headers, token = http_helper.parse_request()
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])
        user = validator.verify(token)
        if not user:
            return http_helper.response(code=400,message=_("You are not allowed to perform this operation. please check with one of your team admins"),success=False)
        employee = http.request.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
        if not employee:
            return http_helper.response(code=400,message=_("You are not allowed to perform this operation. please check with one of your team admins"),success=False)
        try:
            record = http.request.env['hr_timesheet.sheet'].search([('id','=',timesheetId)])
            if record :
                msg = ""
                users = http.request.env['res.users'].sudo().search(
                    [('groups_id', 'in', request.env.ref('hr_timesheet.group_timesheet_manager').ids)])
                if record.state == 'draft':
                    record.action_timesheet_confirm()
                    record.firebase_notification(users)
                    msg = _("Confirm successfully")
                elif record.state == 'confirm' and not refused and user.has_group('hr_timesheet.group_timesheet_manager'):
                    record.action_timesheet_done()
                    record.firebase_notification()
                    msg = _("Approved successfully")
                elif refused and record.state == 'confirm' and user.has_group('hr_timesheet.group_timesheet_manager'):
                    record.action_timesheet_refuse()
                    record.firebase_notification()
                    msg = _("Refused successfully")
                elif record.state in ['done','refuse'] and user.has_group('hr_timesheet.group_timesheet_manager'):
                    record.action_timesheet_draft()
                    record.firebase_notification()
                    msg = _("Reset to Draft successfully")
                else:
                    msg = _("You Do not have access to this operation contact Admin")
                    return http_helper.response(code=400,message=msg,success=False)
                li = []
                value = {'id': record.id,'employee':record.employee_id.name, 'state': validator.get_state_name(record,record.state),
                         'state_name':record.state,'period': record.display_name,
                         'start_date': str(record.date_start), 'end_date': str(record.date_end),
                         'total_hours': record.total_time}
                lines = []
                value['lines'] = False
                if record.timesheet_ids:
                    for line in record.timesheet_ids:
                        data = {
                            'id': line.id,
                            'date': str(line.date),
                            'time': line.unit_amount,
                            'project_id': line.project_id.id,
                            'project_name': line.project_id.name,
                            'task_name': line.task_id.name,
                            'task_id': line.task_id.id,
                            'description': line.name,
                        }
                        lines.append(data)
                    value['lines'] = lines
                li.append(value)
                return http_helper.response(message=msg,data={'timesheets':li})
            else:
                return http_helper.response(code=400,message=_("You  can not perform this operation. please check with one of your team admins"),
                                            success=False)
        except Exception as e:
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)


    @http.route(['/rest_api/v1/timesheets/<string:timesheetId>'], type='http', auth='none', csrf=False, methods=['DELETE'])
    def delete_timesheet(self,timesheetId, **kw):
        http_method, body, headers, token = http_helper.parse_request()
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])
        user = validator.verify(token)
        if not user:
            return http_helper.response(code=400,message=_("You are not allowed to perform this operation. please check with one of your team admins"),success=False)
        employee = http.request.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
        if not employee:
            return http_helper.response(code=400,message=_("You are not allowed to perform this operation. please check with one of your team admins"),success=False)
        try:
            record = http.request.env['hr_timesheet.sheet'].search([('id','=',timesheetId)])
            if record and record.state == 'draft':
                record.unlink()
                return http_helper.response(message=_("Deleted successfully") ,data={})
            else:
                return http_helper.response(code=400,message=_("You  can not perform this operation the state not open. please check with one of your team admins"),
                                            success=False)
        except Exception as e:
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)










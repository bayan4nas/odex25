# -*- coding: utf-8 -*-
import werkzeug
from odoo import http,tools
from odoo.http import request, Response
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.exceptions import UserError, AccessError, ValidationError, Warning
import base64
from ..validator import validator
from ..http_helper import http_helper
import json
import logging
_logger = logging.getLogger(__name__)
import re
from odoo.tools.translate import _

class OverTimeController(http.Controller):
    # overtime get
    
    @http.route(['/rest_api/v1/overtimes/data'], type='http', auth='none', csrf=False, methods=['GET'])
    def get_overtime_datas(self,transfer_type=None, **kw):
        try:
            data = {}
            if transfer_type == 'accounting':
                account = request.env['account.account'].sudo().search([])
                journal = request.env['account.journal'].sudo().search([('type','in',['cash','bank'])])
                data = {'account':account.read(['name','id']),'journal':journal.read(['name','id'])}
            else:
                rules = request.env['hr.salary.rule'].sudo().search([('rules_type', '=', 'overtime')])
                data = {'rules': rules.read(['name', 'id'])}
            if data:
                return http_helper.response(message=_("Data Found  successfully"),
                                            data=data)
            else:
                return http_helper.response(message=_("Data Not Found"),
                                            data=data)
        except Exception as e:
            _logger.error(str(e))
            message = validator.get_server_error(e, request.env.user)
            return http_helper.errcode(code=403, message=message)

    @http.route(['/rest_api/v1/overtimes'], type='http', auth='none', csrf=False, methods=['GET'])
    def get_overtime(self,approvel=None,page=None, **kw):        
        page = page if page else 1
        page, offset, limit, prev = validator.get_page_pagination(page)
        http_method, body, headers, token = http_helper.parse_request()        
        result = validator.verify_token(token)        
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])
        user = validator.verify(token)        
        if not user:
            return http_helper.response(code=400,
                                        message=_("You are not allowed to perform this operation. please check with one of your team admins"),
                                        success=False)
        employee = http.request.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
        if not employee:
            return http_helper.response(code=400,
                                        message=_("You Have issue in your employee profile. please check with one of your team admins"),
                                        success=False)
        try:            
            if approvel:
                domain = [('state','!=','draft')]
                if  user.has_group('hr_base.group_general_manager') or\
                user.has_group('hr_base.group_executive_manager') or user.has_group('hr_base.group_division_manager')or\
                user.has_group('hr_base.group_account_manager') or user.has_group('hr.group_hr_user'):

                    domain = [('state','!=','draft')]

                if not user.has_group('hr_base.group_general_manager') or not \
                user.has_group('hr_base.group_executive_manager') or not user.has_group('hr_base.group_account_manager') or not \
                        user.has_group('hr.group_hr_user'):
                    domain = [('state','!=','draft'),'|',('line_ids_over_time.employee_id.department_id.manager_id.user_id','=', user.id),
                                        ('line_ids_over_time.employee_id.department_id.parent_id.manager_id.user_id','child_of', [user.id])]
                
                overtime = http.request.env['employee.overtime.request'].search(domain, order='request_date desc', offset=offset, limit=limit)
                count = http.request.env['employee.overtime.request'].search_count(domain)
                
                # else:
                #     overtime = False
                #     count = 0
            else:
                overtime = http.request.env['employee.overtime.request'].search([('line_ids_over_time.employee_id', '=', employee.id)], order='request_date desc', offset=offset, limit=limit)
                count = http.request.env['employee.overtime.request'].search_count([('line_ids_over_time.employee_id', '=', employee.id)])
            over = []
            if overtime:
                for s in overtime:
                    value = {'id': s.id, 'transfer_type': s.transfer_type,'request_date':str(s.request_date),'date_from':str(s.date_from), 
                                'date_to':str(s.date_to), 'state_name':s.state,'state':validator.get_state_name(s,s.state),'reason': s.reason, 'overtime_plase': s.overtime_plase,}
                    if approvel:
                        value.update({
                            'account_id': s.sudo().account_id.name if s.sudo().account_id else False,
                            'journal_id': s.sudo().journal_id.name if s.sudo().journal_id else False,
                            'benefits_discounts': s.sudo().benefits_discounts.name if s.sudo().benefits_discounts else False,

                        })
                    li = []
                    emps =[]
                    if s.line_ids_over_time:
                        if approvel:
                            record = s.line_ids_over_time
                        else:
                            record = s.line_ids_over_time.filtered(lambda r:r.employee_id == employee)
                        if record:
                            for r in record:
                                emps.append({ 'employee_id': r.employee_id.id,
                                    'employee_name': r.employee_id.name,})
                                rec = {
                                    'employee_id': r.employee_id.id,
                                    'employee_name': r.employee_id.name,
                                    'id':r.id,
                                    'over_time_workdays_hours':r.over_time_workdays_hours,
                                    'over_time_vacation_hours':r.over_time_vacation_hours,
                                    'daily_hourly_rate':r.daily_hourly_rate,
                                    'holiday_hourly_rate':r.holiday_hourly_rate,
                                    'price_hour':r.price_hour,
                                }

                                li.append(rec)
                    value['lines'] = li
                    value['employees'] = emps
                    over.append(value)
            next = validator.get_page_pagination_next(page, count)
            url = "/rest_api/v1/overtimes?approvel=%s&page=%s" % (approvel, next) if next else False
            prev_url = "/rest_api/v1/overtimes?approvel=%s&page=%s" % (approvel, prev) if prev else False
            data = {'links': {'prev': prev_url, 'next': url, }, 'count': count, 'results': {'overtimes': over,'groups':['group_hr_user','group_account_manager',
                                                'group_executive_manager','group_division_manager','group_general_manager']}}

            return http_helper.response(message="Data Found",
                                            data=data)
        except Exception as e:
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)

    @http.route(['/rest_api/v1/overtimes'], type='http', auth='none', csrf=False, methods=['POST'])
    def create_overtime(self, **kw):        
        data = kw.get('lines', {})
        if data:
            data = json.loads(data)
        http_method, body, headers, token = http_helper.parse_request()
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])
        user = validator.verify(token)
        if not user:
            return http_helper.response(code=400,
                                        message=_("You are not allowed to perform this operation. please check with one of your team admins"),
                                        success=False)
        employee = http.request.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
        if not employee:
            return http_helper.response(code=400,
                                        message=_("You Have issue in your employee profile. please check with one of your team admins"),
                                        success=False)
        if not body.get('reason') :
            return http_helper.response(code=400,
                                        message=_("You need to enter reason"),
                                        success=False)
        if not body.get('transfer_type'):
            return http_helper.response(code=400,
                                        message=_("You need to enter transfer type"),
                                        success=False)
        
        if not body.get('overtime_plase'):
            return http_helper.response(code=400,
                                        message=_("You need to enter overtime plase"),
                                        success=False)


        if not body.get('date_from') or not body.get('date_to') or not body.get('request_date'):
            return http_helper.response(code=400,
                                        message=_("You need to enter request date ,Date from and Date to"),
                                        success=False)
        if not data:
            return http_helper.response(code=400, message=_("Enter Lines for Overtime"), success=False)
        try:
            s = http.request.env['employee.overtime.request'].sudo().create(
                {'transfer_type': body['transfer_type'], 'request_date':body['request_date'], 'date_from': body['date_from'],
                 'date_to': body['date_to'],'reason': body['reason'], 'overtime_plase': body['overtime_plase'],
                 'line_ids_over_time':[ (0, 0, {'employee_id':employee.id,
                                                'over_time_workdays_hours':l['over_time_workdays_hours'],
                                                'over_time_vacation_hours':l['over_time_vacation_hours'],
                                                })for l in data]
                 })
            if s:
                value = {'id': s.id, 'transfer_type': s.transfer_type,'request_date':str(s.request_date),'date_from':str(s.date_from),
                         'date_to':str(s.date_to), 'state_name':s.state,'state':validator.get_state_name(s,s.state),'reason': s.reason, 'overtime_plase': s.overtime_plase}
                li = []
                if s.line_ids_over_time:
                    for r in s.line_ids_over_time:
                        rec = {
                            'id': r.id,
                            'over_time_workdays_hours': r.over_time_workdays_hours,
                            'over_time_vacation_hours': r.over_time_vacation_hours,
                            'price_hour': r.price_hour,
                            'daily_hourly_rate': r.daily_hourly_rate,
                            'holiday_hourly_rate': r.holiday_hourly_rate,
                        }
                        li.append(rec)
                value['lines'] = li

                return http_helper.response(message=_("Overtime created successfully"),
                                            data={'overtimes': [value],})
        except (UserError, AccessError, ValidationError, Warning) as e:
            error = str(e.name) + "\n" + str(e)
            return http_helper.response(code=400, message=str(error), success=False)
        except Exception as e:
            http.request._cr.rollback()
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)

        # overtime edit

    @http.route(['/rest_api/v1/overtimes/<string:id>'], type='http', auth='none', csrf=False, methods=['PUT'])
    def edit_overtime(self,id,approvel=None, **kw):
        data = kw.get('lines', {})
        if data:
            data = json.loads(data)
        http_method, body, headers, token = http_helper.parse_request()
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])
        user = validator.verify(token)
        if not user:
            return http_helper.response(code=400,
                                        message=_("You are not allowed to perform this operation. please check with one of your team admins"),
                                        success=False)
        employee = http.request.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
        if not employee:
            return http_helper.response(code=400,
                                        message=_("You Have issue in your employee profile. please check with one of your team admins"),
                                        success=False)
        if not body.get('reason') :
            return http_helper.response(code=400,
                                        message=_("You need to enter reason"),
                                        success=False)
        if not body.get('transfer_type'):
            return http_helper.response(code=400,
                                        message=_("You need to enter transfer type"),
                                        success=False)

        if not body.get('overtime_plase') :
            return http_helper.response(code=400,
                                        message=_("You need to enter overtime plase"),
                                        success=False)

        if not body.get('date_from') or not body.get('date_to') or not body.get('request_date'):
            return http_helper.response(code=400,
                                        message=_("You need to enter request date ,Date from and Date to"),
                                        success=False)
        # if not data:
        #     return http_helper.response(code=400, message=_("Enter Lines for Overtime"), success=False)
        try:
            s = http.request.env['employee.overtime.request'].search([('id', '=', id)])
            if s:
                vals = {'transfer_type': body['transfer_type'], 'request_date':body['request_date'], 'date_from': body['date_from'],
                     'date_to': body['date_to'],'reason': body['reason'],  'overtime_plase': s.overtime_plase,
                     }
                if approvel:
                    if s.transfer_type == 'accounting' and 'account' in body and 'journal' in body:
                        vals.update({
                            'account_id': body['account'],
                            'journal_id': body['journal'],
                        })
                    elif s.transfer_type == 'payroll' and 'rule' in body :
                        vals.update({
                            'benefits_discounts': body['rule'],
                        })
                s.write(vals)
                if s.state == 'hr_aaproval':
                    s.onchange_transfer_type()
                if data:
                    for t in data:
                        self.get_overtime_line(s.employee_id, s, t)
                value = {'id': s.id, 'transfer_type': s.transfer_type,'request_date':str(s.request_date),'date_from':str(s.date_from), 'overtime_plase': s.overtime_plase,
                         'date_to':str(s.date_to), 'state_name':s.state,'state':validator.get_state_name(s,s.state),'reason': s.reason}
                if approvel:
                    value.update({
                        'account_id': s.sudo().account_id.name if s.sudo().account_id else False,
                        'journal_id': s.sudo().journal_id.name if s.sudo().journal_id else False,
                        'benefits_discounts': s.sudo().benefits_discounts.name if s.sudo().benefits_discounts else False,

                    })
                li = []
                if s.line_ids_over_time:
                    for r in s.line_ids_over_time:
                        rec = {
                            'id': r.id,
                            'over_time_workdays_hours': r.over_time_workdays_hours,
                            'over_time_vacation_hours': r.over_time_vacation_hours,
                            'price_hour': r.price_hour,
                            'daily_hourly_rate': r.daily_hourly_rate,
                            'holiday_hourly_rate': r.holiday_hourly_rate,
                        }
                        li.append(rec)
                value['lines'] = li

                return http_helper.response(message=_("Overtime Update successfully"),
                                            data={'overtimes': [value],})
        except Exception as e:
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)

    def get_overtime_line(self,emp,over,t):
        vals = {'employee_id':emp.id,
                'over_time_workdays_hours':t['over_time_workdays_hours'],
                'over_time_vacation_hours':t['over_time_vacation_hours'],
                }
        if  'line_id' in t:
            record = http.request.env['line.ids.over.time'].search([('id','=',t['line_id'])],limit=1)
            if record:
                vals.update({'employee_id':record.employee_id.id,})
                record.write(vals)
        else:
            vals.update({'employee_over_time_id':over.id,})
            record = http.request.env['line.ids.over.time'].create(vals)

        # Delete overtime line

    @http.route(['/rest_api/v1/overtimes/<string:overtimeId>/lines/<string:lineId>'], type='http', auth='none',csrf=False, methods=['DELETE'])
    def delete_overtime_line(self, overtimeId, lineId, **kw):
        http_method, body, headers, token = http_helper.parse_request()
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])
        user = validator.verify(token)
        if not user:
            return http_helper.response(code=400,
                                        message=_("You are not allowed to perform this operation. please check with one of your team admins"),
                                        success=False)
        employee = http.request.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
        if not employee:
            return http_helper.response(code=400,
                                        message=_("You are not allowed to perform this operation. please check with one of your team admins"),
                                        success=False)
        try:
            record = http.request.env['line.ids.over.time'].search([('id', '=',lineId)])
            if record and record.employee_over_time_id.state == 'draft':
                record.unlink()
                return http_helper.response(message=_("Deleted successfully"), data={})
            else:
                return http_helper.response(code=400,
                                            message=_("You are can not perform this operation. please check with one of your team admins"),
                                            success=False)
        except Exception as e:
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)

    @http.route(['/rest_api/v1/overtimes/<string:overtimeId>'], type='http', auth='none', csrf=False, methods=['DELETE'])
    def delete_overtime(self, overtimeId, **kw):
        http_method, body, headers, token = http_helper.parse_request()
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])
        user = validator.verify(token)
        if not user:
            return http_helper.response(code=400,
                                        message=_("You are not allowed to perform this operation. please check with one of your team admins"),
                                        success=False)
        employee = http.request.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
        if not employee:
            return http_helper.response(code=400,
                                        message=_("You are not allowed to perform this operation. please check with one of your team admins"),
                                        success=False)
        try:
            record = http.request.env['employee.overtime.request'].search([('id', '=', overtimeId)])
            if record and record.state == 'draft':
                record.unlink()
                return http_helper.response(message=_("Deleted successfully"), data={})
            else:
                return http_helper.response(code=400,
                                            message=_("You can not perform this operation. please check with one of your team admins"),
                                            success=False)
        except Exception as e:
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)

            # Submit overtime

    @http.route(['/rest_api/v1/overtimes/<string:overtimeId>'], type='http', auth='none', csrf=False,methods=['PATCH'])
    def confirm_overtime(self, overtimeId,refused=None, **kw):
        http_method, body, headers, token = http_helper.parse_request()
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])
        user = validator.verify(token)
        if not user:
            return http_helper.response(code=400,
                                        message=_("You are not allowed to perform this operation. please check with one of your team admins"),
                                        success=False)
        employee = http.request.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
        if not employee:
            return http_helper.response(code=400,
                                        message=_("You are not allowed to perform this operation. please check with one of your team admins"),
                                        success=False)
        try:
            msg = ""
            s = http.request.env['employee.overtime.request'].search([('id', '=', overtimeId)])
            dev = http.request.env['res.users'].sudo().search(
                [('groups_id', 'in', request.env.ref('hr_base.group_division_manager').ids)])
            acc = http.request.env['res.users'].sudo().search(
                [('groups_id', 'in', request.env.ref('hr_base.group_account_manager').ids)])
            gm= http.request.env['res.users'].sudo().search(
                [('groups_id', 'in', request.env.ref('hr_base.group_general_manager').ids)])
            hr = http.request.env['res.users'].sudo().search(
                [('groups_id', 'in', request.env.ref('hr.group_hr_user').ids)])
            if s:
                if not refused:
                    if s.state == 'draft':
                        s.submit()
                        msg = _("Overtime Confirm Successfully")
                        s.firebase_notification(dev)
                    elif s.state =='submit' and user.has_group('hr_base.group_division_manager'):
                        s.direct_manager()
                        msg = _("Overtime approved by direct manager Successfully")
                        s.firebase_notification(acc)
                    elif s.state =='direct_manager' and user.has_group('hr_base.group_account_manager'):
                        s.financial_manager()
                        msg = _("Overtime approved by financial manager Successfully")
                        s.firebase_notification(hr)
                    elif s.state =='financial_manager' and user.has_group('hr.group_hr_user'):
                        s.hr_aaproval()
                        msg = _("Overtime approved by hr  Successfully")
                        s.firebase_notification(gm)
                    elif s.state in ['hr_aaproval', 'executive_office'] and user.has_group('hr_base.group_general_manager') or s.state in ['hr_aaproval', 'executive_office'] and  user.has_group('hr_base.group_executive_manager'):
                        s.validated()
                        msg = _("Overtime approved  Top Manager Successfully")
                    elif s.state in ['refused','validated'] and user.has_group('hr.group_hr_user'):
                        s.re_draft()
                        msg = _("Overtime Reset to draft")
                        s.firebase_notification()
                elif refused:
                    if (s.state == 'direct_manager' and user.has_group('hr.group_hr_user') )or (s.state in['hr_aaproval','financial_manager'] and user.has_group('hr_base.group_general_manager') or \
                    user.has_group('hr_base.group_executive_manager') )or( s.state == 'submit' and user.has_group('hr_base.group_division_manager')) :
                        s.refused()
                        msg = _("Overtime request Refused")
                        s.firebase_notification()
                else:
                    msg = _('You can not access this operation contact your system admin')
                    return http_helper.response(code=400,message=msg,success=False)
                value = {'id': s.id, 'transfer_type': s.transfer_type, 'request_date': str(s.request_date),
                         'date_from': str(s.date_from),
                         'date_to': str(s.date_to),  'state_name':s.state,'state': validator.get_state_name(s, s.state), 'reason': s.reason}
                li = []
                emps = []
                if s.line_ids_over_time:
                    for r in s.line_ids_over_time:
                        emps.append({'employee_id': r.employee_id.id,
                                     'employee_name': r.employee_id.name, })
                        rec = {
                            'employee_id': r.employee_id.id,
                            'employee_name': r.employee_id.name,
                            'id': r.id,
                            'over_time_workdays_hours': r.over_time_workdays_hours,
                            'over_time_vacation_hours': r.over_time_vacation_hours,
                            'price_hour': r.price_hour,
                            'daily_hourly_rate': r.daily_hourly_rate,
                            'holiday_hourly_rate': r.holiday_hourly_rate,
                        }
                        li.append(rec)
                value['lines'] = li
                value['employees'] = emps
                return http_helper.response(message=msg, data={'overtimes': [value]})
            else:
                return http_helper.response(code=400,
                                            message=_("You  can not perform this operation. please check with one of your team admins"),
                                            success=False)
        except Exception as e:
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)


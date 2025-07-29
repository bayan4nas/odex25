# -*- coding: utf-8 -*-
import re
import werkzeug
from odoo import http, tools,fields
from datetime import datetime, tzinfo, timedelta
from odoo.http import request, Response
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.exceptions import UserError ,AccessError, ValidationError
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT

import base64
from ...validator import validator
from ...http_helper import http_helper
# from odoo.addons.odex_mobile.validator import validator
# from odoo.addons.odex_mobile.http_helper import http_helper
import json
import logging
import calendar
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from odoo.tools.translate import _
import pytz

_logger = logging.getLogger(__name__)


class LeaveController(http.Controller):

    def get_attchment(self, res_id):
        attachment = http.request.env['ir.attachment'].sudo().search(
            [('res_model', '=', 'hr.holidays'), ('res_id', '=', res_id.id)])
        li = []
        if attachment:
            url_base = http.request.env['ir.config_parameter'].sudo(
            ).get_param('web.base.url')
            for att in attachment:
                url = url_base + "/api/content/%s" % (att.id)
                li.append(url)
        return li

    def get_return_data(self, hol, approvel=None):

        value = {'id': hol.id,
                 'type': hol.holiday_status_id.name,
                 'type_value': hol.holiday_status_id.id,
                 'reason_msg': hol.reason or "",
                 'alternative_chick': hol.holiday_status_id.alternative_chick,
                 'replacement_id': hol.sudo().replace_by.id if hol.replace_by else False,
                 'replacement_name': hol.sudo().replace_by.name if hol.replace_by else False,
                 'start_date': str(hol.date_from), 'end_date': str(hol.date_to), 'attachment': self.get_attchment(hol),
                 'reason': hol.name, 'state': validator.get_state_name(hol, hol.state), 'state_name': hol.state,
                 'employee_id': hol.employee_id.id, 'employee_name': hol.employee_id.name,
                 'delegated_permission': hol.delegate_acc}
        if hol.issuing_ticket:
            value.update({'issuing_clearance_form': hol.issuing_clearance_form,
                          'issuing_deliver_custdy': hol.issuing_deliver_custdy,
                          'permission_request_for': hol.permission_request_for,
                          'issuing_exit_return': hol.issuing_exit_return,
                        #   'exit_return_duration': hol.number_of_days_temp,
                          'exit_return_duration': hol.exit_return_duration,
                          'ticket_cash_request_type_id': hol.ticket_cash_request_type.id if hol.ticket_cash_request_type else False,
                          'ticket_cash_request_type_name': hol.ticket_cash_request_type.name if hol.ticket_cash_request_type else False,
                          'ticket_cash_request_for': hol.ticket_cash_request_for,
                          'issuing_ticket': hol.issuing_ticket})
        return value

    @http.route(['/rest_api/v2/leaves'], type='http', auth='none', csrf=False, methods=['GET'])
    def get_leaves(self, approvel=None, done=None,  page=None, **kw):
        http_method, body, headers, token = http_helper.parse_request()
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])
        user = validator.verify(token)
        if not user:
            return http_helper.response(code=400, message=_(
                "You are not allowed to perform this operation. please check with one of your team admins"),
                                        success=False)
        employee = http.request.env['hr.employee'].search(
            [('user_id', '=', user.id)], limit=1)
        if not employee:
            return http_helper.response(code=400, message=_(
                "You Have issue in your employee profile. please check with one of your team admins"), success=False)
        try:
            page = page if page else 1
            page, offset, limit, prev = validator.get_page_pagination(page)
            employees = http.request.env['hr.employee'].sudo().search(
                [('department_id', '=', employee.department_id.id), ('state', '=', 'open'), ('id', '!=', employee.id),
                 '|', ('parent_id', '=', employee.id), ('coach_id', '=', employee.id)])
            balance = http.request.env['hr.holidays'].with_user(user.id).search(
                [('employee_id', '=', employee.id), ('type', '=', 'add'), ('check_allocation_view', '=', 'balance'),('remaining_leaves','>',0)])
            my_leave = balance.mapped('holiday_status_id').ids
            status = http.request.env['hr.holidays.status'].search([('id', 'in', my_leave),('leave_type','!=','sick')])
            status_sick = http.request.env['hr.holidays.status'].search([('id', 'in', my_leave),('leave_type','=','sick')],order = 'sickness_severity',limit=1)
            status |=status_sick
            domain = [('state', '!=', 'draft')]
            alternative_employees = http.request.env['hr.employee'].search_read(
                [('state', '=', 'open')], ['name'])
            if approvel:
                holidays = http.request.env['hr.holidays'].with_user(user.id).search(
                    [('state', 'in', ['confirm','validate','approved']), ('employee_id', '!=', employee.id), ('type', '=', 'remove')],
                    offset=offset, limit=limit)
                count = http.request.env['hr.holidays'].with_user(user.id).search_count(
                    [('state', 'in', ['confirm','validate','approved']), ('employee_id', '!=', employee.id), ('type', '=', 'remove')],)
            elif done:
                holidays = http.request.env['hr.holidays'].with_user(user.id).search(
                     [('state', 'in', ['validate1','refuse','cancel']), ('employee_id', '!=', employee.id), ('type', '=', 'remove')],
                    offset=offset, limit=limit)
                count = http.request.env['hr.holidays'].with_user(user.id).search_count(
                     [('state', 'in', ['validate1','refuse','cancel']), ('employee_id', '!=', employee.id), ('type', '=', 'remove')],)
            else:
                holidays = http.request.env['hr.holidays'].with_user(user.id).search(
                    [('employee_id', '=', employee.id), ('type', '=', 'remove')], offset=offset, limit=limit)
                count = http.request.env['hr.holidays'].with_user(user.id).search_count(
                    [('employee_id', '=', employee.id), ('type', '=', 'remove')],)
            ticket_cash_type = http.request.env['hr.ticket.request.type'].search([])
            ticket_cash = []
            if ticket_cash_type:
                for s in ticket_cash_type:
                    value = {'id': s.id, 'name': s.name or ""}
                    ticket_cash.append(value)
            emp = []
            if employees:
                for s in employees:
                    value = {'id': s.id, 'name': s.name or ""}
                    emp.append(value)
            hol_type = []
            if status:
                for s in status:
                    records = balance.filtered(lambda r: r.holiday_status_id == s)
                    value = {
                        "id": s.id,
                        # "name": s.with_context({"employee_id": employee.id}).name_get()[0][1] or "",
                        "name": s.name or "",
                        "ticket": s.issuing_ticket,
                        "balance": records[0].remaining_leaves if records else 0,
                        "alternative_chick": s.alternative_chick,
                    }
                    hol_type.append(value)
            li = []
            if balance:
                for s in balance:
                    value = {
                        "id": s.id,
                        "name": s.holiday_status_id.name or "",
                        "remain": s.remaining_leaves,
                        "total": s.leaves_taken + s.remaining_leaves,
                        "taken": s.leaves_taken,
                    }
                    li.append(value)
            leaves = []
            if holidays:
                for hol in holidays:
                    value = self.get_return_data(hol, approvel)
                    leaves.append(value)

            params = []
            if approvel:
                params.append("approvel=%s" % approvel)
            if done:
                params.append("done=%s" % done)


            next = validator.get_page_pagination_next(page, count)
            # url = "/rest_api/v2/leaves?approvel=%s&page=%s" % (
            #     approvel, next) if next else False
            # prev_url = "/rest_api/v2/leaves?approvel=%s&page=%s" % (
            #     approvel, prev) if prev else False
            url = f"/rest_api/v2/leaves?page={next}&{'&'.join(params)}" if next else False
            prev_url = f"/rest_api/v2/leaves?page={prev}&{'&'.join(params)}" if prev else False
            data = {'links':
                        {'prev': prev_url,
                         'next': url, },
                    'count': count,
                    'results':
                        {'system_leaves': li,
                          "alternative_employees": alternative_employees,
                         'leaves': leaves,
                         'holiday_types': hol_type,
                         'employees': emp,
                         'ticket_cash_type': ticket_cash,
                         # 'groups': ['group_hr_holidays_user', 'group_division_manager']
                         }}
            return http_helper.response(message="Data Found", data=data)
        except (UserError, AccessError, ValidationError, Exception, Warning) as e:
            http.request._cr.rollback()
            error = str(e)
            return http_helper.response(code=400, message=str(error), success=False)
        except Exception as e:
            http.request._cr.rollback()
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)

    @http.route(['/rest_api/v2/leave/<string:id>'], type='http', auth='none', csrf=False, methods=['GET'])
    def get_leave_by_id(self, id, **kw):
        http_method, body, headers, token = http_helper.parse_request()
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])
        user = validator.verify(token)
        if not user:
            return http_helper.response(code=400,
                                        message=_(
                                            "You are not allowed to perform this operation. please check with one of your team admins"),
                                        success=False)
        data = None
        try:
            holidays = http.request.env['hr.holidays'].sudo().search([('id', '=', id)])
            if holidays:
                data = self.get_return_data(holidays)

            return http_helper.response(message=_("GET Leave Successfully"), data={'leave': data})

        except (UserError, AccessError, ValidationError, Exception, Warning) as e:
            http.request._cr.rollback()
            error = str(e)
            return http_helper.response(code=400, message=str(error), success=False)
        except Exception as e:
            http.request._cr.rollback()
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)

    @http.route(['/rest_api/v2/leaves'], type='http', auth='none', csrf=False, methods=['POST'])
    def create_leaves(self, **kw):
        http_method, body, headers, token = http_helper.parse_request()
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])
        user = validator.verify(token)
        if not user:
            return http_helper.response(code=400, message=_(
                "You are not allowed to perform this operation. please check with one of your team admins"),
                                        success=False)
        if not body.get('start_date') or not body.get('end_date') or not body.get('type_id'):
            return http_helper.response(code=400, message="Enter All required Data for Leave request", success=False)
        employee = http.request.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
        if not employee:
            return http_helper.response(code=400, message=_(
                "You Have issue in your employee profile. please check with one of your team admins"), success=False)
        try:
            with request.env.cr.savepoint():
                local_tz = pytz.timezone(
                    user.tz or 'GMT')
                from_date = fields.Datetime.from_string(body["start_date"]).replace(hour=0, minute=0, second=0,
                                                                                    microsecond=0,tzinfo=local_tz)
                to_date = fields.Datetime.from_string(body["end_date"]).replace(hour=0, minute=0, second=0,
                                                                                microsecond=0,tzinfo=local_tz)
                utc_dt_from = from_date.strftime("%Y-%m-%d %H:%M:%S")
                utc_dt_to = to_date.strftime("%Y-%m-%d %H:%M:%S")
                #
                from_date = datetime.strptime(
                    utc_dt_from, "%Y-%m-%d %H:%M:%S")
                from_date = fields.Datetime.to_string(from_date)
                to_date = datetime.strptime(
                    utc_dt_to, "%Y-%m-%d %H:%M:%S")
                to_date = fields.Datetime.to_string(to_date)


                vals = {
                    "employee_id": employee.id,
                    "date_from": from_date,
                    "date_to": to_date,
                    "name": body["description"] if body.get("description") else "",
                    "holiday_status_id": int(body["type_id"]),
                    "delegate_acc": False if body["delegated_permission"] in ("false","False",'') else True   ,

                    # 'replace_by': int(body['replacement_id']) if body['replacement_id'] else False
                }
                if 'ticket' in body and body['ticket']:
                    vals.update({'issuing_clearance_form': body['issuing_clearance_form'],
                                'issuing_deliver_custdy': body[
                                    'issuing_deliver_custdy'] if 'issuing_deliver_custdy' in body else False,
                                'permission_request_for': body[
                                    'permission_request_for'] if 'permission_request_for' in body else False,
                                'issuing_exit_return': body[
                                    'exit_return_duration'] if 'exit_return_duration' in body else False,
                                'ticket_cash_request_type': body[
                                    'ticket_cash_request_type'] if 'ticket_cash_request_type' in body else False,
                                'ticket_cash_request_for': body[
                                    'ticket_cash_request_for'] if 'ticket_cash_request_for' in body else False,
                                'issuing_ticket': body['issuing_ticket'] if 'issuing_ticket' in body else False, })

                holidays = http.request.env['hr.holidays'].sudo().create(vals)
                if 'attachment' in body and body['attachment']:
                    attach = http.request.env['ir.attachment'].sudo().create({
                            'name': body['attachment'].filename,
                            'datas': base64.b64encode(body['attachment'].read()),
                            'store_fname': body['attachment'].filename,
                            'res_model': 'hr.holidays',
                            'res_id': holidays.id,
                            'att_holiday_ids': holidays.id,
                        })
                    holidays.attach_ids = [(4,attach.id)]
                if holidays:
                    holidays._onchange_employee()
                    holidays._onchange_date_from()
                    holidays._onchange_date_to()
                    holidays._get_end_date()
                    holidays._get_holiday_related_date()
                    # holidays.confirm()
                    # holidays.number_of_days_temp = holidays._get_number_of_days(body['start_date'], body['end_date'],
                    #                                                             employee)
                    data = self.get_return_data(holidays)
                    return http_helper.response(message=_("Leave Created Successfully"), data={'leaves': [data]})
        except (UserError, AccessError, ValidationError, Exception, Warning) as e:
            http.request._cr.rollback()
            error = str(e)
            return http_helper.response(code=400, message=str(error), success=False)
        except Exception as e:
            http.request._cr.rollback()
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)

    @http.route(['/rest_api/v2/leaves/<int:id>'], type='http', auth='none', csrf=False, methods=['PUT'])
    def edit_leaves(self, id, approvel=None, **kw):
        http_method, body, headers, token = http_helper.parse_request()
        result = validator.verify_token(token)
        # import pdb
        # pdb.set_trace()
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])
        user = validator.verify(token)
        if not user:
            return http_helper.response(code=400,
                                        message=_(
                                            "You are not allowed to perform this operation. please check with one of your team admins"),
                                        success=False)
        if not body.get('start_date') or not body.get('end_date') or not body.get('type_id'):
            return http_helper.response(code=400, message="Enter All required Data for Leave request",
                                        success=False)
        employee = http.request.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
        if not employee:
            return http_helper.response(code=400,
                                        message=_(
                                            "You Have issue in your employee profile. please check with one of your team admins"),
                                        success=False)
        try:
            with request.env.cr.savepoint():
                holidays = http.request.env['hr.holidays'].search([('id', '=', int(id))])
                if holidays:
                    days = holidays._get_number_of_days(body['start_date'], body['end_date'], employee.id,holidays.holiday_status_id.official_holidays,
                                                                    holidays.holiday_status_id.working_days)
                    local_tz = pytz.timezone(
                        user.tz or 'GMT')
                    from_date = fields.Datetime.from_string(body["start_date"]).replace(hour=0, minute=0, second=0,
                                                                                        microsecond=0, tzinfo=local_tz)
                    to_date = fields.Datetime.from_string(body["end_date"]).replace(hour=0, minute=0, second=0,
                                                                                    microsecond=0, tzinfo=local_tz)
                    utc_dt_from = from_date.strftime("%Y-%m-%d %H:%M:%S")
                    utc_dt_to = to_date.strftime("%Y-%m-%d %H:%M:%S")
                    #
                    from_date = datetime.strptime(
                        utc_dt_from, "%Y-%m-%d %H:%M:%S")
                    from_date = fields.Datetime.to_string(from_date)
                    to_date = datetime.strptime(
                        utc_dt_to, "%Y-%m-%d %H:%M:%S")
                    to_date = fields.Datetime.to_string(to_date)
                    vals = {
                        'date_from': from_date, 'date_to': to_date,
                        'name': body['description'] if body.get('description') else '',
                        'holiday_status_id': int(body['type_id']),
                        'number_of_days_temp': days, 'delegate_acc': json.loads(body['delegated_permission']),
                    }
                    if approvel and 'replacement_id' in body:
                        vals.update({
                            'replace_by': int(body['replacement_id'])
                        })
                    if 'ticket' in body and body['ticket']:
                        vals.update({'issuing_clearance_form': body['issuing_clearance_form'],
                                    'issuing_deliver_custdy': body[
                                        'issuing_deliver_custdy'] if 'issuing_deliver_custdy' in body else False,
                                    'permission_request_for': body[
                                        'permission_request_for'] if 'permission_request_for' in body else False,
                                    'exit_return_duration': body[
                                        'exit_return_duration'] if 'exit_return_duration' in body else False,
                                    'ticket_cash_request_type': body[
                                        'ticket_cash_request_type'] if 'ticket_cash_request_type' in body else False,
                                    'ticket_cash_request_for': body[
                                        'ticket_cash_request_for'] if 'ticket_cash_request_for' in body else False,
                                    'issuing_ticket': body['issuing_ticket'] if 'issuing_ticket' in body else False, })
                    holidays.write(vals)
                    if 'attachment' in body and body['attachment']:
                        attach = http.request.env['ir.attachment'].sudo().create({
                            'name': body['attachment'].filename,
                            'datas': base64.b64encode(body['attachment'].read()),
                            'store_fname': body['attachment'].filename,
                            'res_model': 'hr.holidays',
                            'res_id': holidays.id,
                            'att_holiday_ids': holidays.id,
                        })
                        holidays.attach_ids = [(4, attach.id)]
                    holidays._onchange_employee()
                    holidays._onchange_date_from()
                    holidays._onchange_date_to()
                    holidays._get_end_date()
                    holidays._get_holiday_related_date()
                    data = self.get_return_data(holidays, approvel)
                    return http_helper.response(message=_("Leave Updated Successfully"), data={'leaves': [data]})
                else:
                    return http_helper.response(code=400,
                                            message=_(
                                                "You Have issue in your employee profile. please check with one of your team admins"),
                                            success=False)
        except (UserError, AccessError, ValidationError, Exception, Warning) as e:
            http.request._cr.rollback()
            error = str(e)
            return http_helper.response(code=400, message=str(error), success=False)
        except Exception as e:
            http.request._cr.rollback()
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)

    @http.route(['/rest_api/v2/leaves/<string:leaveId>'], type='http', auth='none', csrf=False, methods=['DELETE'])
    def delete_leaves(self, leaveId, **kw):
        http_method, body, headers, token = http_helper.parse_request()
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])
        user = validator.verify(token)
        if not user:
            return http_helper.response(code=400,
                                        message=_(
                                            "You are not allowed to perform this operation. please check with one of your team admins"),
                                        success=False)
        employee = http.request.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
        if not employee:
            return http_helper.response(code=400,
                                        message=_(
                                            "You are not allowed to perform this operation. please check with one of your team admins"),
                                        success=False)
        try:
            record = http.request.env['hr.holidays'].search([('id', '=', leaveId)])
            if record and record.state == 'draft':
                record.unlink()
                return http_helper.response(message=_("Deleted successfully"), data={})
            else:
                return http_helper.response(code=400,
                                            message=_(
                                                "You  can not perform this operation. please check with one of your team admins"),
                                            success=False)
        except (UserError, AccessError, ValidationError, Exception, Warning) as e:
            http.request._cr.rollback()
            error = str(e)
            return http_helper.response(code=400, message=str(error), success=False)
        except Exception as e:
            http.request._cr.rollback()
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)

            # Submit leave

    @http.route(['/rest_api/v2/leaves/balance'], type='http', auth='none', csrf=False, methods=['GET'])
    def get_leave_balance_data(self, **kw):
        http_method, body, headers, token = http_helper.parse_request()
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])
        user = validator.verify(token)
        if not user:
            return http_helper.response(code=400, message=_(
                "You are not allowed to perform this operation. please check with one of your team admins"),
                                        success=False)
        employee = http.request.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
        if not employee:
            return http_helper.response(code=400, message=_(
                "You Have issue in your employee profile. please check with one of your team admins"), success=False)
        try:
            balance = http.request.env['hr.holidays'].search(
                [('employee_id', '=', employee.id), ('type', '=', 'add'), ('check_allocation_view', '=', 'balance')])
            li = []
            if balance:
                for s in balance:
                    value = {
                        "id": s.id,
                        "name": s.name or "",
                        # "total": s.leave_balance, repacel this in new relase 
                        # "remain": s.remaining_leaves, repacel this in new relase 
                        "remain": s.leave_balance,
                        "total": s.remaining_leaves,
                        "taken": s.leaves_taken,
                    }
                    li.append(value)
            data = {'system_leaves': li, }
            return http_helper.response(message="Data Found", data=data)
        except (UserError, AccessError, ValidationError, Exception, Warning) as e:
            http.request._cr.rollback()
            error = str(e)
            return http_helper.response(code=400, message=str(error), success=False)
        except Exception as e:
            http.request._cr.rollback()
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)

# -*- coding: utf-8 -*-
import werkzeug
import calendar
from odoo import http, tools
from odoo.http import request, Response
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.exceptions import UserError
from datetime import datetime
import base64
from ..validator import validator
from ..http_helper import http_helper
import json
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
import logging
_logger = logging.getLogger(__name__)
from odoo.tools.translate import _
import re

from odoo import fields

SENSITIVE_FIELDS = ['password', 'password_crypt', 'new_password', 'create_uid', 'write_uid']


class AttendanceController(http.Controller):

    # Zoons
    @http.route(['/rest_api/v1/zoons'], type='http', auth='none', csrf=False, methods=['GET'])
    def get_zone(self, **kw):
        http_method, body, headers, token = http_helper.parse_request()
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])
        user = validator.verify(token)
        if not user:
            return http_helper.response(code=400, message=_("You are not allowed to perform this operation. please check with one of your team admins"), success=False)
        employee = http.request.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
        if not employee:
            return http_helper.response(code=400, message=_("You are not allowed to perform this operation. please check with one of your team admins"), success=False)
        try:
            zone = http.request.env['attendance.zone'].search([('employee_ids', 'in', employee.id)])
            li = []
            general_zoons = False
            if zone:
                general = zone.filtered(lambda r:r.general)
                specific = zone.filtered(lambda r:r.specific)
                general_zoons = True if general else False
                for z in specific:
                    value = {'id': z.id, 'name': z.zone, 'latitude': z.latitude, 'longitude': z.longitude, 'allowed_range': z.allowed_range,
                             'loc_ch_intv': z.loc_ch_intv, 'loc_ch_dist': z.loc_ch_dist, 'srv_ch_tmout': z.srv_ch_tmout}
                    li.append(value)
            return http_helper.response(message="Data Found", data={'general_zoons':general_zoons, 'specific_zoons':li})
        except Exception as e:
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)

    # First check in Last check out
    @http.route(['/rest_api/v1/checks'], type='http', auth='none', csrf=False, methods=['GET'])
    def get_check_in_out(self, **kw):
        http_method, body, headers, token = http_helper.parse_request()
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])
        user = validator.verify(token)
        if not user:
            return http_helper.response(code=400, message=_("You are not allowed to perform this operation. please check with one of your team admins"), success=False)
        if not body.get('date'):
            return http_helper.response(code=400, message=_("Enter Data First"), success=False)
        employee = http.request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
        if not employee:
            return http_helper.response(code=400, message=_("You Have issue in your employee profile. please check with one of your team admins"), success=False)
        date = datetime.strptime(body.get('date'), DEFAULT_SERVER_DATE_FORMAT)
        try:
            attendance = http.request.env['attendance.attendance'].search([('employee_id', '=', employee.id), ('action_date', '=', date)])
            li = []
            in_rec = False
            out_rec = False
            checks_in = attendance.filtered(lambda r:r.action == 'sign_in').mapped('name')
            check_in = min(checks_in) if checks_in else False
            if check_in:
                in_rec = attendance.filtered(lambda r:r.name == check_in and r.action == 'sign_in')
                if in_rec:
                    data = self.get_check_records(in_rec[0])
                    li.append(data)
            check_outs = attendance.filtered(lambda r:r.action == 'sign_out').mapped('name')
            check_out = max(check_outs) if check_outs else False
            if check_out:
                out_rec = attendance.filtered(lambda r:r.name == check_out and r.action == 'sign_out')
                if out_rec:
                    data = self.get_check_records(out_rec[0])
                    li.append(data)
            return http_helper.response(message="Data Found", data={'checks': li})
        except Exception as e:
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)

    def get_check_records(self, action):
        date = action.name.time()
        data = {
            "id": action.id,
            "action": action.action,
            "time": str(date),
            "location": {
                "latitude": action.latitude,
                "longitude": action.longitude,
            }}
        return data

    @http.route(['/rest_api/v1/refresh'], type='http', auth='none', csrf=False, methods=['GET'])
    def refresh_attendance(self, **kw):
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
                "You are not allowed to perform this operation. please check with one of your team admins"),
                                        success=False)
        try:
            data = {}
            records = employee.resource_calendar_id
            shifts = {}
            if records:
                data.update({
                    'shift_start_time': '{0:02.0f}:{1:02.0f}'.format(*divmod(records.full_min_sign_in * 60, 60))if records.is_full_day else
                    ['{0:02.0f}:{1:02.0f}'.format(*divmod(records.shift_one_min_sign_in * 60, 60)),
                     '{0:02.0f}:{1:02.0f}'.format(*divmod(records.shift_two_min_sign_in * 60, 60)), ],
                    'shift_end_time': '{0:02.0f}:{1:02.0f}'.format(*divmod(records.full_min_sign_out * 60, 60)) if records.is_full_day else
                    ['{0:02.0f}:{1:02.0f}'.format(*divmod(records.shift_one_min_sign_out * 60, 60)),
                     '{0:02.0f}:{1:02.0f}'.format(*divmod(records.shift_two_min_sign_out * 60, 60)), ],
                })

            attendance = http.request.env['attendance.attendance'].sudo().search([('employee_id', '=', employee.id), ], order='name desc',
                                                       limit=1)
            if attendance:
                date = attendance.name.time()
                data.update({'id': attendance.id , 'action': attendance.action,
                        'attendance_status': attendance.action, 'time': str(date), 'zone': attendance.zone,
                        'longitude': attendance.longitude, 'latitude': attendance.latitude})
                _logger.error(data)
                return http_helper.response(message="Refresh Successfully", data=data)
            else:
                data.update({'attendance_status':'sign_out'})
                return http_helper.response(message="Refresh Successfully", data=data)
        except Exception as e:
            http.request._cr.rollback()
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)

    # Check In Out
    @http.route(['/rest_api/v1/checks'], type='http', auth='none', csrf=False, methods=['POST'])
    def create_check_in_out(self, system_checkout=None, **kw):
        http_method, body, headers, token = http_helper.parse_request()
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])
        user = validator.verify(token)
        if not user:
            return http_helper.response(code=400, message=_("You are not allowed to perform this operation. please check with one of your team admins"), success=False)
        if not body.get('action'):
            return http_helper.response(code=400, message=_("Enter Check in type"), success=False)
        if not body.get('device_id'):
            return http_helper.response(code=400, message=_("Enter Device Id"), success=False)
        if not body.get('latitude') or not body.get('longitude'):
            return http_helper.response(code=400, message=_("Enter Zone  Data for Check in"), success=False)
        employee = http.request.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
        if not employee:
            return http_helper.response(code=400, message=_("You are not allowed to perform this operation. please check with one of your team admins"), success=False)
        if employee.device_id != body.get('device_id'):
            return http_helper.errcode(code=403, message=_("Device id not matching with already exist in system please contact system admin"))
        try:
            zones = http.request.env['attendance.zone'].search([('employee_ids', 'in', employee.id)])
            if not zones:
                return http_helper.errcode(code=403, message=_("Employee not in any Zone,Contact Admin "))
            zone = http.request.env['attendance.zone'].search([('id', '=', body.get('id'))]) if body.get(
                'id') else False
            rec = http.request.env['attendance.attendance'].sudo().search([('employee_id', '=', employee.id), ],
                                                                                 order='name desc',
                                                                                 limit=1)
            system_checkout = json.loads(body.get('system_checkout')) if 'system_checkout'  in body else False
            if not rec or rec and rec.action != body.get('action'):
                attendance = http.request.env['attendance.attendance'].create({
                    'employee_id':employee.id,
                    'action':body.get('action'),
                    'action_type':"system_checkout" if body.get('action') == 'sign_out' and system_checkout == True else 'application',
                    'name': fields.datetime.now(),
                    # 'device_id':body.get('device_id'),
                    'zone':zone.zone if zone else "%s,%s" % (body.get('longitude'), body.get('latitude')),
                    'longitude': body.get('longitude'),
                    'latitude':body.get('latitude'),
                })
                if attendance:
                    if body.get('action') == 'sign_out' and system_checkout == True:
                        msg = (_("System Force Sign out Due to  Change Location Permission "))
                        subject = (_("System Force Sign out"))
                        self.send_msg(employee, msg, subject)
                    date = attendance.name.time()
                    data = {
                        "id": attendance.id,
                        "action": attendance.action,
                        "attendance_status": attendance.action,
                        "time": str(date),
                        "zone": attendance.zone,
                        "longitude": attendance.longitude,
                        "latitude": attendance.latitude,
                        "range": zone.allowed_range if zone else False,
                    }
                    msg = (_("Check Out successfully")) if body.get('action') == 'sign_out' else (_("Check in successfully"))
            else:
                msg = (_("Check  Fail Due To Duplication"))
                data = {}
            return http_helper.response(msg, data={'checks': [data]})
        except Exception as e:
            http.request._cr.rollback()
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)

    # Get Attendance Transaction Records
    @http.route(['/rest_api/v1/attendaces'], type='http', auth='none', csrf=False, methods=['GET'])
    def get_attendance_transactions(self, **kw):
        http_method, body, headers, token = http_helper.parse_request()
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])
        user = validator.verify(token)
        if not user:
            return http_helper.response(code=400, message=_("You are not allowed to perform this operation. please check with one of your team admins"), success=False)
        if not body.get('date'):
            return http_helper.response(code=400, message=_("Enter Date First"), success=False)
        employee = http.request.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
        if not employee:
            return http_helper.response(code=400, message=_("You are not allowed to perform this operation. please check with one of your team admins"), success=False)
        date = datetime.strptime(body.get('date'), DEFAULT_SERVER_DATE_FORMAT).date()
        year = date.year
        month = date.month
        month_start = datetime(year, month, 1).date()
        last = calendar.monthrange(year, month)[1]
        month_end = datetime(year, month, last).date()
        try:
            records = http.request.env['hr.attendance.transaction'].search([('employee_id', '=', employee.id),
            ('normal_leave', '=', False), ('public_holiday', '=', False), ('is_absent', '=', False), ('date', '>=', month_start), ('date', '<=', month_end)])
            li = []
            if records:
                for rec in records:
                    attendance = {
                        'id':rec.id,
                        'date':str(rec.date),
                        'first_check_in':rec.sign_in,
                        'last_check_out':rec.sign_out,
                        'total_time':rec.office_hours,
                    }
                    li.append(attendance)
            return http_helper.response(message="Data Found", data={'attendaces': li})
        except Exception as e:
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)

    # Get shift
    @http.route(['/rest_api/v1/shifts'], type='http', auth='none', csrf=False, methods=['GET'])
    def get_shift(self, **kw):
        http_method, body, headers, token = http_helper.parse_request()
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])
        user = validator.verify(token)
        if not user:
            return http_helper.response(code=400, message=_("You are not allowed to perform this operation. please check with one of your team admins"), success=False)
        employee = http.request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
        if not employee:
            return http_helper.response(code=400, message=_("You are not allowed to perform this operation. please check with one of your team admins"), success=False)
        try:
            records = employee.resource_calendar_id
            shifts = []
            if records:
                shifts.append({
                    'start_time':records.full_min_sign_in if records.is_full_day else records.shift_one_min_sign_in,
                    'end_time':records.full_min_sign_out if records.is_full_day else records.shift_one_min_sign_out,
                })
            return http_helper.response(message=_("Data Found successfully"), data={'shifts': shifts})
        except Exception as e:
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)

    @http.route(['/rest_api/v1/auto_checkout'], type='http', auth='none', csrf=False, methods=['POST'])
    def auto_checkout(self, in_zone=False, **kw):
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
                "You are not allowed to perform this operation. please check with one of your team admins"),
                                        success=False)
        try:
            if json.loads(body['in_zone']):
                records = employee.attendance_log_ids.sudo().filtered(lambda r: str(r.date) == str(datetime.today().date()) and r.old == False)
                for r in records:
                    r.old = True
                return http_helper.response(message="Old Record Done", data={'status': True})

            else:
                attendance = http.request.env['attendance.attendance'].sudo().search(
                    [('employee_id', '=', employee.id), ], order='name desc',
                    limit=1)
                if attendance.action == 'sign_in':
                    records = employee.attendance_log_ids.sudo().filtered(lambda r: r.old == False and str(r.date) == str(datetime.today().date()))
                    # records = employee.attendance_log_ids.sudo().filtered(lambda r: r.old == False and r.date == str(datetime.today().date()))
                    if records:
                        n = len(records)
                        last = records[n - 1]
                        last = fields.Datetime.from_string(last.time)
                        now = datetime.now()
                        if now > last:
                            diff = now - last
                            diff = diff.seconds / 60
                            auto = request.env.user.company_id.auto_checkout if request.env.user.company_id.auto_checkout > 0 else 5
                            if diff >= auto:
                                attendance = http.request.env['attendance.attendance'].create({
                                    'employee_id': employee.id,
                                    'action':'sign_out',
                                    'action_type': 'auto',
                                    'name': fields.datetime.now(),
                                    # 'device_id': body.get('device_id'),
                                    'zone': "%s,%s" % (body.get('longitude'), body.get('latitude')),
                                    'longitude': body.get('longitude'),
                                    'latitude': body.get('latitude'),
                                })
                                msg = (_("Auto Checkout successfully"))
                                subject = (_("Auto Checkout"))
                                self.send_msg(employee, msg, subject)
                                records = employee.attendance_log_ids.sudo().filtered(
                                    lambda r: str(r.date) == str(datetime.today().date()) and r.old == False)
                                for r in records:
                                    r.old = True
                                return http_helper.response(message="Auto Checkout  successfully", data={'status': True})
                            else:
                                msg = (_("You are out of attendance zone you will be auto sin out "))
                                subject = (_("Auto Sign out"))
                                self.send_msg(employee, msg, subject)
                                return http_helper.response(message="Auto Checkout  Fail and Send", data={'status': False})
                    else:
                        self.create_log(employee, body.get('longitude'), body.get('latitude'))
                        msg = (_("You are out of attendance zone you will be auto sin out "))
                        subject = (_("Auto Sign out"))
                        self.send_msg(employee, msg, subject)
                        return http_helper.response(message="Auto Checkout  Fail and Send", data={'status': False})
                else:
                    return http_helper.response(message="You are not Checked in yet", data={'status': True})
        except Exception as e:
            http.request._cr.rollback()
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)
            
    def send_msg(self, emp, msg, subject):
        if emp.user_id.partner_id:
            partner_id = emp.user_id.partner_id
            partner_id.send_notification(
                subject, msg, data=None, all_device=True)
            data = {
                'title':subject,
                'body':msg,
            }
            emp.user_push_notification(data)

    def create_log(self, employee, longitude, latitude):
        attendance = http.request.env['attendance.log'].create({
            'employee_id': employee.id,
            'time': fields.datetime.now(),
            'date': datetime.today().date(),
            'longitude': longitude,
            'latitude':latitude,
        })

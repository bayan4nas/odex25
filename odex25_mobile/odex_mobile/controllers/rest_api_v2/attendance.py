# -*- coding: utf-8 -*-
import werkzeug
import calendar
from odoo import http, tools
from odoo.http import request, Response
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.exceptions import UserError , AccessError, ValidationError
from datetime import datetime , timedelta
import base64
from ...validator import validator
from ...http_helper import http_helper
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
    @http.route(['/rest_api/v2/zoons'], type='http', auth='none', csrf=False, methods=['GET'])
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
                    value = {'id':z.id, 'name':z.zone, 'latitude':z.latitude, 'longitude':z.longitude, 'allowed_range':z.allowed_range,
                            'loc_ch_intv': z.loc_ch_intv, 'loc_ch_dist':z.loc_ch_dist, 'srv_ch_tmout':z.srv_ch_tmout, 'app_cl_tmout': z.app_cl_tmout}
                    li.append(value)
            return http_helper.response(message="Data Found", data={'general_zoons':general_zoons, 'specific_zoons':li})
        except (UserError, AccessError, ValidationError, Exception, Warning) as e:
            http.request._cr.rollback()
            error = str(e)
            return http_helper.response(code=400, message=str(error), success=False)
        except Exception as e:
            http.request._cr.rollback()
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)

    # First check in Last check out
    @http.route(['/rest_api/v2/checks'], type='http', auth='none', csrf=False, methods=['GET'])
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
        except (UserError, AccessError, ValidationError, Exception, Warning) as e:
            http.request._cr.rollback()
            error = str(e)
            return http_helper.response(code=400, message=str(error), success=False)
        except Exception as e:
            http.request._cr.rollback()
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

    @http.route(['/rest_api/v2/refresh'], type='http', auth='none', csrf=False, methods=['GET'])
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
            with request.env.cr.savepoint():
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
        except (UserError, AccessError, ValidationError, Exception, Warning) as e:
            http.request._cr.rollback()
            error = str(e)
            return http_helper.response(code=400, message=str(error), success=False)
        except Exception as e:
            http.request._cr.rollback()
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)

    # Check In Out
    @http.route(['/rest_api/v2/checks'], type='http', auth='none', csrf=False, methods=['POST'])
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
        employee = http.request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
        if not employee:
            return http_helper.response(code=400, message=_("You are not allowed to perform this operation. please check with one of your team admins"), success=False)
        if employee.device_id != body.get('device_id'):
            return http_helper.errcode(code=403, message=_("Device id not matching with already exist in system please contact system admin"))
        try:
            with request.env.cr.savepoint():
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
                # Reset last_active_time when the employee signed out
                if body.get('action') == 'sign_out':
                    employee.last_active_time = False
                return http_helper.response(msg, data={'checks': [data]})
        except (UserError, AccessError, ValidationError, Exception, Warning) as e:
            http.request._cr.rollback()
            error = str(e)
            return http_helper.response(code=400, message=str(error), success=False)
        except Exception as e:
            http.request._cr.rollback()
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)

    # Get Attendance Transaction Records
    @http.route(['/rest_api/v2/attendaces'], type='http', auth='none', csrf=False, methods=['GET'])
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
        now = fields.Date.today()
        if month_end > now:
            month_end = now
        try:
            records = http.request.env['hr.attendance.transaction'].sudo().search([('employee_id', '=', employee.id),
            ('date', '>=', str(month_start)), ('date', '<=', str(month_end))])
            # records = http.request.env['hr.attendance.transaction'].search([('employee_id','=',employee.id),
            # ('normal_leave', '=', True),('public_holiday', '=', True), ('is_absent','=',True),('date', '>=', str(month_start)), ('date', '<=', str(month_end))])
            li = []
            total_months = {}
            if records:
                records.get_hours()

                total_plan_hours = sum(records.mapped('plan_hours'))
                total_office_hours = sum(records.mapped('office_hours'))
                total_additional_hours = sum(records.mapped('additional_hours'))
                total_mission_hours = sum(records.mapped('total_mission_hours'))
                total_public_holiday = sum(records.filtered(lambda rec:rec.public_holiday == True).mapped('plan_hours'))
                total_normal_leave = sum(records.filtered(lambda rec:rec.normal_leave == True).mapped('plan_hours'))
                total_absent = sum(records.filtered(lambda rec:rec.is_absent == True).mapped('plan_hours'))
                total_approve_lateness = sum(records.mapped('lateness'))
                total_early_exit = sum(records.mapped('early_exit'))
                total_permission_hours = sum(records.mapped('total_permission_hours'))
                total_months = {
                    'total_plan_hours':self.convert_float_total_time(total_plan_hours),
                    'tr_total_plan_hours':_("Plan Hours"),

                    'total_additional_hours':self.convert_float_total_time(total_additional_hours),
                    'tr_total_additional_hours':_("Additional Hours"),

                    'total_normal_leave':self.convert_float_total_time(total_normal_leave),
                    'tr_total_normal_leave':_("Leaves Hours"),

                    'total_total_permission_hours':self.convert_float_total_time(total_permission_hours),
                    'tr_total_total_permission_hours':_("Permissions Hours"),

                    'total_office_hours':self.convert_float_total_time(total_office_hours + total_public_holiday + total_mission_hours),
                    'tr_total_office_hours':_("Attendance hours"),

                    'total_absent':self.convert_float_total_time(total_absent + total_approve_lateness + total_early_exit),
                    'tr_total_absent':_("Absence hours"),
                    }
                for rec in records:
                    attendance = {
                        'id':rec.id,
                        'date':str(rec.date),
                        'tr_date':self.get_translation_field(rec, 'date'),
                        'first_check_in':self.convert_float_2time(rec.sign_in),
                        'tr_sign_in':self.get_translation_field(rec, 'sign_in'),
                        'last_check_out':self.convert_float_2time(rec.sign_out),
                        'tr_sign_out':self.get_translation_field(rec, 'sign_out'),
                        'total_time':self.convert_float_2time(rec.office_hours),
                        'tr_office_hours':self.get_translation_field(rec, 'office_hours'),

                        'total_lateness_hours':self.convert_float_2time(rec.lateness),
                        'approve_lateness':rec.approve_lateness,
                        'tr_approve_lateness':self.get_translation_field(rec, 'approve_lateness'),
                        
                        'total_early_exit_hours':self.convert_float_2time(rec.early_exit),
                        'tr_total_early_exit_hours':self.get_translation_field(rec, 'early_exit'),
                        'early_exit':rec.approve_exit_out,
                        'tr_early_exit':self.get_translation_field(rec, 'approve_exit_out'),

                        'total_permission_hours':self.convert_float_2time(rec.total_permission_hours),
                        'tr_total_permission_hours':self.get_translation_field(rec, 'total_permission_hours'),
                        'permission':rec.approve_personal_permission,
                        'tr_permission':self.get_translation_field(rec, 'approve_personal_permission'),

                        'total_mission_hours':self.convert_float_2time(rec.total_mission_hours),
                        'tr_total_mission_hours':self.get_translation_field(rec, 'total_mission_hours'),
                        'mission':rec.is_official,
                        'tr_mission':self.get_translation_field(rec, 'is_official'),

                        'is_absent':rec.is_absent,
                        'tr_is_absent':self.get_translation_field(rec, 'is_absent'),
                        
                        'normal_leave':rec.normal_leave,
                        'tr_normal_leave':self.get_translation_field(rec, 'normal_leave'),

                        'public_holiday':rec.public_holiday,
                        'tr_public_holiday':self.get_translation_field(rec, 'public_holiday'),
                        
                    }
                    li.append(attendance)
            
                return http_helper.response(message="Data Found", data={'total_months':total_months, 'attendaces': li})
            else:
                return http_helper.response(message="Data not Found", data={'attendaces': li})
        except (UserError, AccessError, ValidationError, Exception, Warning) as e:
            http.request._cr.rollback()
            error = str(e)
            return http_helper.response(code=400, message=str(error), success=False)
        except Exception as e:
            http.request._cr.rollback()
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)

    # Get shift
    @http.route(['/rest_api/v2/shifts'], type='http', auth='none', csrf=False, methods=['GET'])
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

    @http.route(['/rest_api/v2/auto_checkout'], type='http', auth='none', csrf=False, methods=['POST'])
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
            with request.env.cr.savepoint():
                if json.loads(body['in_zone']):
                    records = employee.attendance_log_ids.sudo().filtered(lambda r: str(r.date) == str(datetime.today().date()) and r.old == False)
                    for r in records:
                        r.old = True
                    employee.message_sent = False
                    return http_helper.response(message="Old Record Done", data={'status': True})

                else:
                    attendance = http.request.env['attendance.attendance'].sudo().search(
                        [('employee_id', '=', employee.id), ], order='name desc',
                        limit=1)
                    if attendance.action == 'sign_in':
                        records = employee.attendance_log_ids.sudo().filtered(lambda r: r.old == False and str(r.date) == str(datetime.today().date()))
                        if records:
                            n = len(records)
                            last = records[n - 1]
                            last = fields.Datetime.from_string(last.time)
                            now = datetime.now()
                            if now > last:
                                diff = now - last
                                diff = diff.seconds / 60
                                zone = http.request.env['attendance.zone'].search([('employee_ids', 'in', employee.id)], limit=1)
                                zone_general = http.request.env['attendance.zone'].search([('general', '=', True)], limit=1)
                                auto = zone.auto_checkout or zone_general.auto_checkout or request.env.user.company_id.auto_checkout or 1
                                if diff >= auto:
                                    attendance = http.request.env['attendance.attendance'].create({
                                        'employee_id': employee.id,
                                        'action': 'sign_out',
                                        'action_type': 'auto',
                                        'name': last,
                                        'zone': "%s,%s" % (body.get('longitude'), body.get('latitude')),
                                        'longitude': body.get('longitude'),
                                        'latitude': body.get('latitude'),
                                    })
                                    msg = _("Auto Checkout  successfully")
                                    subject = _("Auto Checkout")
                                    self.send_msg(employee, msg, subject)
                                    records = employee.attendance_log_ids.sudo().filtered(
                                        lambda r: str(r.date) == str(datetime.today().date()) and r.old == False)
                                    for r in records:
                                        r.old = True
                                    employee.message_sent = False
                                    return http_helper.response(message="Auto Checkout  successfully", data={'status': True})
                                else:
                                    if not employee.message_sent:
                                        msg = _("You are out of attendance zone you will be auto sign out")
                                        subject = _("Auto Sign out")
                                        self.send_msg(employee, msg, subject)
                                        employee.message_sent = True
                                    return http_helper.response(message="Auto Checkout Fail and Send", data={'status': False})
                        else:
                            self.create_log(employee, body.get('longitude'), body.get('latitude'))
                            if not employee.message_sent:
                                msg = _("You are out of attendance zone you will be auto sign out")
                                subject = _("Auto Sign out")
                                self.send_msg(employee, msg, subject)
                                employee.message_sent = True
                            return http_helper.response(message="Auto Checkout Fail and Send", data={'status': False})
                    else:
                        return http_helper.response(message="You are not Checked in yet", data={'status': True})

        except (UserError, AccessError, ValidationError, Exception, Warning) as e:
            http.request._cr.rollback()
            error = str(e)
            return http_helper.response(code=400, message=str(error), success=False)
        except Exception as e:
            http.request._cr.rollback()
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)
        
    @http.route('/rest_api/v2/data-sync', type='http', auth='none', methods=['GET'], csrf=False)
    def data_sync(self, **kwargs):
        # Assuming that http_method, body, headers, and token are obtained via helper methods
        http_method, body, headers, token = http_helper.parse_request()

        # Validate token
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])
        
        # Verify user from token
        user = validator.verify(token)
        if not user:
            return http_helper.response(
                code=400,
                message="You are not allowed to perform this operation. Please check with one of your team admins.",
                success=False
            )

        # Find employee linked to the user
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
        if not employee:
            return http_helper.response(
                code=400,
                message="You are not allowed to perform this operation. Please check with one of your team admins.",
                success=False
            )

        # Get the attendance zone for the employee or use general zone
        zone = request.env['attendance.zone'].search([('employee_ids', 'in', employee.id)], limit=1)
        if not zone:
            zone = request.env['attendance.zone'].search([('general', '=', True)], limit=1)

        # Fetch the timeout value from the zone, default to 5 minutes if zone is not found or no value
        app_cl_tmout = zone.app_cl_tmout if zone else 5

        # Get the current datetime and compare with last_active_time
        now = fields.Datetime.now()
        last_active_time = employee.last_active_time or now
        time_difference = now - last_active_time

        # Check if the time difference exceeds the zone's timeout using timedelta
        if time_difference > timedelta(minutes=app_cl_tmout):
            return http_helper.response(
                code=200, 
                message=f"Time difference is more than {app_cl_tmout} minutes",
                success=True,
                data={'force_checkout': True}
            )
        else:
            # Update last_active_time if force_checkout is False
            employee.write({'last_active_time': now})
            return http_helper.response(
                code=200, 
                message=f"Time difference is less than {app_cl_tmout} minutes",
                success=True,
                data={'force_checkout': False}
            )
    
    def send_msg(self, emp, msg, subject):
        if emp.user_id.partner_id:
            partner_id = emp.user_id.partner_id
            partner_id.send_notification(subject, msg, data=None, all_device=True)
            data = {
                'title':subject,
                'body':msg,
            }
            # emp.user_push_notification(data)

    def create_log(self, employee, longitude, latitude):
        with request.env.cr.savepoint():
            attendance = http.request.env['attendance.log'].create({
                'employee_id': employee.id,
                'time': fields.datetime.now(),
                'date': datetime.today().date(),
                'longitude': longitude,
                'latitude':latitude,
            })
    
    def convert_float_2time(self, time):
        td = timedelta(hours=time)
        dt = datetime.min + td
        time = "{:%H:%M}".format(dt)
        return time
    
    def convert_float_total_time(self, time):
        return '{0:02.0f}:{1:02.0f}'.format(*divmod(time * 60, 60))
    
    def get_translation_field(self, rec, field):
        return request.env['ir.translation'].get_field_string(rec._name)[field]

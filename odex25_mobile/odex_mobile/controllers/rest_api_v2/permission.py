# -*- coding: utf-8 -*-
import werkzeug
from odoo import http, tools , exceptions
from datetime import datetime
from odoo.http import request, Response
import base64
from ...validator import validator
from ...http_helper import http_helper
# from odoo.addons.odex_mobile.validator import validator
# from odoo.addons.odex_mobile.http_helper import http_helper
import json
import logging
from odoo.exceptions import ValidationError, Warning ,UserError, AccessError
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT

_logger = logging.getLogger(__name__)
import re
from odoo.tools.translate import _


class PermissionController(http.Controller):
    # Permission
    @http.route(['/rest_api/v2/permissions'], type='http', auth='none', csrf=False, methods=['GET'])
    def get_permission(self, approvel=None, page=None, **kw):
        page = page if page else 1
        page, offset, limit, prev = validator.get_page_pagination(page)
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
            permissions = False
            permission_types = http.request.env['hr.personal.permission.type'].search_read([], ['name'])
            count = 0
            emp = []
            if approvel:
                domain = [('state', '!=', 'draft'), ('employee_id', '!=', employee.id)]
                permissions = http.request.env['hr.personal.permission'].search(domain, offset=offset, limit=limit)
                count = http.request.env['hr.personal.permission'].search_count(domain)
            else:
                permissions = http.request.env['hr.personal.permission'].search([('employee_id', '=', employee.id)],
                                                                                offset=offset, limit=limit)
                count = http.request.env['hr.personal.permission'].search_count([('employee_id', '=', employee.id)])
            if permissions:
                for per in permissions:
                    value = {
                        "permission_type_id": per.permission_type_id.id,
                        "permission_type_name": per.permission_type_id.name,
                        "employee_id": per.employee_id.id,
                        "employee_name": per.employee_id.name,
                        "id": per.id,
                        "date_from": str(per.date_from),
                        "date_to": str(per.date_to),
                        "duration": per.duration,
                        "date": str(per.date),
                        "state": validator.get_state_name(per, per.state),
                        "state_name": per.state,
                        "early_exit": per.early_exit,
                        "reason_msg": per.reason or "",
                        "mission_purpose": per.mission_purpose or "",
                        "attachment": self.get_attchment(per),
                    }
                    emp.append(value)
            next = validator.get_page_pagination_next(page, count)
            url = "/rest_api/v2/permissions?approvel=%s&page=%s" % (approvel, next) if next else False
            prev_url = "/rest_api/v2/permissions?approvel=%s&page=%s" % (approvel, prev) if prev else False
            data = {'links': {'prev': prev_url, 'next': url, }, 'count': count,
                    'results': {'permission_types': permission_types, 'permissions': emp, 'groups': ['group_division_manager', 'group_hr_user']}}
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

    @http.route(['/rest_api/v2/permissions'], type='http', auth='none', csrf=False, methods=['POST'])
    def create_permission(self, **kw):
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
        if not body.get('date') or not body.get('date_from') or not body.get('date_to') or not body.get('permission_type_id'):
            return http_helper.response(code=400, message=_("Enter All required Dates for Permission request"),
                                        success=False)
        if not body.get('early_exit'):
            return http_helper.response(code=400, message="Enter Early Exit for Permission request", success=False)
        # if not body.get('mission_purpose'):
        #     return http_helper.response(code=400, message="mission purpose for Permission request", success=False)
        employee = http.request.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
        if not employee:
            return http_helper.response(code=400,
                                        message=_(
                                            "You Have issue in your employee profile. please check with one of your team admins"),
                                        success=False)
        permission_type_id = http.request.env['hr.personal.permission.type'].browse(int(body.get('permission_type_id')))
        permission = None
        try:
            permission_number = self.permission_number_decrement(employee, body['date_from'], body['date_to'], permission_type_id)
            with request.env.cr.savepoint():
                permission = http.request.env["hr.personal.permission"].sudo().create(
                        {
                            "permission_type_id": permission_type_id.id,
                            "employee_id": employee.id,
                            "date_from": body["date_from"],
                            "date_to": body["date_to"],
                            "early_exit": body["early_exit"],
                            "mission_purpose": body["mission_purpose"],
                            "permission_number": permission_number,
                            "date": body["date"],
                        }
                    )
                
                # permission.permission_number_decrement()
                if 'attachment' in body and body['attachment']:
                    attach = http.request.env['ir.attachment'].sudo().create({
                        'name': body['attachment'].filename,
                        'datas': base64.b64encode(body['attachment'].read()),
                        'store_fname': body['attachment'].filename,
                        'res_model': 'hr.personal.permission',
                        'res_id': permission.id,
                        'personal_permission_id': permission.id,

                    })
                #
                if permission:
                    data = {
                        "id": permission.id,
                        "date": str(permission.date),
                        "permission_type_id": permission.permission_type_id.id,
                        "permission_type_name": permission.permission_type_id.name,
                        "duration": permission.duration,
                        "date_from": str(permission.date_from),
                        "date_to": str(permission.date_to),
                        "early_exit": permission.early_exit,
                        "state": validator.get_state_name(permission, permission.state),
                        "state_name": permission.state,
                        "reason_msg": permission.reason or "",
                        "mission_purpose": permission.mission_purpose or "",
                        "attachment": self.get_attchment(permission),
                    }
                    return http_helper.response(message="Permission Created Successfully", data={'permission': [data]})
        except (UserError, AccessError, ValidationError, Exception, Warning) as e:
            http.request._cr.rollback()
            error = str(e)
            return http_helper.response(code=400, message=str(error), success=False)
        except Exception as e:
            http.request._cr.rollback()
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)

    @http.route(['/rest_api/v2/permissions/<string:id>'], type='http', auth='none', csrf=False, methods=['PUT'])
    def edit_permission(self, id, **kw):
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
        if not body.get('date') or not body.get('date_from') or not body.get('date_to') or not body.get('permission_type_id'):
            return http_helper.response(code=400, message=_("Enter All required Dates for Permission request"),
                                        success=False)
        if not body.get('early_exit'):
            return http_helper.response(code=400, message=_("Enter Early Exit for Permission request"), success=False)
        employee = http.request.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
        if not employee:
            return http_helper.response(code=400,
                                        message=_(
                                            "You Have issue in your employee profile. please check with one of your team admins"),
                                        success=False)
        permission = None
        try:
            with request.env.cr.savepoint():
                permission = http.request.env['hr.personal.permission'].search([('id', '=', id)])
                permission_type_id = http.request.env['hr.personal.permission.type'].browse(int(body.get('permission_type_id')))
                if permission:
                    permission_number = self.permission_number_decrement(employee, body['date_from'], body['date_to'], permission_type_id)
                    permission.write(
                        {'employee_id': permission.employee_id.id, 'date_from': body['date_from'],
                        'permission_type_id': permission_type_id.id,
                        'date_to': body['date_to'],
                        'early_exit': body['early_exit'],
                        'date': body['date'],
                        'mission_purpose': body['mission_purpose'],
                        'permission_number': permission_number,
                        })
                    # permission.permission_number_decrement()
                    if 'attachment' in body and body['attachment']:
                        attach = http.request.env['ir.attachment'].sudo().create({
                            'name': body['attachment'].filename,
                            'datas': base64.b64encode(body['attachment'].read()),
                            'store_fname': body['attachment'].filename,
                            'res_model': 'hr.personal.permission',
                            'res_id': permission.id,
                            'personal_permission_id': permission.id,
                        })
                    permission = http.request.env['hr.personal.permission'].search([('id', '=', id)])
                    data = {
                        "id": permission.id,
                        "permission_type_id": permission_type_id.id,
                        "permission_type_name": permission_type_id.name,
                        "date": str(permission.date),
                        "duration": permission.duration,
                        "date_from": str(permission.date_from),
                        "date_to": str(permission.date_to),
                        "early_exit": permission.early_exit,
                        "reason_msg": permission.reason or "",
                        "mission_purpose": permission.mission_purpose or "",
                        "state": validator.get_state_name(permission, permission.state),
                        "state_name": permission.state,
                        "attachment": self.get_attchment(permission),
                    }
                    return http_helper.response(message="Permission Edited Successfully", data={'permission': [data]})
                else:
                    return http_helper.response(code=400,
                                                message=_("You are not found this permission by id"),
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

    @http.route(['/rest_api/v2/permission/<string:id>'], type='http', auth='none', csrf=False, methods=['GET'])
    def get_permission_by_id(self, id, **kw):
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
        try:
            data = None
            permission = http.request.env['hr.personal.permission'].search([('id', '=', id)])
            if permission:
                if 'attachment' in body and body['attachment']:
                    attach = http.request.env['ir.attachment'].sudo().create({
                        'name': body['attachment'].filename,
                        'datas': base64.b64encode(body['attachment'].read()),
                        'store_fname': body['attachment'].filename,
                        'res_model': 'hr.personal.permission',
                        'res_id': permission.id,
                        'personal_permission_id': permission.id,
                    })
                data = {
                    "id": permission.id,
                    "date": str(permission.date),
                    "permission_type_id": permission.permission_type_id.id,
                    "permission_type_name": permission.permission_type_id.name,
                    "duration": permission.duration,
                    "date_from": str(permission.date_from),
                    "date_to": str(permission.date_to),
                    "early_exit": permission.early_exit,
                    "reason_msg": permission.reason or "",
                    "mission_purpose": permission.mission_purpose or "",
                    "state": validator.get_state_name(permission, permission.state),
                    "state_name": permission.state,
                    "attachment": self.get_attchment(permission),
                }
                return http_helper.response(message="Get Permission Successfully", data={'permission': data})
            else:
                return http_helper.response(code=400, success=False, message="Get Permission Not Fount",
                                            data={'permission': data})
        except (UserError, AccessError, ValidationError, Exception, Warning) as e:
            http.request._cr.rollback()
            error = str(e)
            return http_helper.response(code=400, message=str(error), success=False)
        except Exception as e:
            http.request._cr.rollback()
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)

    @http.route(['/rest_api/v2/permissions/<string:permissionId>'], type='http', auth='none', csrf=False,
                methods=['DELETE'])
    def delete_permission(self, permissionId, **kw):
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
            record = http.request.env['hr.personal.permission'].search([('id', '=', permissionId)])
            if record and record.state == 'draft':
                record.unlink()
                return http_helper.response(message=_("Deleted successfully"), data={})
            else:
                return http_helper.response(code=400,
                                            message=_(
                                                "You can not perform this operation. please check with one of your team admins"),
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

            # Submit permissions

    @http.route(['/rest_api/v2/permissions/balance'], type='http', auth='none', csrf=False, methods=['GET'])
    def get_permission_balance(self, **kw):
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
                                            "You Have issue in your employee profile. please check with one of your team admins"),
                                        success=False)
        if not body.get('date_from') or not body.get('date_to') or not body.get('permission_type_id'):
            return http_helper.response(code=400, message=_("Enter All required Dates for Permission request"),
                                        success=False)
        try:
            emp = []
            permission_type_id = http.request.env['hr.personal.permission.type'].browse(int(body.get('permission_type_id')))
            number_of_per = permission_type_id.monthly_hours
            current_date = datetime.strptime(body['date_to'], DEFAULT_SERVER_DATETIME_FORMAT)
            current_month = datetime.strptime(body['date_to'], DEFAULT_SERVER_DATETIME_FORMAT).month
            date_from = current_date.strftime('%Y-{0}-01'.format(current_month))
            date_to = current_date.strftime('%Y-{0}-01'.format(current_month + 1))
            if current_month == 12:
                date_to = current_date.strftime('%Y-{0}-31'.format(current_month))
            permissions = http.request.env['hr.personal.permission'].search([
                ('employee_id', '=', employee.id),
                ('permission_type_id', '=', int(body['permission_type_id'])),
                ('state', '=', 'approve'),
                ('date_from', '>=', date_from),
                ('date_to', '<=', date_to)])
            permission_number = number_of_per - len(permissions)
            balance = permission_number if permission_number >= 0 else 0

            return http_helper.response(message="Data Found", data={'balance': balance,
                                                                    'permission_limit': permission_type_id.daily_hours})
        except (UserError, AccessError, ValidationError, Exception, Warning) as e:
            http.request._cr.rollback()
            error = str(e)
            return http_helper.response(code=400, message=str(error), success=False)
        except Exception as e:
            http.request._cr.rollback()
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)
    
    def permission_number_decrement(self, employee_id, date_from, date_to, permission_type_id):
        if employee_id:
            if not employee_id.first_hiring_date:
                raise Warning(_('You can not Request Permission The Employee have Not First Hiring Date'))
        if date_to:
            current_date = datetime.strptime(date_to, DEFAULT_SERVER_DATETIME_FORMAT)

            current_month = datetime.strptime(date_to, DEFAULT_SERVER_DATETIME_FORMAT).month
            # date_from = current_date.strftime('%Y-0{0}-01'.format(current_month))
            # date_to = current_date.strftime('%Y-0{0}-01'.format(current_month + 1))
            date_from = current_date.replace(day=1)
            if current_month == 12:
                date_to = current_date.strftime('%Y-{0}-31'.format(current_month))
            number_of_per = permission_type_id.monthly_hours
            employee_permissions = http.request.env['hr.personal.permission'].search([
                ('employee_id', '=', employee_id.id),
                ('permission_type_id', '=', permission_type_id.id),
                ('state', '=', 'approve'),
                ('date_from', '>=', date_from),
                ('date_to', '<=', date_to)])

            all_perission = 0
            for rec in employee_permissions:
                all_perission += rec.duration

                if rec.date_to and date_to:
                    permission_date1 = datetime.strptime(str(rec.date_to),DEFAULT_SERVER_DATETIME_FORMAT).date()
                    date_to_value1 = datetime.strptime(str(date_to), DEFAULT_SERVER_DATETIME_FORMAT).date()
                    if rec.date_to and date_to:
                        permission_date1 = datetime.strptime(str(rec.date_to),DEFAULT_SERVER_DATETIME_FORMAT).date()
                        date_to_value1 = datetime.strptime(str(date_to), DEFAULT_SERVER_DATETIME_FORMAT).date()

                    if permission_date1 == date_to_value1:
                        # return http_helper.errcode(code=403, message=_('Sorry You Have Used All Your Permission In This Day you have one permission per a Day'))
                        raise Warning(
                            _('Sorry You Have Used All Your Permission In This Day you have one permission per a Day'))

            if number_of_per > all_perission:

                return round(number_of_per - all_perission, 2)
            else:
                #     return http_helper.errcode(code=403, message=_('Sorry You Have Used All Your Permission Hours In This Month'))
                raise ValidationError(_('Sorry You Have Used All Your Permission Hours In This Month'))

    def get_attchment(self, res_id):
        attachment = http.request.env['ir.attachment'].search(
            [('res_model', '=', 'hr.personal.permission'), ('res_id', '=', res_id.id)])
        li = []
        if attachment:
            url_base = http.request.env['ir.config_parameter'].sudo().get_param('web.base.url')
            for att in attachment:
                url = url_base + "/api/content/%s" % (att.id)
                li.append(url)
        return li

# -*- coding: utf-8 -*-
from odoo.tools.translate import _
import re
import werkzeug
from odoo import http, tools, exceptions
from datetime import datetime
from odoo.http import request, Response
import base64
from ..validator import validator
from ..http_helper import http_helper
import json
import logging
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT, DEFAULT_SERVER_DATETIME_FORMAT
_logger = logging.getLogger(__name__)


class PermissionController(http.Controller):
    # Permission
    @http.route(['/rest_api/v1/permissions'], type='http', auth='none', csrf=False, methods=['GET'])
    def get_permission(self, approvel=None, page=None, **kw):
        page = page if page else 1
        page, offset, limit, prev = validator.get_page_pagination(page)
        http_method, body, headers, token = http_helper.parse_request()
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])
        user = validator.verify(token)
        if not user:
            return http_helper.response(code=400, message=_("You are not allowed to perform this operation. please check with one of your team admins"), success=False)
        employee = http.request.env['hr.employee'].search(
            [('user_id', '=', user.id)], limit=1)
        if not employee:
            return http_helper.response(code=400, message=_("You Have issue in your employee profile. please check with one of your team admins"), success=False)
        try:
            emp = []
            if approvel:
                domain = [('state', '!=', 'draft')]
                if user.has_group('hr.group_hr_user') or user.has_group('hr_base.group_division_manager'):
                    if not user.has_group('hr.group_hr_user'):
                        domain = [('state', '!=', 'draft'), '|', '|', ('department_id', '=', False), ('department_id.manager_id.user_id', '=', user.id),
                                  ('department_id.parent_id.manager_id.user_id', 'child_of', [user.id])]
                    permissions = http.request.env['hr.personal.permission'].search(
                        domain, offset=offset, limit=limit)
                    count = http.request.env['hr.personal.permission'].search_count(
                        domain)
                else:
                    permissions = False
                    count = 0
            else:
                permissions = http.request.env['hr.personal.permission'].search(
                    [('employee_id', '=', employee.id)], offset=offset, limit=limit)
                count = http.request.env['hr.personal.permission'].search_count(
                    [('employee_id', '=', employee.id)])
            if permissions:
                for per in permissions:
                    value = {'employee_id': per.employee_id.id, 'employee_name': per.employee_id.name, 'id': per.id, 'date_from': str(per.date_from), 'date_to': str(per.date_to), 'duration': per.duration, 'date': str(per.date),
                             'state': validator.get_state_name(per, per.state), 'state_name': per.state, 'early_exit': per.early_exit, 'attachment': self.get_attchment(per)}
                    emp.append(value)
            next = validator.get_page_pagination_next(page, count)
            url = "/rest_api/v1/permissions?approvel=%s&page=%s" % (
                approvel, next) if next else False
            prev_url = "/rest_api/v1/permissions?approvel=%s&page=%s" % (
                approvel, prev) if prev else False
            data = {'links': {'prev': prev_url, 'next': url, }, 'count': count, 'results': {
                'permissions': emp, 'groups': ['group_division_manager', 'group_hr_user']}}
            return http_helper.response(message="Data Found", data=data)
        except Exception as e:
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)

    # create permission
    @http.route(['/rest_api/v1/permissions'], type='http', auth='none', csrf=False, methods=['POST'])
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
        if not body.get('date') or not body.get('date_from') or not body.get('date_to'):
            return http_helper.response(code=400, message=_("Enter All required Dates for Permission request"),
                                        success=False)
        if not body.get('early_exit'):
            return http_helper.response(code=400, message="Enter Early Exit for Permission request", success=False)
        employee = http.request.env['hr.employee'].search(
            [('user_id', '=', user.id)], limit=1)
        if not employee:
            return http_helper.response(code=400,
                                        message=_(
                                            "You Have issue in your employee profile. please check with one of your team admins"),
                                        success=False)
        permission = None
        try:
            # permission_number = self.permission_number_decrement(
            #     employee, body['date_from'], body['date_to'])
            permission = http.request.env['hr.personal.permission'].sudo().create(
                {'employee_id': employee.id, 'date_from': body['date_from'], 'date_to': body['date_to'],
                 'early_exit': body['early_exit'], 
                 'date': body['date'],

                 })
            permission.permission_number_decrement()
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
                data = {'id': permission.id, 'date': str(permission.date), 'duration': permission.duration,
                        'date_from': str(permission.date_from), 'date_to': str(permission.date_to),
                        'early_exit': permission.early_exit,
                        'state': validator.get_state_name(permission, permission.state), 'state_name': permission.state,
                        'attachment': self.get_attchment(permission)}
                return http_helper.response(message="Permission Created Successfully", data={'permission': [data]})
        except Exception as e:
            http.request._cr.rollback()
            if permission:
                permission.unlink()
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)

    # edit permission
    @http.route(['/rest_api/v1/permissions/<string:id>'], type='http', auth='none', csrf=False, methods=['PUT'])
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
        if not body['date'] or not body['date_from'] or not body['date_to']:
            return http_helper.response(code=400, message=_("Enter All required Dates for Permission request"), success=False)
        if not body['early_exit']:
            return http_helper.response(code=400, message=_("Enter Early Exit for Permission request"), success=False)
        employee = http.request.env['hr.employee'].search(
            [('user_id', '=', user.id)], limit=1)
        if not employee:
            return http_helper.response(code=400,
                                        message=_(
                                            "You Have issue in your employee profile. please check with one of your team admins"),
                                        success=False)
        permission = None
        try:
            permission = http.request.env['hr.personal.permission'].search([
                                                                           ('id', '=', id)])
            if permission:
                permission.write(
                    {'employee_id': permission.employee_id.id, 'date_from': body['date_from'], 'date_to': body['date_to'],
                     'early_exit': body['early_exit'],
                     'date': body['date'],
                     })
                permission.permission_number_decrement()
                if 'attachment' in body and body['attachment']:
                    attach = http.request.env['ir.attachment'].create({
                        'name': body['attachment'].filename,
                        'datas': base64.b64encode(body['attachment'].read()),
                        'store_fname': body['attachment'].filename,
                        'res_model': 'hr.personal.permission',
                        'res_id': permission.id,
                        'personal_permission_id': permission.id,
                    })
                data = {'id': permission.id, 'date': str(permission.date), 'duration': permission.duration,
                        'date_from': str(permission.date_from), 'date_to': str(permission.date_to), 'early_exit': permission.early_exit,
                        'state': validator.get_state_name(permission, permission.state), 'state_name': permission.state, 'attachment': self.get_attchment(permission)}
                return http_helper.response(message="Permission Edited Successfully", data={'permission': [data]})
        except Exception as e:
            http.request._cr.rollback()
            if permission:
                permission.unlink()
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)

    def get_attchment(self, res_id):
        attachment = http.request.env['ir.attachment'].search(
            [('res_model', '=', 'hr.personal.permission'), ('res_id', '=', res_id.id)])
        li = []
        if attachment:
            url_base = http.request.env['ir.config_parameter'].sudo(
            ).get_param('web.base.url')
            for att in attachment:
                url = url_base + "/api/content/%s" % (att.id)
                li.append(url)
        return li

    @http.route(['/rest_api/v1/permissions/<string:permissionId>'], type='http', auth='none', csrf=False, methods=['DELETE'])
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
        employee = http.request.env['hr.employee'].search(
            [('user_id', '=', user.id)], limit=1)
        if not employee:
            return http_helper.response(code=400,
                                        message=_(
                                            "You are not allowed to perform this operation. please check with one of your team admins"),
                                        success=False)
        try:
            record = http.request.env['hr.personal.permission'].search(
                [('id', '=', permissionId)])
            if record and record.state == 'draft':
                record.unlink()
                return http_helper.response(message=_("Deleted successfully"), data={})
            else:
                return http_helper.response(code=400,
                                            message=_(
                                                "You can not perform this operation. please check with one of your team admins"),
                                            success=False)
        except Exception as e:
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)

            # Submit permissions

    @http.route(['/rest_api/v1/permissions/<string:permissionId>'], type='http', auth='none', csrf=False, methods=['PATCH'])
    def confirm_permission(self, permissionId, refused=None, **kw):
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
        employee = http.request.env['hr.employee'].search(
            [('user_id', '=', user.id)], limit=1)
        if not employee:
            return http_helper.response(code=400,
                                        message=_(
                                            "You are not allowed to perform this operation. please check with one of your team admins"),
                                        success=False)
        try:
            msg = ""
            permission = http.request.env['hr.personal.permission'].search(
                [('id', '=', permissionId)])
            dev = http.request.env['res.users'].sudo().search(
                [('groups_id', 'in', request.env.ref('hr_base.group_division_manager').ids)])
            hr = http.request.env['res.users'].sudo().search(
                [('groups_id', 'in', request.env.ref('hr.group_hr_user').ids)])
            if permission:
                if not refused:
                    if permission.state == 'draft':
                        permission.send()
                        msg = (_("permission Confirm Successfully"))
                        permission.firebase_notification(dev)
                    elif permission.state == 'send' and user.has_group('hr_base.group_division_manager'):
                        permission.direct_manager()
                        msg = _("Permission approved by Direct manager")
                        permission.firebase_notification(hr)
                    elif permission.state == 'direct_manager' and user.has_group('hr.group_hr_user'):
                        permission.approve()
                        msg = _("Permission approved ")
                        permission.firebase_notification()
                    elif permission.state in ['approve', 'refused'] and user.has_group('hr.group_hr_user'):
                        permission.draft_state()
                        msg = (_("Permission Reset to draft "))
                        permission.firebase_notification()
                elif refused:
                    if permission.state == 'direct_manager' and user.has_group('hr.group_hr_user') or\
                            permission.state == 'send' and user.has_group('hr_base.group_division_manager'):
                        permission.refused()
                        msg = (_("Permission Refused "))
                        permission.firebase_notification()
                else:
                    msg = _(
                        'You can not access this operation contact your system admin')
                    return http_helper.response(code=400, message=msg, success=False)

                data = {'id': permission.id, 'date': str(permission.date), 'duration': permission.duration,
                        'date_from': str(permission.date_from), 'date_to': str(permission.date_to),
                        'early_exit': permission.early_exit,
                        'state': validator.get_state_name(permission, permission.state),
                        'attachment': self.get_attchment(permission),
                        'state_name': permission.state, }

                return http_helper.response(message=msg, data={'permissions': [data]})
            else:
                return http_helper.response(code=400,
                                            message=_(
                                                "You  can not perform this operation. please check with one of your team admins"),
                                            success=False)
        except Exception as e:
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)

    @http.route(['/rest_api/v1/permissions/balance'], type='http', auth='none', csrf=False, methods=['GET'])
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
        employee = http.request.env['hr.employee'].search(
            [('user_id', '=', user.id)], limit=1)
        if not employee:
            return http_helper.response(code=400,
                                        message=_(
                                            "You Have issue in your employee profile. please check with one of your team admins"),
                                        success=False)
        if not body['date_from'] or not body['date_to']:
            return http_helper.response(code=400, message=_("Enter All required Dates for Permission request"), success=False)
        try:
            emp = []
            number_of_per = employee.contract_id.working_hours.permission_number
            current_date = datetime.strptime(
                body['date_to'], DEFAULT_SERVER_DATETIME_FORMAT)
            current_month = datetime.strptime(
                body['date_to'], DEFAULT_SERVER_DATETIME_FORMAT).month
            date_from = current_date.strftime(
                '%Y-{0}-01'.format(current_month))
            date_to = current_date.strftime(
                '%Y-{0}-01'.format(current_month + 1))
            if current_month == 12:
                date_to = current_date.strftime(
                    '%Y-{0}-31'.format(current_month))
            permissions = http.request.env['hr.personal.permission'].search([
                ('employee_id', '=', employee.id),
                ('state', '=', 'approve'),
                ('date_from', '>=', date_from),
                ('date_to', '<=', date_to)])
            permission_number = number_of_per - len(permissions)
            balance = permission_number if permission_number >= 0 else 0

            return http_helper.response(message="Data Found", data={'balance': balance, 'permission_limit': employee.contract_id.working_hours.permission_hours})
        except Exception as e:
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)

    def permission_number_decrement(self, employee_id, date_from, date_to):
        if employee_id:
            if not employee_id.first_hiring_date:
                raise exceptions.Warning(
                    _('You can not Request Permission The Employee have Not First Hiring Date'))
        if date_to:
            current_date = datetime.strptime(
                date_to, DEFAULT_SERVER_DATETIME_FORMAT)
            current_month = datetime.strptime(
                date_to, DEFAULT_SERVER_DATETIME_FORMAT).month
            date_from = current_date.strftime(
                '%Y-{0}-01'.format(current_month))
            date_to = current_date.strftime(
                '%Y-{0}-01'.format(current_month + 1))
            if current_month == 12:
                date_to = current_date.strftime(
                    '%Y-{0}-31'.format(current_month))
            number_of_per = employee_id.contract_id.working_hours.permission_number
            employee_permissions = http.request.env['hr.personal.permission'].search([
                ('employee_id', '=', employee_id.id),
                ('state', '=', 'approve'),
                ('date_from', '>=', str(date_from)),
                ('date_to', '<=', str(date_to))])

            all_perission = 0
            for rec in employee_permissions:
                all_perission += rec.duration

                if rec.date_to and item.date_to:
                    permission_date1 = datetime.strptime(rec.date_to,
                                                         DEFAULT_SERVER_DATETIME_FORMAT).date()
                    date_to_value1 = datetime.strptime(
                        item.date_to, DEFAULT_SERVER_DATETIME_FORMAT).date()

                    if permission_date1 == date_to_value1:
                        raise exceptions.Warning(
                            _('Sorry You Have Used All Your Permission In This Day you have one permission per a Day'))

            if number_of_per > all_perission:

                return round(number_of_per - all_perission, 2)
            else:

                raise ValidationError(
                    _('Sorry You Have Used All Your Permission Hours In This Month'))

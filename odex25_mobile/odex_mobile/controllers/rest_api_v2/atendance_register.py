# -*- coding: utf-8 -*-
import logging

from odoo import http, _
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.http import request
from ...http_helper import http_helper
from ...validator import validator


_logger = logging.getLogger(__name__)


class HrAttendanceRegisterAPI(http.Controller):
    
    def _check_required_fields(self, body, required_fields):
        missing_fields = [f for f in required_fields if f not in body or body.get(f) in (False, None, '')]

        msg = {
            "action_type": _("The field 'Action Type' is required."),
            "action_date": _("The field 'Action Date' is required."),
            "register_date": _("The field 'Register Date' is required.")
        }

        if missing_fields:
            messages = [msg.get(field, _("Missing field: %s") % field) for field in missing_fields]
            return False, _("Missing required fields: %s") % ", ".join(messages)

        return True, ""

        
    def get_lable_selection(self, rec, field_name, state):
        return dict(rec._fields[field_name]._description_selection(http.request.env)).get(state)
    
    def _get_attendance_return_data(self, rec):
        return {
            "id": rec.id,
            "employee_id": rec.employee_id.id,
            "employee_name": rec.employee_id.name,
            "action_type": rec.action_type,
            "action_type_name": self.get_lable_selection(rec, 'action_type', rec.action_type),
            "action_date": str(rec.action_date),
            "note_text": rec.note_text or "",
            "register_date": str(rec.register_date),
            "state": rec.state,
            'state_name': self.get_lable_selection(rec, 'state', rec.state),
        }

    @http.route(['/rest_api/v2/hr_attendance_register'], type='http', auth='none', csrf=False, methods=['GET'])
    def get_all_attendance(self,approvel=None, done=None, **kw):
        http_method, body, headers, token = http_helper.parse_request()
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])

        user = validator.verify(token)
        if not user:
            return http_helper.response(code=401, message=_("Authentication failed or user is not allowed."), success=False)

        employee = http.request.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
        if not employee:
            return http_helper.response(code=400, message=_(
                "You Have issue in your employee profile. please check with one of your team admins"), success=False)
        try:
            page = int(kw.get("page", 1))
            sort = kw.get("sort", "")
            filters_str = kw.get("filters", "")
            page, offset, limit, prev = validator.get_page_pagination(page)

            domain = [('employee_id', '=', employee.id)]
            if approvel:
                domain=[('state', 'not in', ['hr_manager','refused','draft']),('employee_id', '!=', employee.id)]
            elif done:
                domain = [('state', 'in', ['hr_manager','refused']), ('employee_id', '!=', employee.id)]

            if filters_str:
                for part in filters_str.split(";"):
                    if "=" in part:
                        k, v = part.split("=", 1)
                        if ',' in v:
                            domain.append((k.strip(), "in", v.split(',')))
                        else:
                            domain.append((k.strip(), "=", v.strip()))

            order = "action_date desc"
            if sort:
                order = sort[1:] + " desc" if sort.startswith("-") else sort + " asc"

            AttObj = request.env["hr.attendance.register"].with_user(user.id)
            records = AttObj.search(domain, offset=offset, limit=limit, order=order)
            all_records = AttObj.search_count(domain)
            result_list = [self._get_attendance_return_data(r) for r in records]
            params = []
            if approvel:
                params.append("approvel=%s" % approvel)
            if done:
                params.append("done=%s" % done)
            next_page = validator.get_page_pagination_next(page, all_records)
            # next_url = f"/rest_api/v2/hr_attendance_register?page={next_page}" if next_page else False
            # prev_url = f"/rest_api/v2/hr_attendance_register?page={prev}" if prev else False
            next_url = f"/rest_api/v2/hr_attendance_register?page={next_page}&{'&'.join(params)}" if next_page else False
            prev_url = f"/rest_api/v2/hr_attendance_register?page={prev}&{'&'.join(params)}" if prev else False

            return http_helper.response(message=_("Attendance retrieved successfully"), data={
                'links': {'prev': prev_url, 'next': next_url},
                'count': len(records) ,
                'total': all_records,
                'results': result_list
            })

        except (UserError, AccessError, ValidationError) as e:
            request.env.cr.rollback()
            return http_helper.response(code=400, message=str(e), success=False)
        except Exception as e:
            request.env.cr.rollback()
            _logger.exception("Error creating mission: %s", e)
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=500, message=message)

    @http.route(['/rest_api/v2/hr_attendance_register'], type='http', auth='none', csrf=False, methods=['POST'])
    def create_attendance(self, **kw):
        http_method, body, headers, token = http_helper.parse_request()
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])

        user = validator.verify(token)
        if not user:
            return http_helper.response(code=401, message=_("Authentication failed or user is not allowed."), success=False)
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)

        required_fields = [ "action_type", "action_date", "register_date", ]
        valid, msg = self._check_required_fields(body, required_fields)
        if not valid:
            return http_helper.response(code=400, message=msg, success=False)

        try:
            vals = {
                "action_type": body.get("action_type"),
                "action_date": body.get("action_date"),
                "note_text": body.get("note_text"),
                "register_date": body.get("register_date"),
                "state": body.get("state", "draft"),
                "employee_id": employee.id,
            }
            record = request.env['hr.attendance.register'].sudo().create(vals)
            # call all on change method needed
            record.chick_all_employees()
            return http_helper.response(message=_("Attendance created successfully"), data=self._get_attendance_return_data(record))
        except (UserError, AccessError, ValidationError) as e:
            request.env.cr.rollback()
            return http_helper.response(code=400, message=str(e), success=False)
        except Exception as e:
            request.env.cr.rollback()
            _logger.exception("Error creating attendance: %s", e)
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=500, message=message)

    @http.route(['/rest_api/v2/hr_attendance_register/<int:rec_id>'], type='http', auth='none', csrf=False, methods=['GET'])
    def get_single_attendance(self, rec_id, **kw):
        http_method, body, headers, token = http_helper.parse_request()
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])

        user = validator.verify(token)
        if not user:
            return http_helper.response(code=401, message=_("Authentication failed or user is not allowed."), success=False)

        try:
            rec = request.env['hr.attendance.register'].sudo().browse(rec_id)
            if not rec.exists():
                return http_helper.response(code=404, message="Record not found", success=False)
            return http_helper.response(message="Success", data=self._get_attendance_return_data(rec))
        except (UserError, AccessError, ValidationError) as e:
            request.env.cr.rollback()
            return http_helper.response(code=400, message=str(e), success=False)
        except Exception as e:
            request.env.cr.rollback()
            _logger.exception("Error creating mission: %s", e)
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=500, message=message)
    
    @http.route(['/rest_api/v2/hr_attendance_register/<int:rec_id>'], type='http', auth='none', csrf=False, methods=['PUT', 'PATCH'])
    def update_attendance(self, rec_id, **kw):
        http_method, body, headers, token = http_helper.parse_request()
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])

        user = validator.verify(token)
        if not user:
            return http_helper.response(code=401, message=_("Authentication failed or user is not allowed."), success=False)
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
        required_fields = [ "action_type", "action_date", "register_date", ]
        valid, msg = self._check_required_fields(body, required_fields)
        if not valid:
            return http_helper.response(code=400, message=msg, success=False)

        try:
            rec = request.env['hr.attendance.register'].sudo().browse(rec_id)
            if not rec.exists():
                return http_helper.response(code=404, message="Record not found", success=False)
            rec.write({key: body[key] for key in body if key in rec._fields})
            return http_helper.response(message="Updated", data=self._get_attendance_return_data(rec))
        except (UserError, AccessError, ValidationError) as e:
            request.env.cr.rollback()
            return http_helper.response(code=400, message=str(e), success=False)
        except Exception as e:
            request.env.cr.rollback()
            _logger.exception("Error updating attendance: %s", e)
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=500, message=message)

    @http.route(['/rest_api/v2/hr_attendance_register/<int:rec_id>'], type='http', auth='none', csrf=False, methods=['DELETE'])
    def delete_attendance(self, rec_id, **kw):
        http_method, body, headers, token = http_helper.parse_request()
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])

        user = validator.verify(token)
        if not user:
            return http_helper.response(code=401, message=_("Authentication failed or user is not allowed."), success=False)

        try:
            rec = request.env['hr.attendance.register'].sudo().browse(rec_id)
            if not rec.exists():
                return http_helper.response(code=404, message="Record not found", success=False)
            rec.unlink()
            return http_helper.response(message="Deleted successfully", data={})
        except (UserError, AccessError, ValidationError) as e:
            request.env.cr.rollback()
            return http_helper.response(code=400, message=str(e), success=False)
        except Exception as e:
            request.env.cr.rollback()
            _logger.exception("Error creating mission: %s", e)
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=500, message=message)

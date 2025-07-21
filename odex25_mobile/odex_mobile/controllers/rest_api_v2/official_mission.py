# -*- coding: utf-8 -*-
import logging

from odoo import http, _
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.http import request
from ...http_helper import http_helper
from ...validator import validator
from datetime import date, datetime
from ast import literal_eval

_logger = logging.getLogger(__name__)


def convert_dates_in_data(data):
    if isinstance(data, dict):
        for key, value in data.items():
            data[key] = convert_dates_in_data(value)
        return data
    elif isinstance(data, list):
        return [convert_dates_in_data(item) for item in data]
    elif isinstance(data, (date, datetime)):
        return data.isoformat()
    else:
        return data


class HrOfficialMissionController(http.Controller):
    """
    Example Controller for HR Official Mission CRUD Endpoints:
      1.1. Create Mission              (POST   /rest_api/v2/hr_official_mission)
      1.2. Get All Missions (Paginate) (GET    /rest_api/v2/hr_official_mission)
      1.3. Get Mission by ID           (GET    /rest_api/v2/hr_official_mission/<id>)
      1.4. Update Mission              (PATCH  /rest_api/v2/hr_official_mission/<id>)
      1.5. Delete Mission              (DELETE /rest_api/v2/hr_official_mission/<id>)
    """

    def get_lable_selection(self, rec, field_name, state):
        return dict(rec._fields[field_name]._description_selection(http.request.env)).get(state)

    def _get_mission_return_data(self, mission):
        """
        Build the dictionary of fields to return in mission responses.
        This can be expanded according to your business needs.
        """
        res = {
            "id": mission.id,
            "date": mission.date or False,
            "move_type_selection": dict(
                mission._fields['move_type']._description_selection(
                    http.request.env)),
            "date_from": mission.date_from or False,
            "date_to": mission.date_to or False,
            "hour_from": mission.hour_from or 0.0,
            "hour_to": mission.hour_to or 0.0,
            "date_duration": mission.date_duration or 0.0,
            "duration_type": mission.duration_type or "",
            "hour_duration": mission.hour_duration or 0.0,
            "balance": mission.balance or 0.0,
            "early_exit": mission.early_exit or False,
            "mission_purpose": mission.mission_purpose or "",
            "state": mission.state or "",
            'state_name': self.get_lable_selection(mission, 'state', mission.state),
            "move_type": mission.move_type or "",
            "move_type_name": self.get_lable_selection(mission, 'move_type', mission.move_type),
            "department_id": mission.department_id.ids,
            "employee_ids": [],
            "approved_by": mission.approved_by.id if mission.approved_by else None,
            "approved_by_name": mission.approved_by.name if mission.approved_by else None,
            "refused_by": mission.refused_by.id if mission.refused_by else None,
            "refused_by_name": mission.refused_by.name if mission.refused_by else None,
            "mission_type": mission.mission_type.id if mission.mission_type else None,
            "mission_type_name": mission.mission_type.name if mission.mission_type else None,
            "country_id": mission.country_id.id if mission.country_id else None,
            "country_name": mission.country_id.name if mission.country_id else None,
            "ticket_insurance": mission.ticket_insurance or "",
            "car_insurance": mission.car_insurance or "",
            "self_car": mission.self_car or "",
            "car_type": mission.car_type or "",
            "rent_days": mission.rent_days or 0,
            "max_rent": mission.max_rent or 0,
            "visa": mission.visa or "",
            "note": mission.note or "",
            "course_name": mission.course_name.id if mission.course_name else None,
            "course_name_name": mission.course_name.name if mission.course_name else None,
            "process_type": mission.process_type or "",
            "train_category": mission.train_category or "",
            "partner_id": mission.partner_id.id if mission.partner_id else None,
            "partner_name": mission.partner_id.name if mission.partner_id else None,
            "destination": mission.destination.id if mission.destination else None,
            "destination_name": mission.destination.name if mission.destination else None,
            "issuing_ticket": mission.issuing_ticket or "",
            "ticket_cash_request_type": mission.ticket_cash_request_type.id if mission.ticket_cash_request_type else None,
            "ticket_cash_request_type_name": mission.ticket_cash_request_type.name if mission.ticket_cash_request_type else None,
            "ticket_cash_request_for": mission.ticket_cash_request_for or "",
            "Training_cost": mission.Training_cost or 0.0,
            "appraisal_check": mission.appraisal_check or False,
            "Tra_cost_invo_id": mission.Tra_cost_invo_id.id if mission.Tra_cost_invo_id else None,
            "max_of_employee": mission.max_of_employee or 0,
            "min_of_employee": mission.min_of_employee or 0,
            "employee_id": mission.employee_id.id if mission.employee_id else None,
            "employee_name": mission.employee_id.name if mission.employee_id else None,
            "reference": mission.reference or "",
            "company_id": mission.company_id.id if mission.company_id else None,
            "company_name": mission.company_id.name if mission.company_id else None,
        }
        res = convert_dates_in_data(res)

        # Build One2many list (hr.official.mission.employee)
        employee_lines = []
        for line in mission.employee_ids:
            employee_lines.append({
                "date_from": line.date_from or False,
                "date_to": line.date_to or False,
                "days": line.days or 0,
                "hour_from": line.hour_from or 0,
                "hour_to": line.hour_to or 0,
                "hours": line.hours or 0,
                "day_price": line.day_price or 0,
                "hour_price": line.hour_price or 0,
                "amount": line.amount or 0,
                "fees_amount": line.fees_amount or 0,
                "appraisal_id": line.appraisal_id.id if line.appraisal_id else None,
                "appraisal_name": line.appraisal_id.name if line.appraisal_id else None,
                "appraisal_result": line.appraisal_result.id if line.appraisal_result else None,
                "employee_id": line.employee_id.id if line.employee_id else None,
                "employee_name": line.employee_id.name if line.employee_id else None,
                "account_move_id": line.account_move_id.id if line.account_move_id else None,
                "advantage_id": line.advantage_id.id if line.advantage_id else None,
                "train_cost_emp": line.train_cost_emp or 0,
                "total_hours": line.total_hours or 0,
            })
        employee_lines = convert_dates_in_data(employee_lines)
        res["employee_ids"] = employee_lines

        return res

    def _prepare_employee_ids(self, employee_ids_list):
        """
        Convert the list of dictionaries (employee lines) from the request body
        into the Odoo-compliant One2many / Many2many commands.
        Each line => (0, 0, {...fields...}).
        """
        commands = []
        for line in employee_ids_list or []:
            cmd_vals = {
                "date_from": line.get("date_from"),
                "date_to": line.get("date_to"),
                "days": line.get("days", 0),
                "hour_from": line.get("hour_from", 0),
                "hour_to": line.get("hour_to", 0),
                "hours": line.get("hours", 0),
                "day_price": line.get("day_price", 0),
                "hour_price": line.get("hour_price", 0),
                "amount": line.get("amount", 0),
                "fees_amount": line.get("fees_amount", 0),
                "appraisal_id": line.get("appraisal_id") or False,
                "appraisal_result": line.get("appraisal_result") or False,
                "employee_id": line.get("employee_id") or False,
                "account_move_id": line.get("account_move_id") or False,
                "advantage_id": line.get("advantage_id") or False,
                "train_cost_emp": line.get("train_cost_emp", 0),
                "total_hours": line.get("total_hours", 0),
            }
            cmd_vals = convert_dates_in_data(cmd_vals)
            commands.append((0, 0, cmd_vals))
        return commands

    # ----------------------------------------------------------
    # 1.1 Create Mission (POST)
    # ----------------------------------------------------------
    @http.route(['/rest_api/v2/hr_official_mission'],
                type='http', auth='none', csrf=False, methods=['POST'])
    def create_mission(self, **kw):
        http_method, body, headers, token = http_helper.parse_request()
        # 1) Check Token
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])
        user = validator.verify(token)
        if not user:
            return http_helper.response(code=400,
                                        message=_("Authentication failed or user is not allowed."),
                                        success=False)
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
        # 2) Validate/Parse Body
        # Required fields check, e.g. 'date_from', 'date_to', etc.
        required_fields = ["date", "date_from", "date_to", "hour_from", "hour_to",
                           "mission_type"]
        missing_fields = [f for f in required_fields if f not in body]
        if missing_fields:
            return http_helper.response(
                code=400,
                message=_("Missing required fields: %s") % ", ".join(missing_fields),
                success=False
            )

        # 3) Create the record in Odoo
        try:
            with request.env.cr.savepoint():
                # Convert department_id from a list to commands if needed
                # department_ids = body.get("department_id", [])
                # if department_ids and isinstance(department_ids, list):
                #     # For many2many, use [(6, 0, list_of_ids)]
                #     department_val = [(6, 0, department_ids)]
                # else:
                #     department_val = False

                # Convert employee_ids to one2many lines
                # employee_lines = self._prepare_employee_ids(body.get("employee_ids", []))

                # vals = {
                #     "date": body["date"],
                #     "date_from": body["date_from"],
                #     "date_to": body["date_to"],
                #     "hour_from": body["hour_from"],
                #     "hour_to": body["hour_to"],
                #     "date_duration": body.get("date_duration", 0),
                #     "hour_duration": body.get("hour_duration", 0),
                #     "balance": body.get("balance", 0),
                #     "early_exit": body.get("early_exit", False),
                #     "mission_purpose": body.get("mission_purpose", ""),
                #     # "move_type": body["move_type"],
                #     "department_id": department_val,
                #     "employee_ids": employee_lines,
                #     "approved_by":  int(body.get("approved_by")) if body.get("approved_by") else False,
                #     "refused_by": int(body.get("refused_by")) if body.get("refused_by") else False,
                #     "mission_type": int(body["mission_type"]),
                #     "country_id": int(body.get("country_id")) if body.get("country_id") else False,
                #     "ticket_insurance": body.get("ticket_insurance", ""),
                #     "car_insurance": body.get("car_insurance", ""),
                #     "self_car": body.get("self_car", ""),
                #     "car_type": body.get("car_type", ""),
                #     "rent_days": body.get("rent_days", 0),
                #     "max_rent": body.get("max_rent", 0),
                #     "visa": body.get("visa", ""),
                #     "note": body.get("note", ""),
                #     "course_name": body.get("course_name") or False,
                #     "process_type": body.get("process_type", ""),
                #     "train_category": body.get("train_category", ""),
                #     "partner_id":  int(body.get("partner_id")) if body.get("partner_id") else False,
                #     "issuing_ticket": body.get("issuing_ticket", ""),
                #     "ticket_cash_request_type": body.get("ticket_cash_request_type") or False,
                #     "ticket_cash_request_for": body.get("ticket_cash_request_for", ""),
                #     "Training_cost": body.get("Training_cost", 0.0),
                #     "appraisal_check": body.get("appraisal_check", False),
                #     "Tra_cost_invo_id":  int(body.get("Tra_cost_invo_id")) if body.get("Tra_cost_invo_id") else False,
                #     "max_of_employee": body.get("max_of_employee", 0),
                #     "min_of_employee": body.get("min_of_employee", 0),
                #     "employee_id": employee.id,
                #     "reference": body.get("reference", ""),
                #     "company_id": 1,
                #     # attachments? see example below
                # }

                # Create the record
                # Prepare the response

                mission_type = body.get('mission_type')
                mission_purpose = body.get('mission_purpose','')
                date_from = body.get('date_from')
                date_to = body.get('date_to')
                hour_from = body.get('hour_from', 8)
                hour_to = body.get('hour_to', 16)
                destination_type = body.get('destination')
                try:
                    hour_from = float(body.get('hour_from') or 8)
                    if hour_from == 0.0:
                        hour_from = 8.0
                except:
                    hour_from = 8.0

                try:
                    hour_to = float(body.get('hour_to') or 16)
                    if hour_to == 0.0:
                        hour_to = 16.0
                except:
                    hour_to = 16.0

                mission = request.env['hr.official.mission'].sudo().create({
                    'mission_type': int(mission_type),
                    'date_from': date_from,
                    'date_to': date_to,
                    'hour_from': hour_from,
                    'hour_to': hour_to,
                    'destination': int(destination_type),
                    'employee_id': employee.id,
                    'process_type': 'especially_hours',
                    'mission_purpose':mission_purpose
                })
                if mission:
                    mission._get_mission_no()
                    mission._add_process_type()

                mission_employee = request.env['hr.official.mission.employee'].sudo().create({
                    'employee_id': employee.id,
                    'official_mission_id': mission.id,
                    'date_from': date_from,
                    'date_to': date_to,
                    'hour_from': hour_from,
                    'hour_to': hour_to,
                    'days': mission.date_duration,
                    'hours': mission.hour_duration,
                })
                if mission_employee:
                    mission_employee.compute_number_of_days()
                    mission_employee.compute_number_of_hours()
                    mission_employee.compute_day_price()
                    mission_employee.compute_Training_cost_emp()
                    mission_employee.chick_not_overtime()

                mis = request.env['hr.official.mission'].sudo().search([('id', '=', mission.id)])

                data = self._get_mission_return_data(mis)
                # Return success
                return http_helper.response(
                    message=_("Mission created successfully"),
                    data=data
                )

        except (UserError, AccessError, ValidationError) as e:
            request.env.cr.rollback()
            return http_helper.response(code=400, message=str(e), success=False)
        except Exception as e:
            request.env.cr.rollback()
            _logger.exception("Error creating mission: %s", e)
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=500, message=message)

    # ----------------------------------------------------------
    # 1.2 Get All Missions (List with Pagination)
    # ----------------------------------------------------------
    @http.route(['/rest_api/v2/hr_official_mission'],
                type='http', auth='none', csrf=False, methods=['GET'])
    def get_all_missions(self,done=None, **kw):
        """
        Query parameters:
          page   (optional, default=1)
          limit  (optional, default=10)
          sort   (optional, e.g. 'date_from', '-state', etc.)
          filters (optional, e.g. 'state=draft' or multiple conditions you parse)
        """
        http_method, body, headers, token = http_helper.parse_request()
        # 1) Check Token
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])
        user = validator.verify(token)
        if not user:
            return http_helper.response(code=400,
                                        message=_("Authentication failed or user is not allowed."),
                                        success=False)

        employee = http.request.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
        if not employee:
            return http_helper.response(code=400, message=_(
                "You Have issue in your employee profile. please check with one of your team admins"), success=False)
        try:
            # 2) Build domain & pagination
            page = int(kw.get('page', 1))
            approvel = kw.get('approvel', 0)
            # done = kw.get('done', 0)
            sort = kw.get('sort')  # e.g. 'date_from' or '-state'
            filters_str = kw.get('filters')
            page, offset, limit, prev = validator.get_page_pagination(page)

            domain = [('employee_id', '=', employee.id)]
            if approvel:
                domain=[('state', 'not in', ['approve','refused','draft']),('employee_id', '!=', employee.id)]
            elif done:
                domain = [('state', 'in', ['approve','refused']), ('employee_id', '!=', employee.id)]

            if filters_str:
                # Very basic parse; adapt as you like.
                parts = filters_str.split(';')
                for p in parts:
                    if '=' in p:
                        key, val = p.split('=', 1)
                        domain.append((key.strip(), '=', val.strip()))
            domain.append(('process_type', '=', 'especially_hours'))

            offset = (page - 1) * limit if page > 0 else 0
            order = "create_date desc"
            if sort:
                # if user specified '-field', interpret as descending
                if sort.startswith('-'):
                    order = sort[1:] + " desc"
                else:
                    order = sort + " asc"

            # 3) Search & count
            Mission = request.env['hr.official.mission'].with_user(user.id)
            missions = Mission.search(domain, offset=offset, limit=limit, order=order)
            all_missions = Mission.search_count(domain)
            # 4) Build response data
            data_list = []
            for mis in missions:
                print("process_type", mis.process_type)
                data_list.append(self._get_mission_return_data(mis))
            data_list = convert_dates_in_data(data_list)

            params = []
            if approvel:
                params.append("approvel=%s" % approvel)
            if done:
                params.append("done=%s" % done)

            next_page = validator.get_page_pagination_next(page, all_missions)
            # next_url = "/rest_api/v2/employee_other_request?approvel=%s&done=%s&page=%s" % (
            #     approvel,done, next_page) if next_page else False
            # prev_url = "/rest_api/v2/employee_other_request?approvel=%s&done=%s&page=%s" % (approvel,done, prev) if prev else False
            next_url = f"/rest_api/v2/hr_official_mission?page={next_page}&{'&'.join(params)}" if next_page else False
            prev_url = f"/rest_api/v2/hr_official_mission?page={prev}&{'&'.join(params)}" if prev else False
            data = {
                'links': {
                    'prev': prev_url,
                    'next': next_url,
                },
                'count': limit,
                'results': {
                    'officialMission': data_list,
                }
            }
            return http_helper.response(
                message=_("All missions retrieved."),
                data=data
            )
        except (UserError, AccessError, ValidationError) as e:
            request.env.cr.rollback()
            return http_helper.response(code=400, message=str(e), success=False)
        except Exception as e:
            request.env.cr.rollback()
            _logger.exception("Error getting missions list: %s", e)
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=500, message=message)

    # ----------------------------------------------------------
    # 1.3 Get Mission by ID
    # ----------------------------------------------------------
    @http.route(['/rest_api/v2/hr_official_mission/<int:mission_id>'],
                type='http', auth='none', csrf=False, methods=['GET'])
    def get_mission_by_id(self, mission_id, **kw):
        http_method, body, headers, token = http_helper.parse_request()
        # 1) Check Token
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])
        user = validator.verify(token)
        if not user:
            return http_helper.response(code=400,
                                        message=_("Authentication failed or user is not allowed."),
                                        success=False)

        try:
            mission = request.env['hr.official.mission'].sudo().search([('id', '=', mission_id)], limit=1)
            if not mission:
                return http_helper.response(code=404, message="Mission not found", success=False)

            data = self._get_mission_return_data(mission)
            return http_helper.response(
                message=_("Mission retrieved successfully"),
                data=data
            )
        except (UserError, AccessError, ValidationError) as e:
            request.env.cr.rollback()
            return http_helper.response(code=400, message=str(e), success=False)
        except Exception as e:
            request.env.cr.rollback()
            _logger.exception("Error getting mission by ID: %s", e)
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=500, message=message)

    # ----------------------------------------------------------
    # 1.4 Update Mission (PATCH)
    # ----------------------------------------------------------
    @http.route(['/rest_api/v2/hr_official_mission/<int:mission_id>'],
                type='http', auth='none', csrf=False, methods=['PATCH'])
    def update_mission(self, mission_id, **kw):
        """
        Allows partial update of fields, only updates fields included in the request body.
        Example body:
          {
            "date_to": "2025-02-10",
            "hour_to": 18,
            "balance": 120,
            "mission_purpose": "Updated purpose for the mission."
          }
        """
        http_method, body, headers, token = http_helper.parse_request()
        # 1) Check Token
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])
        user = validator.verify(token)
        if not user:
            return http_helper.response(code=400,
                                        message=_("Authentication failed or user is not allowed."),
                                        success=False)

        try:
            with request.env.cr.savepoint():
                mission = request.env['hr.official.mission'].sudo().search([('id', '=', mission_id)], limit=1)
                if not mission:
                    return http_helper.response(code=404, message="Mission not found", success=False)

                # Build vals only from the body keys we actually have
                vals = {}
                updatable_fields = [
                    "date", "date_from", "date_to", "hour_from", "hour_to",
                    "date_duration", "hour_duration", "balance", "early_exit",
                    "mission_purpose", "state", "move_type", "approved_by",
                    "refused_by", "mission_type", "country_id", "ticket_insurance",
                    "car_insurance", "self_car", "car_type", "rent_days",
                    "max_rent", "visa", "note", "course_name", "process_type",
                    "train_category", "partner_id", "destination", "issuing_ticket",
                    "ticket_cash_request_type", "ticket_cash_request_for",
                    "Training_cost", "appraisal_check", "Tra_cost_invo_id",
                    "max_of_employee", "min_of_employee", "employee_id", "reference",
                    "company_id",
                ]
                # If you need to handle department_id (many2many) or employee_ids (one2many) updates,
                # you can handle them separately or the same way.
                # e.g. if "department_id" in body: create the many2many commands.
                # e.g. if "employee_ids" in body: parse them with _prepare_employee_ids.

                for field_name in updatable_fields:
                    if field_name in body:
                        value = body[field_name]

                        if field_name in ['mission_type', 'destination']:
                            try:
                                value = int(value)
                            except:
                                return http_helper.response(
                                    code=400,
                                    message=_("Invalid type for field '%s': expected integer.") % field_name,
                                    success=False
                                )

                        vals[field_name] = value

                # example for department_id (many2many):
                if "department_id" in body:
                    dep_ids = body["department_id"]
                    if isinstance(dep_ids, list):
                        vals["department_id"] = [(6, 0, dep_ids)]

                # example for employee_ids (one2many lines):
                if "employee_ids" in body and isinstance(body["employee_ids"], list):
                    vals["employee_ids"] = [(5, 0, 0)]  # remove existing lines
                    vals["employee_ids"] += self._prepare_employee_ids(body["employee_ids"])

                mission.write(vals)

                # Return the updated record
                data = self._get_mission_return_data(mission)
                return http_helper.response(
                    message=_("Mission updated successfully"),
                    data=data
                )

        except (UserError, AccessError, ValidationError) as e:
            request.env.cr.rollback()
            return http_helper.response(code=400, message=str(e), success=False)
        except Exception as e:
            request.env.cr.rollback()
            _logger.exception("Error updating mission: %s", e)
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=500, message=message)

    # ----------------------------------------------------------
    # 1.5 Delete Mission (DELETE)
    # ----------------------------------------------------------
    @http.route(['/rest_api/v2/hr_official_mission/<int:mission_id>'],
                type='http', auth='none', csrf=False, methods=['DELETE'])
    def delete_mission(self, mission_id, **kw):
        http_method, body, headers, token = http_helper.parse_request()
        # 1) Check Token
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])
        user = validator.verify(token)
        if not user:
            return http_helper.response(code=400,
                                        message=_("Authentication failed or user is not allowed."),
                                        success=False)

        try:
            with request.env.cr.savepoint():
                mission = request.env['hr.official.mission'].sudo().search([('id', '=', mission_id)], limit=1)
                if not mission:
                    return http_helper.response(code=404, message="Mission not found", success=False)

                mission.unlink()
                return http_helper.response(
                    message=_("Mission deleted successfully"),
                    data={"id": mission_id}
                )
        except (UserError, AccessError, ValidationError) as e:
            request.env.cr.rollback()
            return http_helper.response(code=400, message=str(e), success=False)
        except Exception as e:
            request.env.cr.rollback()
            _logger.exception("Error deleting mission: %s", e)
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=500, message=message)


# ------------------------------------------------------------------
# 2. Related Models (Read-Only)
#    2.1 Mission Type (hr.official.mission.type)
#    2.2 Mission Destination (mission.destination)
#    2.3 Employee Course Name (employee.course.name)
# ------------------------------------------------------------------

class HrOfficialMissionRelatedModelsController(http.Controller):
    """
    Minimal read-only endpoints to retrieve valid IDs from related models
    (mission_type, mission_destination, course_name, etc.)
    """

    # 2.1 Mission Type
    @http.route(['/api/mission_type'], type='http', auth='none', csrf=False, methods=['GET'])
    def get_mission_type_list(self, **kw):
        # No token check here if it is publicly available; otherwise, do similar token checks

        domain = [('special_hours', '=', True)]
        mission_types = request.env["hr.official.mission.type"].sudo().search(domain)
        data = []
        for mt in mission_types:
            data.append({
                "id": mt.id,
                "name": mt.name,
                "duration_type": mt.duration_type,
                "maximum_days": mt.maximum_days,
                "related_with_financial": mt.related_with_financial,
                "day_price": mt.day_price,
                "work_state": mt.work_state,
            })
        return http_helper.response(message="Mission Types", data=data)

    @http.route(['/api/mission_type/<int:mt_id>'], type='http', auth='none', csrf=False, methods=['GET'])
    def get_mission_type_detail(self, mt_id, **kw):
        mt = request.env["hr.official.mission.type"].sudo().search([('id', '=', mt_id)], limit=1)
        if not mt:
            return http_helper.response(code=404, message="Mission Type not found", success=False)
        data = {
            "id": mt.id,
            "name": mt.name,
            "duration_type": mt.duration_type,
            "maximum_days": mt.maximum_days,
            "related_with_financial": mt.related_with_financial,
            "day_price": mt.day_price,
            "work_state": mt.work_state,
        }
        return http_helper.response(message="Mission Type Detail", data=data)

    # 2.2 Mission Destination
    @http.route(['/api/mission_destination'], type='http', auth='none', csrf=False, methods=['GET'])
    def get_mission_destination_list(self, **kw):
        param = request.env['ir.config_parameter'].sudo().get_param('mission.destination.domain', '[]')

        # evaluate the string into a domain list
        try:
            domain = literal_eval(param)
            if not isinstance(domain, list):
                domain = []
        except Exception:
            domain = []
        destinations = request.env["mission.destination"].sudo().search(domain)
        data = []
        for dest in destinations:
            data.append({
                "id": dest.id,
                "name": dest.name,
                "code": dest.code,
                "country_id": dest.country_id.id if dest.country_id else None,
            })
        return http_helper.response(message="Mission Destinations", data=data)

    @http.route(['/api/mission_destination/<int:dest_id>'], type='http', auth='none', csrf=False, methods=['GET'])
    def get_mission_destination_detail(self, dest_id, **kw):
        dest = request.env["mission.destination"].sudo().search([('id', '=', dest_id)], limit=1)
        if not dest:
            return http_helper.response(code=404, message="Destination not found", success=False)
        data = {
            "id": dest.id,
            "name": dest.name,
            "code": dest.code,
            "country_id": dest.country_id.id if dest.country_id else None,
        }
        return http_helper.response(message="Destination Detail", data=data)

    # 2.3 Employee Course Name
    @http.route(['/api/course_name'], type='http', auth='none', csrf=False, methods=['GET'])
    def get_course_name_list(self, **kw):
        courses = request.env["employee.course.name"].sudo().search([])
        data = []
        for c in courses:
            data.append({
                "id": c.id,
                "name": c.name,
                "code": c.code,
            })
        return http_helper.response(message="Course Names", data=data)

    @http.route(['/api/course_name/<int:course_id>'], type='http', auth='none', csrf=False, methods=['GET'])
    def get_course_name_detail(self, course_id, **kw):
        course = request.env["employee.course.name"].sudo().search([('id', '=', course_id)], limit=1)
        if not course:
            return http_helper.response(code=404, message="Course not found", success=False)
        data = {
            "id": course.id,
            "name": course.name,
            "code": course.code,
        }
        return http_helper.response(message="Course Detail", data=data)
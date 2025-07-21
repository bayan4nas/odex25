# -*- coding: utf-8 -*-
import logging
import traceback

from odoo import http, _ ,SUPERUSER_ID
from odoo.exceptions import UserError, AccessError, ValidationError
from odoo.http import request
from ...http_helper import http_helper
from ...validator import validator
from datetime import date, datetime
from odoo.addons.web.controllers.main import ReportController
from werkzeug import exceptions
import json
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

class EmployeeOtherRequest(http.Controller):

    def get_lable_selection(self, rec, field_name, state):
        return dict(rec._fields[field_name]._description_selection(http.request.env)).get(state)

    @http.route(['/rest_api/v2/employeeRequest/types', '/rest_api/v2/employeeRequest/types/<string:key>'], type='http',
                auth='none', csrf=False, methods=['GET'])
    def get_employee_other_request_type(self, key=None):
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
            data = {"other_request_types": dict(
                http.request.env['employee.other.request']._fields['request_type']._description_selection(
                    http.request.env)),
                    "salary_request_print_type": dict(
                        http.request.env['employee.other.request']._fields['print_type']._description_selection(
                            http.request.env)),
                    "salary_request_state": dict(
                        http.request.env['employee.other.request']._fields['state']._description_selection(
                            http.request.env)),
                    "certification_degree": dict(
                        http.request.env['hr.certification']._fields['certification_degree']._description_selection(
                            http.request.env)),
                    "qualification_degree": dict(
                        http.request.env['hr.qualification']._fields['qualification_degree']._description_selection(
                            http.request.env)),
                    "gender": dict(http.request.env['hr.employee.dependent']._fields['gender']._description_selection(
                        http.request.env)),
                    "relation": dict(
                        http.request.env['hr.employee.dependent']._fields['relation']._description_selection(
                            http.request.env)),
                    "nationality": request.env['res.country'].sudo().search([]).read(['id', 'name']),
                    "uni_name_UniversityName": request.env['office.office'].sudo().search([]).read(['id', 'name']),
                    "col_name_College": request.env['hr.college'].sudo().search([]).read(['id', 'name']),
                    "hr_qualification_name": request.env['hr.qualification.name'].sudo().search([]).read(
                        ['id', 'name']),
                    "qualification_specification": request.env['qualification.specification'].sudo().search(
                        [('type', '=', 'qualification')]).read(['id', 'name']),
                    "certificate_specification": request.env['qualification.specification'].sudo().search(
                        [("type", "=", "certificate")]).read(['id', 'name']),
                    "membership_type": request.env['membership.types'].sudo().search([]).read(['id', 'name']),
                    "membership_categorys": request.env['membership.categorys'].sudo().search([]).read(['id', 'name']),
                    }
            if key:
                data = {key: data[key]}
            return http_helper.response(message="Data Found", data=data)
        except Exception as e:
            _logger.error(str(e))
            _logger.error(traceback.format_exc())
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)

    @http.route(['/rest_api/v2/employeeRequests/', '/rest_api/v2/employeeRequests/<int:id>'], type='http', auth='none',
                csrf=False, methods=['GET'])
    def get_employee_other_requests(self, id=None, approvel=None, page=None, **kw):
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
            if approvel:
                domain = [('state', '!=', 'draft'), ('employee_id', '!=', employee.id)]
                emp_requests = http.request.env['employee.other.request'].search(domain, order='date desc',
                                                                                 offset=offset, limit=limit)
                count = http.request.env['employee.other.request'].search_count(domain)
            else:
                emp_requests = http.request.env['employee.other.request'].search([('employee_id', '=', employee.id)],
                                                                                 order='date desc', offset=offset,
                                                                                 limit=limit)
                count = http.request.env['employee.other.request'].search_count([('employee_id', '=', employee.id)])
            if id:
                emp_requests = http.request.env['employee.other.request'].search([('id', '=', int(id))],
                                                                                 order='date desc')
                count = http.request.env['employee.other.request'].search_count([('id', '=', int(id))])
            employeeRequests = []
            if emp_requests:
                for s in emp_requests:
                    value = {
                        'id': s.id,
                        'employee_id': s.employee_id.name,
                        'department_id': s.department_id.name,
                        'destination': s.destination,
                        'comment': s.comment,
                        'request_type': s.request_type,
                        'request_type_lable': self.get_lable_selection(s, 'request_type', s.request_type),
                        'state': s.state,
                        'state_name': self.get_lable_selection(s, 'state', s.state),
                    }
                    employee_dependant = []
                    for dep in s.employee_dependant:
                        dep_val = {
                            'name': dep.name or '',
                            'age': dep.age or '',
                            'birthday': str(dep.birthday or ''),
                            'gender': dep.gender or '',
                            'gender_lable': self.get_lable_selection(dep, 'gender', dep.gender),
                            'relation': dep.relation or '',
                            'relation_lable': self.get_lable_selection(dep, 'relation', dep.relation),
                            'nationality': dep.nationality.read(['id', 'name'])[0] or {},
                            'passport_no': dep.passport_no or '',
                            'passport_issue_date': str(dep.passport_issue_date or ''),
                            'passport_expire_date': str(dep.passport_expire_date or ''),
                            # 'remarks': dep.remarks,
                            'degree_medical_insu': dep.degree_medical_insu or '',
                            'medical_insurance_num': dep.medical_insurance_num or '',
                            'identity_num': dep.identity_num or '',
                            'has_ticket': dep.has_ticket,
                            # 'attachment': dep.attachment,

                        }
                        employee_dependant.append(dep_val)
                    if s.employee_dependant:
                        value['employee_dependant'] = employee_dependant
                    qualification_employee = []
                    for qua in s.qualification_employee:
                        qua_val = {
                            'uni_name_UniversityName': qua.uni_name.read(['id', 'name'])[0] or {},
                            'col_name_CollegeName': qua.col_name.read(['id', 'name'])[0] or {},
                            'prg_status': qua.prg_status or '',
                            'comp_date': str(qua.comp_date or ''),
                            'end_date': str(qua.end_date or ''),
                            'degree': qua.degree or 0.0,
                            'contact_name': qua.contact_name or '',
                            'contact_phn': qua.contact_phn or '',
                            'contact_email': qua.contact_email or '',
                            'country_name': qua.country_name.read(['id', 'name'])[0] or {},
                            'qualification_degree': qua.qualification_degree or '',
                            'qualification_degree_lable': self.get_lable_selection(qua, 'qualification_degree',
                                                                                   qua.qualification_degree),
                            'qualification_specification_id': qua.qualification_specification_id.read(['id', 'name'])[
                                                                  0] or {},
                            'qualification_id': qua.qualification_id.read(['id', 'name'])[0] or {},
                            # 'attachment': qua.attachment,

                        }
                        qualification_employee.append(qua_val)
                    if s.qualification_employee:
                        value['qualification_employee'] = qualification_employee
                    certification_employee = []
                    for cer in s.certification_employee:
                        cer_val = {
                            'id': cer.id,
                            'cer_name': cer.car_name or '',
                            'certification_specification': cer.certification_specification_id.name or '',
                            'issue_org': cer.issue_org or '',
                            'certification_degree': cer.certification_degree or '',
                            'certification_degree_lable': self.get_lable_selection(cer, 'certification_degree',
                                                                                   cer.certification_degree),
                            'issue_date': str(cer.issue_date or ''),
                            'exp_date': str(cer.exp_date or ''),
                            'country_id': cer.country_name.read(['id', 'name'])[0] or {},
                        }
                        certification_employee.append(cer_val)
                    if s.certification_employee:
                        value['certification_employee'] = certification_employee

                    employeeRequests.append(value)
            next = validator.get_page_pagination_next(page, count)
            url = "/rest_api/v2/employeeRequests?approvel=%s&page=%s" % (approvel, next) if next else False
            prev_url = "/rest_api/v2/employeeRequests?approvel=%s&page=%s" % (approvel, prev) if prev else False
            data = {'links': {'prev': prev_url, 'next': url, },
                    'count': count,
                    'results': {'employeeRequests': employeeRequests, }}
            return http_helper.response(message="Data Found", data=data)

        except Exception as e:
            _logger.error(str(e))
            _logger.error(traceback.format_exc())
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)

    @http.route([
        '/rest_api/v2/report/<reportname>/<docids>',
        '/rest_api/v2/report/',
    ], type='http', auth='none')
    def report_routes(self, reportname=None, docids=None, **data):
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
        if not reportname:
            return http_helper.response(code=400, message=_(
                "please sent report name . please check with one of your team admins"), success=False)
        report = request.env['ir.actions.report']._get_report_from_name(reportname)
        if docids:
            docids = [int(i) for i in docids.split(',')]
        else:
            return http_helper.response(code=400, message=_(
                "please sent id recrod print report. please check with one of your team admins"), success=False)
        if report:
            model = report.model_id.model or report.model
            if len(request.env[model].search([('id', 'in', docids)])) < len(docids):
                return http_helper.response(code=400, message=_(
                    "You Have issue in your  data not found. please check with one of your team admins"), success=False)
        else:
            return http_helper.response(code=400, message=_(
                "You Have issue in your  report not found. please check with one of your team admins"), success=False)
        try:
            context = dict(request.env.context)
            pdf = report.with_context(context)._render_qweb_pdf(docids, data=data)[0]
            pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf))]
            return request.make_response(pdf, headers=pdfhttpheaders)
        except Exception as e:
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)


class EmployeeOtherRequestController(http.Controller):
    """
    Controller for Employee Other Requests (employee.other.request)

    Endpoints:
      3.1 Create Request                (POST   /rest_api/v2/employee_other_request)
      3.2 Get All Requests (Paginate)   (GET    /rest_api/v2/employee_other_request)
      3.3 Get Request by ID             (GET    /rest_api/v2/employee_request/<id>)
      3.4 Update Request                (PATCH  /rest_api/v2/employee_other_request/<id>)
      3.5 Delete Request                (DELETE /rest_api/v2/employee_other_request/<id>)
    """
    def get_lable_selection(self, rec, field_name, state):
        return dict(rec._fields[field_name]._description_selection(http.request.env)).get(state)
    # --------------------------------------------
    # Utilities
    # --------------------------------------------
    def _prepare_employee_dependant_lines(self, dependant_list):
        """
        Convert the list of employee_dependant dicts from the request
        into Odoo One2many commands: (0, 0, {vals})
        """
        commands = []
        for dep in dependant_list or []:
            commands.append((0, 0, {
                "name": dep.get("name"),
                "relation": dep.get("relation"),
                "date_of_birth": dep.get("date_of_birth"),
            }))
        return commands

    def _prepare_qualification_employee_lines(self, quals_list):
        """
        Convert the list of qualification_employee dicts from the request
        into One2many commands for hr.qualification model
        """
        commands = []
        for q in quals_list or []:
            commands.append((0, 0, {
                "qualification_name": q.get("qualification_name"),
                "date_obtained": str(q.get("date_obtained","")),
                "institute": q.get("institute"),
            }))
        return commands

    def _prepare_certification_employee_lines(self, certs_list):
        """
        Convert the list of certification_employee dicts from the request
        into One2many commands for hr.certification model
        """
        commands = []
        for c in certs_list or []:
            commands.append((0, 0, {
                "certification_name": c.get("certification_name"),
                "date_obtained":str( c.get("date_obtained","")),
                "organization": c.get("organization"),
            }))
        return commands

    def _get_request_return_data(self, req):
        """
        Build a dictionary of fields to return for a single record
        (similar to the detailed response in 3.3 Get Request by ID)
        """
        dict_type_report_name={
            'salary_define/detail':'employee_requests.action_report_employee_identification',
            'salary_define/no_detail':'employee_requests.action_report_employee_identify_2',
            'salary_define/no_salary':'employee_requests.action_report_employee_identify_3',
            'salary_fixing':'employee_requests.salary_conf_report_act',
        }
        define_key = f'{req.request_type}/{req.print_type}' if req.request_type=='salary_define' else req.request_type
        res = {
            "id": req.id,
            "from_hr": req.from_hr,
            "date": req.date,
            "comment": req.comment or "",
            'request_type': req.request_type,
            'request_type_lable': self.get_lable_selection(req, 'request_type', req.request_type),
            'state': req.state,
            'state_name': self.get_lable_selection(req, 'state', req.state),
            "employee_id": req.employee_id.id if req.employee_id else None,
            "employee_name": req.employee_id.name if req.employee_id else None,
            "employee_dependant": [],
            "qualification_employee": [],
            "certification_employee": [],
            "create_insurance_request": req.create_insurance_request,
            "print_type": req.print_type,
            "print_type_name": self.get_lable_selection(req, 'print_type', req.print_type),
            "destination": req.destination.id if req.destination else None,
            'destination_name': req.destination.name if req.destination else None,
            "parent_request_id": req.parent_request_id.id if req.parent_request_id else None,
            "company_id": req.company_id.id if req.company_id else None,
            "company_name": req.company_id.name if req.company_id else None,
            "report_url": f'/rest_api/v2/public_report/pdf/{dict_type_report_name.get(define_key,"No Report")}/{req.id}'
        }
        res = convert_dates_in_data(res)

        for dep in req.employee_dependant:
            res["employee_dependant"].append({
                'name': dep.name or '',
                'age': dep.age or '',
                'birthday': str(dep.birthday or ''),
                'gender': dep.gender or '',
                'gender_lable': self.get_lable_selection(dep, 'gender', dep.gender),
                'relation': dep.relation or '',
                'relation_lable': self.get_lable_selection(dep, 'relation', dep.relation),
                'nationality': dep.nationality.read(['id', 'name'])[0] or {},
                'passport_no': dep.passport_no or '',
                'passport_issue_date': str(dep.passport_issue_date or ''),
                'passport_expire_date': str(dep.passport_expire_date or ''),
                'degree_medical_insu': dep.degree_medical_insu or '',
                'medical_insurance_num': dep.medical_insurance_num or '',
                'identity_num': dep.identity_num or '',
                'has_ticket': dep.has_ticket,
            })

        for qua in req.qualification_employee:
            res["qualification_employee"].append({
                'uni_name_UniversityName': qua.uni_name.read(['id', 'name'])[0] or {},
                'col_name_CollegeName': qua.col_name.read(['id', 'name'])[0] or {},
                'prg_status': qua.prg_status or '',
                'comp_date': str(qua.comp_date or ''),
                'end_date': str(qua.end_date or ''),
                'degree': qua.degree or 0.0,
                'contact_name': qua.contact_name or '',
                'contact_phn': qua.contact_phn or '',
                'contact_email': qua.contact_email or '',
                'country_name': qua.country_name.read(['id', 'name'])[0] or {},
                'qualification_degree': qua.qualification_degree or '',
                'qualification_degree_lable': self.get_lable_selection(qua, 'qualification_degree',
                                                                       qua.qualification_degree),
                'qualification_specification_id': qua.qualification_specification_id.read(['id', 'name'])[
                                                      0] or {},
                'qualification_id': qua.qualification_id.read(['id', 'name'])[0] or {},
            })
            res["qualification_employee"] = convert_dates_in_data(res["qualification_employee"])
        for cer in req.certification_employee:
            res["certification_employee"].append({
                'id': cer.id,
                'cer_name': cer.car_name or '',
                'certification_specification': cer.certification_specification_id.name or '',
                'issue_org': cer.issue_org or '',
                'certification_degree': cer.certification_degree or '',
                'certification_degree_lable': self.get_lable_selection(cer, 'certification_degree',
                                                                       cer.certification_degree),
                'issue_date': str(cer.issue_date or ''),
                'exp_date': str(cer.exp_date or ''),
                'country_id': cer.country_name.read(['id', 'name'])[0] or {},
            })
            res["certification_employee"] = convert_dates_in_data(res["certification_employee"])

        return res

    # --------------------------------------------
    # 3.1 Create Request (POST)
    # --------------------------------------------
    @http.route(['/rest_api/v2/employee_other_request'],
                type='http', auth='none', csrf=False, methods=['POST'])
    def create_request(self, **kw):
        http_method, body, headers, token = http_helper.parse_request()

        # 1) Check Token
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])
        user = validator.verify(token)

        if not user:
            return http_helper.response(
                code=400,
                message=_("Authentication failed or user is not allowed."),
                success=False
            )
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
        # 2) Validate/Parse Body
        required_fields = ["date", "request_type"]
        missing = [f for f in required_fields if f not in body]
        if missing:
            return http_helper.response(
                code=400,
                message=_("Missing required fields: %s") % ", ".join(missing),
                success=False
            )

        try:
            with request.env.cr.savepoint():
                # Prepare Odoo create vals
                vals = {
                    "from_hr": body.get("from_hr", False),
                    "date": body["date"],
                    "comment": body.get("comment") or "",
                    "request_type": body.get('request_type'),
                    "employee_id": employee.id,
                    "employee_dependant": self._prepare_employee_dependant_lines(body.get("employee_dependant", [])),
                    "qualification_employee": self._prepare_qualification_employee_lines(
                        body.get("qualification_employee", [])),
                    "certification_employee": self._prepare_certification_employee_lines(
                        body.get("certification_employee", [])),
                    "create_insurance_request": body.get("create_insurance_request", False),
                    "print_type": body.get("print_type", ""),
                    "destination": int(body.get("destination")) if body.get("destination") else False,
                    "parent_request_id": int(body.get("parent_request_id")) if body.get("parent_request_id") else False,
                    "company_id": 1,
                }

                # Create record
                new_req = request.env["employee.other.request"].sudo().create(vals)

                # Build success response
                data = self._get_request_return_data(new_req)
                return http_helper.response(
                    message=_("Request created successfully"),
                    data=data
                )

        except (UserError, AccessError, ValidationError) as e:
            request.env.cr.rollback()
            _logger.error("Error creating request: %s", str(e))
            return http_helper.response(code=400, message=str(e), success=False)
        except Exception as e:
            request.env.cr.rollback()
            _logger.exception("Unexpected error while creating request")
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=500, message=message)

    # --------------------------------------------
    # 3.2 Get All Requests (GET) with Pagination
    # --------------------------------------------
    @http.route(['/rest_api/v2/employee_other_request'],
                type='http', auth='none', csrf=False, methods=['GET'])
    def get_all_requests(self,done=None, **kw):
        http_method, body, headers, token = http_helper.parse_request()

        # 1) Check Token
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])
        user = validator.verify(token)
        if not user:
            return http_helper.response(
                code=400,
                message=_("Authentication failed or user is not allowed."),
                success=False
            )

        employee = http.request.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
        if not employee:
            return http_helper.response(code=400, message=_(
                "You Have issue in your employee profile. please check with one of your team admins"), success=False)
        try:
            # 2) Parse Query params
            page = int(kw.get("page", 1))
            sort = kw.get("sort", "")  # e.g. 'date' or '-state'
            approvel = kw.get("approvel", 0)
            # done = kw.get("done", 0)
            filters_str = kw.get("filters", "")  # e.g. 'state=approved'
            page, offset, limit, prev = validator.get_page_pagination(page)
            domain = [('employee_id', '=', employee.id)]
            if approvel:
                domain=[('state', 'not in', ['approved','refuse','draft']),('employee_id', '!=', employee.id)]
            elif done:
                domain = [('state', 'in', ['approved','refuse']), ('employee_id', '!=', employee.id)]
            if filters_str:
                # Very naive filter parser: "state=approved;request_type=insurance"
                for part in filters_str.split(";"):
                    if "=" in part:
                        k, v = part.split("=", 1)
                        if ',' in v:
                            domain.append((k.strip(), "in", v.split(',')))
                        else:
                            domain.append((k.strip(), "=", v.strip()))
            domain.append(('request_type', 'in', ['salary_define', 'salary_fixing']))

            offset = (page - 1) * limit if page > 0 else 0
            order = "create_date desc"
            if sort:
                if sort.startswith("-"):
                    order = sort[1:] + " desc"
                else:
                    order = sort + " asc"

            RequestObj = request.env["employee.other.request"].with_user(user.id)
            records = RequestObj.search(domain, offset=offset, limit=limit, order=order)
            all_records = RequestObj.search_count(domain)
            # Build minimal list
            request_list = []
            for r in records:
                request_list.append(self._get_request_return_data(r))

            request_list = convert_dates_in_data(request_list)

            params = []
            if approvel:
                params.append("approvel=%s" % approvel)
            if done:
                params.append("done=%s" % done)

            next_page = validator.get_page_pagination_next(page, all_records)
            # next_url = "/rest_api/v2/employee_other_request?approvel=%s&done=%s&page=%s" % (
            # approvel,done, next_page) if next_page else False
            # prev_url = "/rest_api/v2/employee_other_request?approvel=%s&done=%s&page=%s" % (approvel,done, prev) if prev else False
            next_url = f"/rest_api/v2/employee_other_request?page={next_page}&{'&'.join(params)}" if next_page else False
            prev_url = f"/rest_api/v2/employee_other_request?page={prev}&{'&'.join(params)}" if prev else False
            data = {
                'links': {
                    'prev': prev_url,
                    'next': next_url,
                },
                'count': limit,
                'results': {
                    'employeeRequests': request_list,
                }
            }
            return http_helper.response(
                message=_("Requests retrieved successfully"),
                data=data
            )

        except (UserError, AccessError, ValidationError) as e:
            request.env.cr.rollback()
            _logger.error("Error getting requests: %s", str(e))
            return http_helper.response(code=400, message=str(e), success=False)
        except Exception as e:
            request.env.cr.rollback()
            _logger.exception("Unexpected error while listing requests")
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=500, message=message)

    # --------------------------------------------
    # 3.3 Get Request by ID (GET)
    #    /rest_api/v2/employee_request/<id>
    # --------------------------------------------
    @http.route(['/rest_api/v2/employee_request/<int:req_id>'],
                type='http', auth='none', csrf=False, methods=['GET'])
    def get_request_by_id(self, req_id, **kw):
        http_method, body, headers, token = http_helper.parse_request()

        # 1) Check Token
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])
        user = validator.verify(token)
        if not user:
            return http_helper.response(
                code=400,
                message=_("Authentication failed or user is not allowed."),
                success=False
            )

        try:
            req = request.env["employee.other.request"].sudo().search([("id", "=", req_id)], limit=1)
            if not req:
                return http_helper.response(code=404, message="Request not found", success=False)

            data = self._get_request_return_data(req)
            return http_helper.response(
                message=_("Request retrieved successfully"),
                data=data
            )

        except (UserError, AccessError, ValidationError) as e:
            request.env.cr.rollback()
            _logger.error("Error getting request by ID: %s", str(e))
            return http_helper.response(code=400, message=str(e), success=False)
        except Exception as e:
            request.env.cr.rollback()
            _logger.exception("Unexpected error while getting request by ID")
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=500, message=message)

    # --------------------------------------------
    # 3.4 Update Request (PATCH)
    #    /rest_api/v2/employee_other_request/<id>
    # --------------------------------------------
    @http.route(['/rest_api/v2/employee_other_request/<int:req_id>'],
                type='http', auth='none', csrf=False, methods=['PATCH'])
    def update_request(self, req_id, **kw):
        """
        Allows partial update of fields present in the request body.
        Example Body:
        {
          "state": "approved",
          "comment": "Request approved by HR.",
          "print_type": "no_salary"
        }
        """
        http_method, body, headers, token = http_helper.parse_request()

        # 1) Check Token
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])
        user = validator.verify(token)
        if not user:
            return http_helper.response(
                code=400,
                message=_("Authentication failed or user is not allowed."),
                success=False
            )

        try:
            with request.env.cr.savepoint():
                req = request.env["employee.other.request"].sudo().search([("id", "=", req_id)], limit=1)
                if not req:
                    return http_helper.response(code=404, message="Request not found", success=False)

                # Build a vals dict for fields that appear in the body
                updatable_fields = [
                    "from_hr", "date", "comment", "state", "request_type",
                    "employee_id", "create_insurance_request", "print_type",
                    "destination", "parent_request_id", "company_id"
                ]
                vals = {}
                for field_name in updatable_fields:
                    if field_name in body:
                        vals[field_name] = int(body[field_name]) if field_name in ["destination", "parent_request_id", "company_id"] else body[field_name]

                # Handle One2many lines if needed
                if "employee_dependant" in body:
                    # Clear existing lines, then add the new ones
                    vals["employee_dependant"] = [(5, 0, 0)]
                    vals["employee_dependant"] += self._prepare_employee_dependant_lines(body["employee_dependant"])
                if "qualification_employee" in body:
                    vals["qualification_employee"] = [(5, 0, 0)]
                    vals["qualification_employee"] += self._prepare_qualification_employee_lines(
                        body["qualification_employee"])
                if "certification_employee" in body:
                    vals["certification_employee"] = [(5, 0, 0)]
                    vals["certification_employee"] += self._prepare_certification_employee_lines(
                        body["certification_employee"])

                req.write(vals)
                updated_data = self._get_request_return_data(req)
                return http_helper.response(
                    message=_("Request updated successfully"),
                    data=updated_data
                )

        except (UserError, AccessError, ValidationError) as e:
            request.env.cr.rollback()
            _logger.error("Error updating request: %s", str(e))
            return http_helper.response(code=400, message=str(e), success=False)
        except Exception as e:
            request.env.cr.rollback()
            _logger.exception("Unexpected error while updating request")
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=500, message=message)

    # --------------------------------------------
    # 3.5 Delete Request (DELETE)
    #    /rest_api/v2/employee_other_request/<int:req_id>
    # --------------------------------------------
    @http.route(['/rest_api/v2/employee_other_request/<int:req_id>'],
                type='http', auth='none', csrf=False, methods=['DELETE'])
    def delete_request(self, req_id, **kw):
        http_method, body, headers, token = http_helper.parse_request()

        # 1) Check Token
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])
        user = validator.verify(token)
        if not user:
            return http_helper.response(
                code=400,
                message=_("Authentication failed or user is not allowed."),
                success=False
            )

        try:
            with request.env.cr.savepoint():
                req = request.env["employee.other.request"].sudo().search([("id", "=", req_id)], limit=1)
                if not req:
                    return http_helper.response(code=404, message="Request not found", success=False)

                req.unlink()
                return http_helper.response(
                    message=_("Request deleted successfully"),
                    data={"id": req_id}
                )

        except (UserError, AccessError, ValidationError) as e:
            request.env.cr.rollback()
            _logger.error("Error deleting request: %s", str(e))
            return http_helper.response(code=400, message=str(e), success=False)
        except Exception as e:
            request.env.cr.rollback()
            _logger.exception("Unexpected error while deleting request")
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=500, message=message)


# --------------------------------------------
# 4. Related Models (Read-Only)
# 4.1 Salary Destination
# 4.2 Get Qualifications
# 4.3 Get Employee Dependents
# 4.4 Get Certifications
# --------------------------------------------

class EmployeeOtherRequestRelatedModelsController(http.Controller):
    """
    Minimal endpoints for related models used in employee.other.request
    """
    def get_lable_selection(self, rec, field_name, state):
        return dict(rec._fields[field_name]._description_selection(http.request.env)).get(state)
    # 4.1 Salary Destination (salary.destination)
    @http.route(['/rest_api/v2/salary_destination'], type='http', auth='none', csrf=False, methods=['GET'])
    def get_salary_destination_list(self, **kw):
        """
        GET /rest_api/v2/salary_destination
        Return a list of salary.destination records
        """
        http_method, body, headers, token = http_helper.parse_request()
        # If this is publicly available, skip token check or do it similarly
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])

        try:
            destinations = request.env['salary.destination'].sudo().search([])
            data = []
            for dest in destinations:
                data.append({
                    "id": dest.id,
                    "name": dest.name,
                    "english_name": dest.english_name,
                })
            return http_helper.response(message="Salary Destination List", data=data)

        except Exception as e:
            _logger.exception("Error listing salary destinations")
            return http_helper.response(code=400, message=str(e), success=False)

    @http.route(['/api/salary_destination/<int:dest_id>'], type='http', auth='none', csrf=False, methods=['GET'])
    def get_salary_destination_detail(self, dest_id, **kw):
        """
        GET /api/salary_destination/<id>
        Return the detail of a specific salary.destination record
        (Note: endpoint path from your specification)
        """
        # If you want token checks, add them
        dest = request.env['salary.destination'].sudo().search([('id', '=', dest_id)], limit=1)
        if not dest:
            return http_helper.response(code=404, message="Salary destination not found", success=False)
        data = {
            "id": dest.id,
            "name": dest.name,
            "english_name": dest.english_name,
        }
        return http_helper.response(message="Salary Destination Detail", data=data)

    # 4.2 Get Qualifications (Read-Only)
    @http.route(['/rest_api/v2/qualifications'], type='http', auth='none', csrf=False, methods=['GET'])
    def get_qualifications_list(self, **kw):
        """
        GET /rest_api/v2/qualifications
        Retrieve a paginated list of qualifications
        Query Params:
          page, limit, sort, filters
        """
        http_method, body, headers, token = http_helper.parse_request()
        # If needed, check token:
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])

        try:
            page = int(kw.get("page", 1))
            limit = int(kw.get("limit", 10))
            sort = kw.get("sort", "")  # e.g. '-comp_date'
            filters_str = kw.get("filters", "")

            domain = []
            if filters_str:
                for part in filters_str.split(";"):
                    if "=" in part:
                        k, v = part.split("=", 1)
                        domain.append((k.strip(), "=", v.strip()))

            offset = (page - 1) * limit if page > 0 else 0
            order = False
            if sort:
                if sort.startswith("-"):
                    order = sort[1:] + " desc"
                else:
                    order = sort + " asc"

            Qualification = request.env["hr.qualification"].sudo()
            total_count = Qualification.search_count(domain)
            records = Qualification.search(domain, offset=offset, limit=limit, order=order)

            qual_list = []
            for q in records:
                qual_list.append({
                    "id": q.id,
                    "uni_name": q.uni_name.id if q.uni_name else None,  # or q.uni_name.name?
                    "col_name": q.col_name.id if q.col_name else None,
                    "prg_status": q.prg_status or "",
                    "comp_date": q.comp_date or "",
                    "qualification_degree": q.qualification_degree or "",
                    'qualification_degree_lable': self.get_lable_selection(q, 'qualification_degree',
                                                                           q.qualification_degree),
                    "country_name": q.country_name.id if q.country_name else None,
                    "attachment": None,
                })
            qual_list = convert_dates_in_data(qual_list)
            data = {
                "page": page,
                "limit": limit,
                "total_records": total_count,
                "qualifications": qual_list,
            }
            return http_helper.response(message="Qualifications retrieved", data=data)

        except Exception as e:
            _logger.exception("Error listing qualifications")
            return http_helper.response(code=400, message=str(e), success=False)

    # 4.3 Get Employee Dependents (Read-Only)
    @http.route(['/rest_api/v2/employee_dependents'], type='http', auth='none', csrf=False, methods=['GET'])
    def get_employee_dependents_list(self, **kw):
        """
        GET /rest_api/v2/employee_dependents
        Paginated list of dependents
        Query Params:
          page, limit, filters
        """
        http_method, body, headers, token = http_helper.parse_request()
        # If needed, check token:
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])

        try:
            page = int(kw.get("page", 1))
            limit = int(kw.get("limit", 10))
            filters_str = kw.get("filters", "")

            domain = []
            if filters_str:
                for part in filters_str.split(";"):
                    if "=" in part:
                        k, v = part.split("=", 1)
                        domain.append((k.strip(), "=", v.strip()))

            offset = (page - 1) * limit if page > 0 else 0

            DependentModel = request.env["hr.employee.dependent"].sudo()
            total_count = DependentModel.search_count(domain)
            records = DependentModel.search(domain, offset=offset, limit=limit)

            dep_list = []
            for dep in records:
                dep_list.append({
                    'name': dep.name or '',
                    'age': dep.age or '',
                    'birthday': str(dep.birthday or ''),
                    'gender': dep.gender or '',
                    'gender_lable': self.get_lable_selection(dep, 'gender', dep.gender),
                    'relation': dep.relation or '',
                    'relation_lable': self.get_lable_selection(dep, 'relation', dep.relation),
                    'nationality': dep.nationality.read(['id', 'name'])[0] or {},
                    'passport_no': dep.passport_no or '',
                    'passport_issue_date': str(dep.passport_issue_date or ''),
                    'passport_expire_date': str(dep.passport_expire_date or ''),
                    'degree_medical_insu': dep.degree_medical_insu or '',
                    'medical_insurance_num': dep.medical_insurance_num or '',
                    'identity_num': dep.identity_num or '',
                    'has_ticket': dep.has_ticket,
                })

            data = {
                "page": page,
                "limit": limit,
                "total_records": total_count,
                "dependents": dep_list,
            }
            return http_helper.response(message="Dependents retrieved", data=data)

        except Exception as e:
            _logger.exception("Error listing employee dependents")
            return http_helper.response(code=400, message=str(e), success=False)

    # 4.4 Get Certifications (Read-Only)
    @http.route(['/rest_api/v2/certifications'], type='http', auth='none', csrf=False, methods=['GET'])
    def get_certifications_list(self, **kw):
        """
        GET /rest_api/v2/certifications
        Paginated list of certifications
        Query Params:
          page, limit, filters
        """
        http_method, body, headers, token = http_helper.parse_request()
        # If needed, check token:
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])

        try:
            page = int(kw.get("page", 1))
            limit = int(kw.get("limit", 10))
            filters_str = kw.get("filters", "")

            domain = []
            if filters_str:
                for part in filters_str.split(";"):
                    if "=" in part:
                        k, v = part.split("=", 1)
                        domain.append((k.strip(), "=", v.strip()))

            offset = (page - 1) * limit if page > 0 else 0

            CertificationModel = request.env["hr.certification"].sudo()
            total_count = CertificationModel.search_count(domain)
            records = CertificationModel.search(domain, offset=offset, limit=limit)

            cert_list = []
            for c in records:
                cert_list.append({
                    "id": c.id,
                    "car_name": c.car_name or "",  # or maybe c.certification_name in your DB
                    "issue_org": c.issue_org or "",
                    "issue_date": c.issue_date or "",
                    "exp_date": c.exp_date or "",
                    "regis_no": c.regis_no or "",
                    "certification_degree": c.certification_degree or "",
                    "contact_name": c.contact_name or "",
                    "contact_phn": c.contact_phn or "",
                    "contact_email": c.contact_email or "",
                    "country_name": c.country_name.name if c.country_name else "",
                    "attachment": None,
                })
            cert_list = convert_dates_in_data(cert_list)

            data = {
                "page": page,
                "limit": limit,
                "total_records": total_count,
                "certifications": cert_list,
            }
            return http_helper.response(message="Certifications retrieved", data=data)

        except Exception as e:
            _logger.exception("Error listing certifications")
            return http_helper.response(code=400, message=str(e), success=False)
class ReportControllerInherit(ReportController):

    @http.route([
        '/rest_api/v2/public_report/pdf/<reportname>/<docids>',
    ], type="http", auth="none", methods=["GET"])
    def public_report_routes(self, reportname, docids=None, converter="pdf", **data):
        if not converter:
            converter = 'pdf'
        http_method, body, headers, token = http_helper.parse_request()
        # If needed, check token:
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])

        user = validator.verify(token)
        if not user:
            return http_helper.response(code=400, message=_(
                "You are not allowed to perform this operation. please check with one of your team admins"),
                                        success=False)

        env = request.env(user=user.id)

        report = env['ir.actions.report']._get_report_from_name(reportname) or env.ref(reportname)
        context = dict(request.env.context)

        if docids:
            docids = [int(i) for i in docids.split(',')]
        if data.get('options'):
            data.update(json.loads(data.pop('options')))
        if data.get('context'):
            # Ignore 'lang' here, because the context in data is the one from the webclient *but* if
            # the user explicitely wants to change the lang, this mechanism overwrites it.
            data['context'] = json.loads(data['context'])
            if data['context'].get('lang') and not data.get('force_context_lang'):
                del data['context']['lang']
            context.update(data['context'])
        if converter == 'html':
            html = report.with_context(context)._render_qweb_html(docids, data=data)[0]
            return request.make_response(html)
        elif converter == 'pdf':
            pdf = report.with_context(context)._render_qweb_pdf(docids, data=data)[0]
            pdfhttpheaders = [('Content-Type', 'application/pdf'), ('Content-Length', len(pdf))]
            return request.make_response(pdf, headers=pdfhttpheaders)
        elif converter == 'text':
            text = report.with_context(context)._render_qweb_text(docids, data=data)[0]
            texthttpheaders = [('Content-Type', 'text/plain'), ('Content-Length', len(text))]
            return request.make_response(text, headers=texthttpheaders)
        else:
            raise exceptions.HTTPException(description='Converter %s not implemented.' % converter)
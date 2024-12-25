# -*- coding: utf-8 -*-
import werkzeug
from odoo import http, tools
from odoo.http import request, Response
from odoo.exceptions import UserError
import base64
from ...validator import validator
from ...http_helper import http_helper
from odoo.tools.translate import _
import json
import logging
import traceback
_logger = logging.getLogger(__name__)


class EmployeeOtherRequest(http.Controller):

    def get_lable_selection(self, rec, field_name, state):
        return dict(rec._fields[field_name]._description_selection(http.request.env)).get(state)

    @http.route(['/rest_api/v2/employeeRequest/types', '/rest_api/v2/employeeRequest/types/<string:key>'], type='http', auth='none', csrf=False, methods=['GET'])
    def get_employee_other_request_type(self, key=None):
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
            data = {"other_request_types": dict(http.request.env['employee.other.request']._fields['request_type']._description_selection(http.request.env)),
                    "salary_request_print_type": dict(http.request.env['employee.other.request']._fields['print_type']._description_selection(http.request.env)),
                    "salary_request_state": dict(http.request.env['employee.other.request']._fields['state']._description_selection(http.request.env)),
                    "certification_degree": dict(http.request.env['hr.certification']._fields['certification_degree']._description_selection(http.request.env)),
                    "qualification_degree": dict(http.request.env['hr.qualification']._fields['qualification_degree']._description_selection(http.request.env)),
                    "gender": dict(http.request.env['hr.employee.dependent']._fields['gender']._description_selection(http.request.env)),
                    "relation": dict(http.request.env['hr.employee.dependent']._fields['relation']._description_selection(http.request.env)),
                    "nationality": request.env['res.country'].sudo().search([]).read(['id', 'name']),
                    "uni_name_UniversityName": request.env['office.office'].sudo().search([]).read(['id', 'name']),
                    "col_name_College": request.env['hr.college'].sudo().search([]).read(['id', 'name']),
                    "hr_qualification_name": request.env['hr.qualification.name'].sudo().search([]).read(['id', 'name']),
                    "qualification_specification": request.env['qualification.specification'].sudo().search([('type', '=', 'qualification')]).read(['id', 'name']),
                    "certificate_specification": request.env['qualification.specification'].sudo().search([("type", "=", "certificate")]).read(['id', 'name']),
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

    @http.route(['/rest_api/v2/employeeRequests/', '/rest_api/v2/employeeRequests/<int:id>'], type='http', auth='none', csrf=False, methods=['GET'])
    def get_employee_other_requests(self, id=None, approvel=None, page=None, **kw):
        page = page if page else 1
        page, offset, limit, prev = validator.get_page_pagination(page)
        http_method, body, headers, token = http_helper.parse_request()
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])
        user = validator.verify(token)
        if not user:
            return http_helper.response(code=400, message=_("You are not allowed to perform this operation. please check with one of your team admins"), success=False)
        employee = http.request.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
        if not employee:
            return http_helper.response(code=400, message=_("You Have issue in your employee profile. please check with one of your team admins"), success=False)

        try:
            if approvel:
                domain = [('state', '!=', 'draft'),('employee_id', '!=', employee.id)]
                emp_requests = http.request.env['employee.other.request'].search(domain, order='date desc', offset=offset, limit=limit)
                count = http.request.env['employee.other.request'].search_count(domain)
            else:
                emp_requests = http.request.env['employee.other.request'].search([('employee_id', '=', employee.id)], order='date desc', offset=offset, limit = limit)
                count = http.request.env['employee.other.request'].search_count([('employee_id', '=', employee.id)])
            if id:
                emp_requests = http.request.env['employee.other.request'].search([('id', '=', int(id))], order='date desc')
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
                        'state_lable': self.get_lable_selection(s, 'state', s.state),
                    }
                    employee_dependant = []
                    for dep in s.employee_dependant:
                        dep_val = {
                            'name': dep.name or '',
                            'age': dep.age or '',
                            'birthday': str(dep.birthday or ''),
                            'gender':  dep.gender or '',
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
                            'qualification_degree_lable': self.get_lable_selection(qua, 'qualification_degree', qua.qualification_degree),
                            'qualification_specification_id': qua.qualification_specification_id.read(['id', 'name'])[0] or {},
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
                            'certification_degree':  cer.certification_degree or '',
                            'certification_degree_lable': self.get_lable_selection(cer, 'certification_degree', cer.certification_degree),
                            'issue_date': str(cer.issue_date or ''),
                            'exp_date': str(cer.exp_date or ''),
                            'country_id': cer.country_name.read(['id', 'name'])[0] or {},
                        }
                        certification_employee.append(cer_val)
                    if s.certification_employee:
                        value['certification_employee'] = certification_employee

                    employeeRequests.append(value)
            next = validator.get_page_pagination_next(page, count)
            url = "/rest_api/v2/employeeRequests?approvel=%s&page=%s" % ( approvel, next) if next else False
            prev_url = "/rest_api/v2/employeeRequests?approvel=%s&page=%s" % ( approvel, prev) if prev else False
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
            return http_helper.response(code=400, message=_("You are not allowed to perform this operation. please check with one of your team admins"), success=False)
        employee = http.request.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
        if not employee:
            return http_helper.response(code=400, message=_("You Have issue in your employee profile. please check with one of your team admins"), success=False)
        if not reportname:
            return http_helper.response(code=400, message=_("please sent report name . please check with one of your team admins"), success=False)
        report = request.env['ir.actions.report']._get_report_from_name(reportname)
        if docids:
            docids = [int(i) for i in docids.split(',')]
        else:
            return http_helper.response(code=400, message=_("please sent id recrod print report. please check with one of your team admins"), success=False)
        if report:
            model = report.model_id.model or report.model
            if len(request.env[model].search([('id', 'in', docids)])) < len(docids):
                return http_helper.response(code=400, message=_("You Have issue in your  data not found. please check with one of your team admins"), success=False)
        else:
            return http_helper.response(code=400, message=_("You Have issue in your  report not found. please check with one of your team admins"), success=False)
        try:
            context = dict(request.env.context)
            pdf = report.with_context(context)._render_qweb_pdf(docids, data=data)[0]
            pdfhttpheaders = [('Content-Type', 'application/pdf'),('Content-Length', len(pdf))]
            return request.make_response(pdf, headers=pdfhttpheaders)
        except Exception as e:
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)
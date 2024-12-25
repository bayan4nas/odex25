# -*- coding: utf-8 -*-
import werkzeug
from odoo import http,tools
from odoo.http import request, Response
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.exceptions import UserError
import base64
from ..validator import validator
from ..http_helper import http_helper
from odoo.tools.translate import _

import json
import logging
_logger = logging.getLogger(__name__)
import re

class LoanController(http.Controller):
    # loans
    @http.route(['/rest_api/v1/loans'], type='http', auth='none', csrf=False, methods=['GET'])
    def get_loan(self,approvel=None,page=None, **kw):
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
            page = page if page else 1
            page, offset, limit, prev = validator.get_page_pagination(page)
            loan_advantage = http.request.env['loan.request.type'].search([])
            if approvel:
                domain = [('state', '!=', 'draft')]
                if user.has_group('hr.group_hr_manager') or user.has_group('hr_base.group_division_manager') or user.has_group('hr_base.group_general_manager') or\
                    user.has_group('hr_base.group_executive_manager') or user.has_group('hr_loans_salary_advance.group_loan_user') :
                    
                    domain = [('state', '!=', 'draft')]

                if not user.has_group('hr.group_hr_manager') or not user.has_group('hr_base.group_general_manager') or not \
                user.has_group('hr_base.group_executive_manager') or not user.has_group('hr_loans_salary_advance.group_loan_user'):

                    domain = [('state', '!=', 'draft'),'|','|',('department_id.manager_id','=',False),
                                            ('department_id.manager_id.user_id','child_of', [user.id]),
                                            ('department_id.parent_id.manager_id.user_id','child_of', [user.id])]
                loans = http.request.env['hr.loan.salary.advance'].search(domain, order='date desc', offset=offset, limit=limit),
                count = http.request.env['hr.loan.salary.advance'].search_count(domain)
                # else:
                #     loans = False
                #     count = 0
            else:
                loans = http.request.env['hr.loan.salary.advance'].search([('employee_id', '=', employee.id)], order='date desc', offset=offset, limit=limit)
                count = http.request.env['hr.loan.salary.advance'].search_count([('employee_id', '=', employee.id)])
            types = []
            if loan_advantage:
                for x in loan_advantage:
                    value = {'id': x.id, 'name': x.name,'amount':x.amount,
                             }
                    types.append(value)
            li = []
            if loans:
                for l in loans:
                    for s in l:
                        value = {'employee_id':s.employee_id.id,'employee_name':s.employee_id.name,'id': s.id, 'code': s.code, 'expect_amount': s.emp_expect_amount,'date':str(s.date),'state_name':s.state,
                                 'installment_amount':s.installment_amount,'state':validator.get_state_name(s,s.state),'months':s.months,
                                 'request_type_id':s.request_type.id, 'request_type_name':s.request_type.name}
                        lines = []
                        if s.deduction_lines:
                            for l in s.deduction_lines:
                                vals = {
                                    'installment_date':str(l.installment_date),
                                    'installment_amount':l.installment_amount,
                                    'paid':l.paid
                                }
                                lines.append(vals)
                        value['lines'] = lines
                        li.append(value)
            next = validator.get_page_pagination_next(page, count)
            url = "/rest_api/v1/loans?approvel=%s&page=%s" % (approvel, next) if next else False
            prev_url = "/rest_api/v1/loans?approvel=%s&page=%s" % (approvel, prev) if prev else False
            data = {'links': {'prev': prev_url, 'next': url, }, 'count': count, 'results':{'loan_types': types, 'employee_loans': li,'groups':['group_loan_user',
                                              'group_executive_manager','group_hr_manager','group_division_manager','group_general_manager']}}
            return http_helper.response(message="Data Found",
                                        data=data)
        except Exception as e:
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)

        # loans create

    @http.route(['/rest_api/v1/loans'], type='http', auth='none', csrf=False, methods=['POST'])
    def create_loan(self, **kw):
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
        if not body.get('request_type'):
            return http_helper.response(code=400,message=_("Enter request Type"), success=False)
        if not body.get('months'):
            return http_helper.response(code=400,message=_("Enter numbers of month"), success=False)
        if not body.get('expect_amount'):
            return http_helper.response(code=400,message=_("Enter expected Amount"), success=False)
        if not body.get('date'):
            return http_helper.response(code=400,message=_("Enter Date"), success=False)
        if not body.get('request_type'):
            return http_helper.response(code=400,message=_("Enter Request Type"), success=False)
        if not body.get('is_old'):
            return http_helper.response(code=400,message=_("Enter is old"), success=False)
        try:
            loans = http.request.env['hr.loan.salary.advance'].create({
                'employee_id':employee.id,
                'request_type':int(body['request_type']),
                'date':body['date'],
                'emp_expect_amount':body['expect_amount'],
                'finance_propos_amount':body['expect_amount'],
                'gm_propos_amount':body['expect_amount'],
                'is_old':body['is_old'],
                'months':body['months'],
            })
            if loans:
                value = {'id': loans.id, 'code': loans.code, 'expect_amount': loans.emp_expect_amount, 'date': str(loans.date),
                 'state_name':loans.state,  'installment_amount': loans.installment_amount, 'state': validator.get_state_name(loans,loans.state), 'months': loans.months,
                         'request_type_id':loans.request_type.id, 'request_type_name':loans.request_type.name}
                lines = []
                if loans.deduction_lines:
                    for l in loans.deduction_lines:
                        vals = {
                            'installment_date': str(l.installment_date),
                            'installment_amount': l.installment_amount,
                            'paid': l.paid
                        }
                        lines.append(vals)
                value['lines'] = lines
                return http_helper.response(message=_("Record create Successfully"),
                                    data={'employee_loans': [value], })
        except Exception as e:
            http.request._cr.rollback()
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)
 # loans edit

    @http.route(['/rest_api/v1/loans/<string:id>'], type='http', auth='none', csrf=False, methods=['PUT'])
    def edit_loan(self,id, **kw):
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
        if not body.get('request_type'):
            return http_helper.response(code=400, message=_("Enter request Type"), success=False)
        if not body.get('months'):
            return http_helper.response(code=400, message=_("Enter numbers of month"), success=False)
        if not body.get('expect_amount'):
            return http_helper.response(code=400, message=_("Enter expected Amount"), success=False)
        if not body.get('date'):
            return http_helper.response(code=400, message=_("Enter Date"), success=False)
        if not body.get('request_type'):
            return http_helper.response(code=400, message=_("Enter Request Type"), success=False)
        if not body.get('is_old'):
            return http_helper.response(code=400, message=_("Enter is old"), success=False)
        try:
            loans = http.request.env['hr.loan.salary.advance'].search([('id','=',id)])
            if loans:
                loans.write({
                    'employee_id':loans.employee_id.id,
                    'request_type':int(body['request_type']),
                    'date':body['date'],
                    'emp_expect_amount':body['expect_amount'],
                    'is_old':body['is_old'],
                    'months':body['months'],
                })
                # loans.create_loan()
                value = {'id': loans.id, 'code': loans.code, 'expect_amount': loans.emp_expect_amount, 'date': str(loans.date),
                         'installment_amount': loans.installment_amount,  'state_name':loans.state,'state': validator.get_state_name(loans,loans.state), 'months': loans.months,
                         'request_type_id': loans.request_type.id, 'request_type_name': loans.request_type.name}
                lines = []
                if loans.deduction_lines:
                    for l in loans.deduction_lines:
                        vals = {
                            'installment_date': str(l.installment_date),
                            'installment_amount': l.installment_amount,
                            'paid': l.paid
                        }
                        lines.append(vals)
                value['lines'] = lines
                return http_helper.response(message=_("Loan Updated successfully"),
                                    data={'employee_loans': [value], })
        except Exception as e:
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)


    @http.route(['/rest_api/v1/loans/<string:loanId>'], type='http', auth='none', csrf=False, methods=['DELETE'])
    def delete_loan(self, loanId, **kw):
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
            record = http.request.env['hr.loan.salary.advance'].search([('id', '=', loanId)])
            if record and record.state == 'draft':
                record.unlink()
                return http_helper.response(message=_("Deleted successfully"), data={})
            else:
                return http_helper.response(code=400,
                                            message=_("You  can not perform this operation. please check with one of your team admins"),
                                            success=False)
        except Exception as e:
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)

            # Submit loan

    @http.route(['/rest_api/v1/loans/<string:loanId>'], type='http', auth='none', csrf=False,methods=['PATCH'])
    def confirm_loan(self, loanId,approvel=None,refused=None, **kw):
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
            loans = http.request.env['hr.loan.salary.advance'].search([('id', '=', loanId)])
            hr = http.request.env['res.users'].sudo().search(
                [('groups_id', 'in', request.env.ref('hr.group_hr_manager').ids)])
            gm = http.request.env['res.users'].sudo().search(
                [('groups_id', 'in', request.env.ref('hr_base.group_general_manager').ids)])
            dev = http.request.env['res.users'].sudo().search(
                [('groups_id', 'in', request.env.ref('hr_base.group_division_manager').ids)])
            l_user = http.request.env['res.users'].sudo().search(
                [('groups_id', 'in', request.env.ref('hr_loans_salary_advance.group_loan_user').ids)])
            if loans:
                if not refused:
                    if loans.state == 'draft' and not refused:
                        if not loans.deduction_lines:
                            loans.create_loan()
                        loans.submit()
                        msg = _("Loan Submitted Successfully")
                        loans.firebase_notification(l_user)
                    elif loans.state == 'submit' and user.has_group('hr_base.group_division_manager') or  loans.state == 'submit' and user.has_group('hr_loans_salary_advance.group_loan_user'):
                        loans.direct_manager()
                        msg = _("Loan Confirm By direct Manager Successfully")
                        loans.firebase_notification(hr)
                    elif loans.state == 'direct_manager' and user.has_group('hr.group_hr_manager'):
                        loans.hr_manager()
                        msg = _("Loan Approved By Hr  Successfully")
                        loans.firebase_notification(gm)
                    elif loans.state == 'hr_manager' and user.has_group('hr_base.group_general_manager') or \
                            loans.state == 'hr_manager' and user.has_group('hr_base.group_executive_manager'):
                        loans.executive_manager()
                        msg = _("Loan Approved By Executive Manager Successfully ")
                        loans.firebase_notification(hr)
                    elif loans.state == 'executive_manager' and user.has_group('hr.group_hr_manager'):
                        loans.pay()
                        msg = _("Loan Approved By Hr Manager Successfully ")
                        loans.firebase_notification()
                    elif loans.state == 'pay' and user.has_group('hr_loans_salary_advance.group_loan_user'):
                        loans.closed()
                        msg = _("Loan Closed Successfully")
                        loans.firebase_notification(l_user)
                    elif loans.state == 'refused' and user.has_group('hr_loans_salary_advance.group_loan_user') or \
                            loans.state == 'refused' and user.has_group('hr.group_hr_manager'):
                        loans.draft_state()
                        msg = _("Loan Reset to Draft Successfully ")
                        loans.firebase_notification()
                    elif loans.state == 'closed' and user.has_group('hr_loans_salary_advance.group_loan_user') or \
                            loans.state == 'closed' and user.has_group('hr.group_hr_manager'):
                        loans.to_re_paid()
                        msg = _("Loan State change to Re Pay ")
                        loans.firebase_notification()
                elif refused:
                    if loans.state not in ['draft', 'refused', 'closed']:
                        if user.has_group('hr.group_hr_manager') or \
                            user.has_group('hr_base.group_general_manager') or user.has_group('hr_base.group_executive_manager') or \
                            user.has_group('hr_loans_salary_advance.group_loan_user'):
                            loans.refused()
                            msg = _("Loan request  Refused ")
                            loans.firebase_notification()
                    else:
                        msg = _("You con not refuse this Loan")
                        return http_helper.response(code=400, message=msg, data={'loans': []})
                else:
                    msg = _("You do not have access contact system admin")
                    return http_helper.response(code=400,message=msg, data={'loans': []})
                data = {'id': loans.id, 'code': loans.code, 'expect_amount': loans.emp_expect_amount, 'date': str(loans.date),
                         'installment_amount': loans.installment_amount, 'state_name':loans.state, 'state': validator.get_state_name(loans,loans.state), 'months': loans.months,
                         'request_type_id': loans.request_type.id, 'request_type_name': loans.request_type.name}
                lines = []
                if loans.deduction_lines:
                    for l in loans.deduction_lines:
                        vals = {
                            'installment_date': str(l.installment_date),
                            'installment_amount': l.installment_amount,
                            'paid': l.paid
                        }
                        lines.append(vals)
                data['lines'] = lines
                return http_helper.response(message=msg, data={'loans': [data]})
            else:
                return http_helper.response(code=400,
                                            message=_("You  can not perform this operation. please check with one of your team admins"),
                                            success=False)
        except Exception as e:
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)



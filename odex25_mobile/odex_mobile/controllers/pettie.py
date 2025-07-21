# -*- coding: utf-8 -*-
import werkzeug
from odoo import http,tools
from datetime import datetime
from odoo.http import request, Response
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.exceptions import UserError
import base64
from ..validator import validator
from ..http_helper import http_helper
import json
import logging
import calendar
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
_logger = logging.getLogger(__name__)
import re

class PettiesController(http.Controller):
    # Document
    @http.route(['/rest_api/v1/documents'], type='http', auth='none', csrf=False, methods=['GET'])
    def get_document(self, **kw):
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
            documents = http.request.env['hr.employee.document'].search([('employee_ref', '=', employee.id)])
            if documents:
                li = []
                for pro in documents:
                    value = {'id': pro.id, 'name': pro.name, 'issue_date': pro.issue_date, 'expiry_date': pro.expiry_date,
                             'document_type':pro.document_type,'doc_number':self.get_document_number(pro)}
                    li.append(value)
                return http_helper.response(message="Data Found", data={'documents': li})
            else:
                return http_helper.errcode(code=403, message="No Document for this employee")
        except Exception as e:
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)

    def get_document_number(self,rec):
        if rec.document_type == 'iqama':
            return rec.iqama_id
        elif rec.document_type == 'passport':
            return rec.passport_id
        elif rec.document_type == 'license':
            return rec.license_id
        elif rec.document_type == 'saudi':
            return rec.saudi_id
        elif rec.document_type == 'medical_examination':
            return rec.file_examination
        else:
            return False
    # Petty
    @http.route(['/rest_api/v1/petties'], type='http', auth='none', csrf=False, methods=['GET'])
    def get_petties(self, **kw):
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
            petty = http.request.env['petty.cash.payment'].search([('employee_id','=',employee.id)])
            journal = http.request.env['petty.cash.payment.journal'].search([])
            types = []
            if journal:
                for pro in journal:
                    value = {'id': pro.id, 'name': pro.name}
                    types.append(value)
            li = []
            if petty:
                for pro in petty:
                    value = {'id': pro.id, 'name': pro.name,'date':pro.date,'amount':pro.amount,'state':validator.get_state_name(pro,pro.state),
                             'reconciliation_amount':pro.reconciliation_amount,'type':pro.type.name,'type_id':pro.type.id }
                    li.append(value)
            return http_helper.response(message="Data Found", data={'petties': li,'types':types})
        except Exception as e:
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)
        # else:
        #     return http_helper.errcode(code=403, message="No Petty for this employee")

#         petty create

    @http.route(['/rest_api/v1/petties'], type='http', auth='none', csrf=False, methods=['POST'])
    def create_petties(self, **kw):
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
        employee = http.request.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
        if not body['amount']:
            return http_helper.response(code=400,message="Please enter Amount",success=False)
        if not body['date']:
            return http_helper.response(code=400,message="Please enter Date",success=False)
        if not body['name']:
            return http_helper.response(code=400,message="Please enter Name",success=False)
        if not body['type']:
            return http_helper.response(code=400,message="Please enter Type",success=False)
        try:
            petty = http.request.env['petty.cash.payment'].create({
                'employee_id':employee.id,
                'amount':body['amount'],
                'date':body['date'],
                'name':body['name'],
                'type':body['type'],
            })
            if petty:
                li = []
                value = {'id': petty.id, 'name': petty.name,'date':petty.date,'amount':petty.amount,'state':validator.get_state_name(petty,petty.state),
                         'reconciliation_amount':petty.reconciliation_amount,'type':petty.type.name,'type_id':petty.type.id }
                li.append(value)
                return http_helper.response(message="Petty Created Successfully", data={'petties': li})
        except Exception as e:
            http.request._cr.rollback()
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)

#         petty edit

    @http.route(['/rest_api/v1/petties/<string:id>'], type='http', auth='none', csrf=False, methods=['PUT'])
    def edit_petties(self,id, **kw):
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
        employee = http.request.env['hr.employee'].search([('user_id', '=', user.id)], limit=1)
        if not body['amount']:
            return http_helper.response(code=400,message="Please enter Amount",success=False)
        if not body['date']:
            return http_helper.response(code=400,message="Please enter Date",success=False)
        if not body['name']:
            return http_helper.response(code=400,message="Please enter Name",success=False)
        if not body['type']:
            return http_helper.response(code=400,message="Please enter Type",success=False)
        try:
            petty = http.request.env['petty.cash.payment'].search([('id','=',id)])
            if petty:
                petty.write({
                    'employee_id':employee.id,
                    'amount':body['amount'],
                    'date':body['date'],
                    'name':body['name'],
                    'type':body['type'],
                })
                li = []
                value = {'id': petty.id, 'name': petty.name,'date':petty.date,'amount':petty.amount,'state':validator.get_state_name(petty,petty.state),
                         'reconciliation_amount':petty.reconciliation_amount,'type':petty.type.name,'type_id':petty.type.id }
                li.append(value)
                return http_helper.response(message="Petty Updated Successfully", data={'petties': li})
        except Exception as e:
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)

    @http.route(['/rest_api/v1/petties/<string:pettyId>'], type='http', auth='none', csrf=False,methods=['DELETE'])
    def delete_petties(self, pettyId, **kw):
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
            record = http.request.env['petty.cash.payment'].search([('id', '=', pettyId)])
            if record and record.state == 'draft':
                record.unlink()
                return http_helper.response(message="Deleted successfully", data={})
            else:
                return http_helper.response(code=400,
                                            message="You  can not perform this operation. please check with one of your team admins",
                                            success=False)
        except Exception as e:
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)

            # Submit petty

    @http.route(['/rest_api/v1/petties/<string:pettyId>'], type='http', auth='none', csrf=False,methods=['PATCH'])
    def confirm_petty(self, pettyId, **kw):
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
            petty = http.request.env['petty.cash.payment'].search([('id','=',pettyId)])
            if petty and petty.state == 'draft':
                petty.button_submit()
                li = []
                value = {'id': petty.id, 'name': petty.name, 'date': petty.date, 'amount': petty.amount,
                         'state': validator.get_state_name(petty, petty.state),
                         'reconciliation_amount': petty.reconciliation_amount, 'type': petty.type.name,
                         'type_id': petty.type.id}
                li.append(value)
                return http_helper.response(message="Petty Confirm Successfully", data={'petties': li})
            else:
                return http_helper.response(code=400,
                                            message="You  can not perform this operation. please check with one of your team admins",
                                            success=False)
        except Exception as e:
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)




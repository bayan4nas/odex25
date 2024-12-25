# -*- coding: utf-8 -*-
from .main import *

import logging

from odoo import http
from odoo.http import request

from odoo import _

_logger = logging.getLogger(__name__)


class UserApi(http.Controller):

    @http.route('/api/user/verify_otp', methods=["POST"], type='http', auth='none',  csrf=False)
    def verify_otp_post_api(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        mobile = kw.get('mobile', False)
        otp = kw.get('otp', '')

        # Checking and validation
        if all([mobile, otp]):
            if re.match(SAUDI_MOBILE_PATTERN, str(mobile)) == None:
                error_descrip = _('Enter a valid Saudi mobile number')
                error = 'invalid_mobile'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

            # OTP verify processing..
            user_id = request.env['res.users'].sudo().search([('mobile', '=', mobile)], limit=1)
            if not user_id:
                error_descrip = _('User account does not exist')
                error = 'does_not_exist'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

            result = user_id.sudo().verify_otp(otp)
            if result['code'] == 200:
                return successful_response(
                    status=OUT_SUCCESS_CODE,
                    dict_data=result['results']
                )
            else:
                code = result['code']
                error_descrip = result['error_descrip']
                error = result['error']
                _logger.error(error_descrip)
                return error_response(code, error, error_descrip)

        else:
            error_descrip = _('Some or all data is missing')
            error = 'missing_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

    @http.route('/api/user/request_otp', methods=["POST"], type='http', auth='none',  csrf=False)
    def request_otp_post_api(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        mobile_or_email = kw.get('auth_key', False)

        if not mobile_or_email:
            error_descrip = _('Some or all data is missing')
            error = 'missing_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        user_id = request.env['res.users'].sudo().search(
            ['|', ('login', '=', mobile_or_email), ('mobile', '=', mobile_or_email)], limit=1)
        if not user_id:
            error_descrip = _('User account does not exist')
            error = 'does_not_exist'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        mobile = user_id.mobile or False

        if mobile:
            result = user_id.sudo().request_otp(mobile)
            if result['code'] == 200:
                return successful_response(
                    status=OUT_SUCCESS_CODE,
                    dict_data=result['results']
                )
            else:
                code = result['code']
                error_descrip = result['error_descrip']
                error = result['error']
                _logger.error(error_descrip)
                return error_response(code, error, error_descrip)

        else:
            error_descrip = _('This account has not a mobile number')
            error = 'does_not_exist'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

    @http.route('/api/user/reset_password', methods=["POST"], type='http', auth='none', 
                csrf=False)
    def reset_password_user_post_api(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        password1 = kw.get('password1', False)
        password2 = kw.get('password2', False)
        otp = kw.get('otp', False)
        mobile_or_email = kw.get('auth_key', False)

        if all([mobile_or_email, password1, password2, otp]):

            if password1 != password2:
                error_descrip = _('The entered password does not match')
                error = 'password_not_match'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

            user_id = request.env['res.users'].sudo().search(
                ['|', ('login', '=', mobile_or_email), ('mobile', '=', mobile_or_email)], limit=1)
            if not user_id:
                error_descrip = _('User account does not exist')
                error = 'does_not_exist'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

            # Reset..
            result = user_id.sudo().reset_password_using_otp(password1, password2, otp)
            if result['code'] == 200:
                return successful_response(
                    status=OUT_SUCCESS_CODE,
                    dict_data=result['results']
                )
            else:
                code = result['code']
                error_descrip = result['error_descrip']
                error = result['error']
                _logger.error(error_descrip)
                return error_response(code, error, error_descrip)

        else:
            error_descrip = _('Some or all data is missing')
            error = 'missing_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

    @http.route('/api/user/email_verification', methods=["POST"], type='http', auth='none', 
                csrf=False)
    def email_verification_user_post_api(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        mobile_or_email = kw.get('auth_key', False)

        if not mobile_or_email:
            error_descrip = _('Some or all data is missing')
            error = 'missing_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        user_id = request.env['res.users'].sudo().search(
            ['|', ('login', '=', mobile_or_email), ('mobile', '=', mobile_or_email)], limit=1)
        if user_id:
            # Email verification processing..
            result = user_id.sudo().reset_password_using_email()
            if result['code'] == 200:
                return successful_response(
                    status=OUT_SUCCESS_CODE,
                    dict_data=result['results']
                )
            else:
                code = result['code']
                error_descrip = result['error_descrip']
                error = result['error']
                _logger.error(error_descrip)
                return error_response(code, error, error_descrip)
        else:
            error_descrip = _('User account does not exist')
            error = 'does_not_exist'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

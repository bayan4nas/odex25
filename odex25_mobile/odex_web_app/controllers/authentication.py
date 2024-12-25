# -*- coding: utf-8 -*-
import werkzeug
from odoo import http, tools
from odoo.http import request, Response
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.addons.web.controllers.main import ensure_db
from odoo.exceptions import UserError
import base64
from ..validator import validator
from ..http_helper import http_helper
import json
import logging
from odoo.tools.translate import _

_logger = logging.getLogger(__name__)

SENSITIVE_FIELDS = ['password', 'password_crypt', 'new_password', 'create_uid', 'write_uid']


class AuthenticationController(http.Controller):

    @http.route('/rest_api/web/login', type='http', auth='none', csrf=False, cors='*', methods=['POST'])
    def login_phone(self, **kw):
        if not kw:
            kw = json.loads(http.request.httprequest.data)
        db = kw.get('db')
        login = kw.get('login')
        password = kw.get('password')

        # Check for required fields
        if not login:
            return http_helper.response(code=400, message=_('Username or email is missing'), success=False)
        if not password:
            return http_helper.response(code=400, message=_('Password is missing'), success=False)
        if not kw.get('device_id'):
            return http_helper.response(code=400, message=_('Device id is missing'), success=False)
        if not kw.get('fcm_token_web'):
            return http_helper.response(code=400, message=_('FCM Token is missing'), success=False)

        # Set the database for the request environment
        if db:
            ensure_db()

        # Authenticate user
        uid = http_helper.is_authentic(login, password)
        if not uid:
            return http_helper.errcode(code=400, message=_('Unable to Sign In. invalid user password'))

        # Generate token and prepare response
        user = request.env['res.users'].browse(uid)
        token = validator.create_token(user)
        dic = user.sudo().to_dict(True)
        employee = request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)

        # Update device_id and fcm_token_web if present
        if employee:
            if kw.get('device_id') and not employee.device_id:
                employee.sudo().write({'device_id': kw.get('device_id')})
            if kw.get('fcm_token_web'):
                employee.sudo().write({'fcm_token_web': kw.get('fcm_token_web')})

        dic['token'] = token
        http_helper.cleanup()
        return http_helper.response(data=dic, message=_("User logged in successfully"))
    

    @http.route('/rest_api/web/validate',type='http', auth='none', csrf=False, cors='*',methods=['POST'])
    def validate_token(self, **kw):
        http_method, body, headers, token = http_helper.parse_request()

        result = validator.validate_token(token)
        if result['code'] == 497 or result['code'] == 498:
            return http_helper.errcode(code=result['code'], message=result['message'])

        return http_helper.response(message="uploaded success",data=result['data'])

    @http.route('/rest_api/web/refresh',type='http', auth='none', csrf=False, cors='*',methods=['POST'])
    def refresh_token(self, **kw):
        http_method, body, headers, token = http_helper.parse_request()

        result = validator.refresh_token(token)
        if result['code'] == 497:
            return http_helper.errcode(code=result['code'], message=result['message'])

        return http_helper.response(message="uploaded success",data=result['data'])

    # Reet password with email
    @http.route(['/rest_api/web/reset'], type='http', auth='none', csrf=False, methods=['POST'])
    def reset_email(self, **kw):
        http_method, body, headers, token = http_helper.parse_request()
        if not body.get('email'):
            return http_helper.response(code=400, message="Email must not be empty", success=False)
        user = http.request.env['res.users'].sudo().search([('login', '=', kw.get('email'))])
        if user:
            user.sudo().action_reset_password()
            return http_helper.response(message=_("A verification link has been sent to you email account"), data={})
        else:
            return http_helper.errcode(code=403, message="Password reset failed")
    
    @http.route('/rest_api/web/users/password',type='http', auth='none', csrf=False, cors='*',methods=['PUT'])
    def change_password(self, **kw):
        http_method, body, headers, token = http_helper.parse_request()
        if not body.get('old_password') or not  body.get('new_password'):
            return http_helper.errcode(code=400, message='Password must not be empty')
        
        result = validator.verify_token(token)
        
        if not result['status']:
            return http_helper.errcode(code=400, message='Invalid passwords')
        
        user = validator.verify(token)
        if not user:
            return http_helper.errcode(code=400, message=_("You are not allowed to perform this operation. please check with one of your team admins"))

        if not http_helper.is_authentic(user.login, body.get('old_password')):
            return http_helper.errcode(code=400, message='Invalid passwords')
        
        request.env.user.write({
            'password':str(body.get('new_password')).strip()
        })
        request.session.logout()
        

        return http_helper.response(message=_("password changed successfully"),data={'id':user.id})
    
    @http.route('/rest_api/web/logout', type='http', auth='none', csrf=False, cors='*', methods=['POST'])
    def logout(self, **kw):
        http_method, body, headers, token = http_helper.parse_request()
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])

        http_helper.do_logout(token)
        return http_helper.response()
    
    @http.route('/rest_api/web/users', type='http', auth='none', csrf=False, cors='*', methods=['GET'])
    def info(self, **kw):
        http_method, body, headers, token = http_helper.parse_request()
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])
        user = validator.verify(token)
        if not user:
            return http_helper.response(code=400, message=_("You are not allowed to perform this operation. please check with one of your team admins"), success=False)
              
        return http_helper.response(data=user.to_dict(True))

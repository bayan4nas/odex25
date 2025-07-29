# -*- coding: utf-8 -*-
import werkzeug
from odoo import http,tools
from odoo.http import request, Response
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.addons.web.controllers.main import ensure_db
from odoo.exceptions import UserError ,AccessError, ValidationError
import base64
# from odoo.addons.odex_mobile.validator import validator
# from odoo.addons.odex_mobile.http_helper import http_helper
# from odoo.addons.odex_mobile.data_util import data_util
from ...validator import validator
from ...http_helper import http_helper
from ...data_util import data_util
import json
import logging
import time
from odoo.tools.translate import _
_logger = logging.getLogger(__name__)



SENSITIVE_FIELDS = ['password', 'password_crypt', 'new_password', 'create_uid', 'write_uid']

class AuthenticationController(http.Controller):

    @http.route('/rest_api/validate',type='http', auth='none', csrf=False, cors='*',methods=['POST'])
    def validate_token(self, **kw):
        start_time_pc = time.perf_counter()
        http_method, body, headers, token = http_helper.parse_request()

        result = validator.validate_token(token)
        _logger.info("DEBUG VALIDATION: %s", result)
        if result['code'] == 497 or result['code'] == 498:
            return http_helper.errcode(code=result['code'], message=result['message'])

        end_time_pc = time.perf_counter()
        execution_time_pc = end_time_pc - start_time_pc
        _logger.info("TIME VALIDATION API: %s seconds, user id: %s, user name: %s", execution_time_pc, request.env.user.id, request.env.user.name)
        return http_helper.response(message="uploaded success",data=result['data'])

    @http.route('/rest_api/refresh',type='http', auth='none', csrf=False, cors='*',methods=['POST'])
    def refresh_token(self, **kw):
        http_method, body, headers, token = http_helper.parse_request()

        result = validator.refresh_token(token)
        if result['code'] == 497:
            return http_helper.errcode(code=result['code'], message=result['message'])

        return http_helper.response(message="uploaded success",data=result['data'])

    @http.route('/rest_api/users/avatar',type='http', auth='none', csrf=False, cors='*',methods=['POST'])
    def update_avatar(self, **kw):
        http_method, body, headers, token = http_helper.parse_request()
        if not body.get('image'):
            return http_helper.response(code=400,message=_("Image must not be empty"),success=False)

        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])
        
        user = validator.verify(token)
        if not user:
            return http_helper.response(code=400,message=_("You are not allowed to perform this operation. please check with one of your team admins"),success=False)
        
        try:
            binary = base64.encodestring(body.get("image").read())
            content = tools.image_resize_image(base64_source=binary, size=(200,200), encoding='base64')
            if not content:
                return http_helper.response(message=_("uploaded failed"), success=False)

            user.write({
                "image":content
            })
        except Exception as e:
            _logger.error(str(e))
            return http_helper.response_500()

        return http_helper.response(message="uploaded success",data={"uid":user.id})

    @http.route('/rest_api/users/password',type='http', auth='none', csrf=False, cors='*',methods=['PUT'])
    def change_password(self, **kw):
        try:
            http_method, body, headers, token = http_helper.parse_request()
            if not body.get('old_password') or not  body.get('new_password'):
                return http_helper.errcode(code=400, message='Password must not be empty')
            
            result = validator.verify_token(token)
            if not result['status']:
                return http_helper.errcode(code=400, message='Invalid Token')
            user = validator.verify(token)
            if not user:
                return http_helper.errcode(code=400, message=_("You are not allowed to perform this operation. please check with one of your team admins"))

            if not http_helper.is_authentic(user.login, body.get('old_password')):
                return http_helper.errcode(code=400, message='Invalid passwords')
            
            res = request.env.user.sudo().write({
                'password':str(body.get('new_password')).strip()
            })
            # # change_password(self, old_passwd, new_passwd)

            # # res = user.sudo().change_password(str(body.get('old_password')).strip(),str(body.get('new_password')).strip())
            request.session.logout()
            http_helper.do_logout(token)
            return http_helper.response(message=_("password changed successfully"),data={'id':user.id})
        except (UserError, AccessError, ValidationError, Exception, Warning) as e:
            http.request._cr.rollback()
            error = str(e)
            return http_helper.response(code=400, message=str(error), success=False)
        except Exception as e:
            http.request._cr.rollback()
            _logger.error(str(e))
            message = validator.get_server_error(e, user)
            return http_helper.errcode(code=403, message=message)

    # Reet password with email
    @http.route(['/rest_api/reset'], type='http', auth='none', csrf=False, methods=['POST'])
    def reset_email(self, **kw):
        http_method, body, headers, token = http_helper.parse_request()
        email =kw.get('email')
        if not email:
            return http_helper.response(code=400, message="Email must not be empty", success=False)

        try:
            users = http.request.env['res.users'].sudo().search([('login', '=', email)])
            if users:
                if len(users) > 1:
                    return http_helper.response(code=409, message="Multiple accounts found for this email",
                                                success=False)
                users.sudo().with_context(company_id=users.company_id.id).action_reset_password()
                return http_helper.response(message="A verification link has been sent to your email account", data={})

            employee = http.request.env['hr.employee'].sudo().search([('work_email', '=', email)], limit=1)
            if employee:
                if not employee.user_id:
                    return http_helper.response(code=404, message="This employee is not linked to any user",
                                                success=False)
                employee.user_id.sudo().with_context(company_id=employee.company_id.id).action_reset_password()
                return http_helper.response(message="A verification link has been sent to your email account", data={})

            return http_helper.response(code=403, message="Password reset failed", success=False)

        except Exception as e:
            return http_helper.response(code=500, message=str(e), success=False)

    # def reset_email(self, **kw):
    #     http_method, body, headers, token = http_helper.parse_request()
    #     if not body.get('email'):
    #         return http_helper.response(code=400, message="Email must not be empty", success=False)
    #     user = http.request.env['res.users'].sudo().search([('login', '=', kw.get('email'))])
    #     if user:
    #         if user:
    #             try:
    #                 user.sudo().with_context(company_id=user.company_id.id).action_reset_password()
    #             except Exception as e:
    #                 return http_helper.response(message=_(e.__str__()),
    #                                             data={})
    #             return http_helper.response(message=_("A verification link has been sent to you email account"),
    #                                         data={})
    #     else:
    #         return http_helper.errcode(code=403, message="Password reset failed")

    @http.route('/rest_api/get_language',type='http', auth='none', csrf=False ,methods=['GET'])
    def get_language(self, **kw):
        lang = http.request.env['res.lang'].sudo().search_read([('active', '=', True)],['name','code'],)
        return http_helper.response(message=_("Languages"), data=lang ,success=False)
        
        
    @http.route('/rest_api/change_language',type='http', auth='none', csrf=False, cors='*',methods=['PUT'])
    def change_language(self, **kw):
        http_method, body, headers, token = http_helper.parse_request()
        result = validator.verify_token(token)

        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])
        
        user = validator.verify(token)
        if not user:
            return http_helper.response(code=400, message=_("You are not allowed to perform this operation. please check with one of your team admins"), success=False)
        if not body.get("lang"):
            return http_helper.response(message=_("Language must not be empty"),success=False)
    
        # if not body.get("phone"):
        #     return http_helper.response(message="Phone must not be empty",success=False)
        try:
            user.write({
                'lang':body.get('lang'),
                # 'phone':body.get('phone'),
            })
        except Exception as e:
            _logger.error(str(e))
            return http_helper.response_500()
        return http_helper.response(message=_("Update success"),data={"uid":user.id})
    
    @http.route('/rest_api/users', type='http', auth='none', csrf=False, cors='*', methods=['GET'])
    def info(self, **kw):
        http_method, body, headers, token = http_helper.parse_request()
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])
        user = validator.verify(token)
        if not user:
            return http_helper.response(code=400, message=_("You are not allowed to perform this operation. please check with one of your team admins"), success=False)
              
        return http_helper.response(data=user.to_dict(True))

    @http.route('/rest_api/logout', type='http', auth='none', csrf=False, cors='*', methods=['POST'])
    def logout(self, **kw):
        http_method, body, headers, token = http_helper.parse_request()
        result = validator.verify_token(token)
        if not result['status']:
            return http_helper.errcode(code=result['code'], message=result['message'])

        http_helper.do_logout(token)
        return http_helper.response()

    @http.route('/rest_api/login', type='http', auth='none', csrf=False, cors='*', methods=['POST'])
    def login_phone(self, **kw):
        if not kw:
            kw = json.loads(http.request.httprequest.data)
        db = kw.get('db')
        start_time_pc = time.perf_counter()
        login=kw.get('login')
        password=kw.get('password')
        if not login :
            return http_helper.response(code=400,message=_('username or email is missing'),success=False)

        if not password:
            return http_helper.response(code=400,message=_('Password is missing'),success=False)
        if not kw.get('device_id'):
            return http_helper.response(code=400,message=_('Device id is missing'),success=False)

        #check fcm_token
        if not kw.get('fcm_token'):
            return http_helper.response(code=400,message=_('FCM Token is missing'),success=False)
            # Set the database for the request environment
        if db:
            ensure_db()

        user = request.env['res.users'].sudo().search([('login', '=',login)], limit=1)
   
        if not user or not user.login:
            return http_helper.response(code=400,message=_('User account with login {} not found').format(login),success=False)
            
        uid = http_helper.is_authentic(login,password)
        if not uid:
            return http_helper.errcode(code=400, message=_('Unable to Sign In. invalid user password'))
        token = validator.create_token(request.env.user)
        dic = request.env.user.to_dict(True)
        employee = http.request.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
        if employee and kw.get('device_id') and not employee.device_id:
            employee.sudo().write({'device_id':kw.get('device_id')})

        #write fcm_token in employee
        if employee and kw.get('fcm_token'):
            employee.sudo().write({'fcm_token':kw.get('fcm_token')})

        dic['token'] = token
        dic['is_approve'] = 'group_division_manager' in dic.get('groups',[]) or 'group_hr_user' in dic.get('groups', [])
        dic['is_done'] = 'group_division_manager' in dic.get('groups',[]) or 'group_hr_user' in dic.get('groups', [])
        dic['has_two_periods'] = not employee.resource_calendar_id.is_full_day if employee.resource_calendar_id else False
        http_helper.cleanup()
        end_time_pc = time.perf_counter()
        execution_time_pc = end_time_pc - start_time_pc
        _logger.info("TIME LOGIN API: %s seconds, user id: %s, user name: %s", execution_time_pc, user.id, user.name)
        return http_helper.response(data=dic, message=_("User log in successfully"))

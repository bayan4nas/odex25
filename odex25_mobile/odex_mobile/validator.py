import logging
import jwt
import re
import pytz
import datetime
import traceback
from odoo import http, service, registry, SUPERUSER_ID,_
from odoo.http import request
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import phonenumbers
import math
from math import ceil
from odoo.service import security

import logging
_logger = logging.getLogger(__name__)

SECRET_KEY = "skjdfe48ueq739rihesdio*($U*WIO$u8"

regex = r"^[a-z0-9!#$%&'*+\/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+\/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?$"


class Validator:
    def get_page_pagination(self,page):
        limit = 20
        page = int(page)
        page = 1 if page<1 else page
        offset = (page - 1) * limit
        prev = False if page -1<=0 else page -1
        return page,offset,limit,prev

    def get_page_pagination_next(self,page,count):
        page = int(page)
        page = page+1
        next = math.ceil(count / 20)
        if next <page:
            return False
        else:
            return page

    def get_attendance_check(self,employee):
        if not employee:
            return 'sign_out'
        user = employee.user_id
        timezone = user.tz or 'GMT'
        local_tz = pytz.timezone(timezone)
        now_gmt = datetime.datetime.now(local_tz)
        current_time_float = now_gmt.hour + now_gmt.minute / 60.0

        calendar = employee.resource_calendar_id
        before_work = getattr(calendar, 'grace_hour_before_work', 8.0)
        after_work = getattr(calendar, 'grace_hour_after_work', 16.0)

        if before_work and after_work:
            if current_time_float < before_work or current_time_float > after_work:
                return 'sign_out'

        last = http.request.env['attendance.attendance'].sudo().search([('employee_id', '=', employee.id), ], order='name desc',
                                                       limit=1)
        if last:
            return last.action
        else:
            return 'sign_out'


    def get_state_name(self,obj,state):
        state_name = dict(obj.fields_get(["state"],['selection'])['state']["selection"]).get(obj.state)
        return state_name

    def is_valid_name(self, name):
        return len (name) > 6
    
    def is_valid_password(self, password):
        return len (password) > 5
    
    def is_valid_location(self, location):
        try:
            lat , lat = [float(x) for x in location.split(',') if x.replace('.','',1).isdigit()]
            if lat and lat:
                return True
        except :
            pass
        return False
    
    def is_valid_email(self, email):
        return re.search(regex, email)

    def is_valid_phone(self,phone):
        try:
            if not phone.startswith('+'):
                phone = '+'+phone
            number = phonenumbers.parse(phone, None)
            isvalid =  phonenumbers.is_valid_number(number)
            return isvalid
        except :
            pass
        return False

    def get_server_error(self,e,user):
        x= False
        if len(e.args) == 2:
            x, y = e.args
            x = re.sub('\n', '', x)
        else:
            x = e.args
        text = ""
        if user.lang ==  'en_US':
            text =(_("contact admin or edit it Manually"))
        else:
            text = "الرجاء التواصل مع مدير النظام او استخدام الموقع الالكترونى"
        message = "%s, %s" % (x,text)
        return message
    
    
    def create_token(self, user):
        try:
            now = datetime.datetime.now(datetime.timezone.utc)
            exp = now + datetime.timedelta(days=user.company_id.jwt_expire_days or 14)
            payload = {
                'exp': exp,
                'iat': now,
                'sub': user['id'],
                'lgn': user['login'],
            }
            token = jwt.encode(
                payload,
                SECRET_KEY,
                algorithm='HS256'
            )
            # payload = jwt.decode(token, SECRET_KEY ,algorithms='HS256')
            self.save_token(token, user['id'], exp)

            return token
        except Exception as ex:
            _logger.error(ex)
            raise

    def save_token(self, token, uid, exp):
        request.env['jwt_provider.access_token'].sudo().create({
            'user_id': uid,
            'expires': exp.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            'token': token,
        })

    def verify(self, token):
        record = request.env['jwt_provider.access_token'].sudo().search([
            ('token', '=', token)
        ])

        if len(record) != 1:
            _logger.info('not found %s' % token)
            return False

        if record.is_expired:
            return False
        
        record.set_env(request.env)        
        return record.user_id

    def verify_token(self, token):
        try:
            result = {
                'status': False,
                'message': None,
            }

            record = request.env['jwt_provider.access_token'].sudo().search([
                ('token', '=', token)
            ])
            
            if len(record) != 1:
                result['message'] = 'Token not found'
                result['code'] = 497
                return result

            if record.is_expired:
                result['message'] = 'Token has expired'
                result['code'] = 498
                return result

            payload = jwt.decode(token, SECRET_KEY ,algorithms='HS256')

            uid =self.verify(token)
            user =  uid
            request.session.uid = user.id
            request.session.login = user.login
            request.session.session_token = user.id and security.compute_session_token(
                request.session, request.env
            )
            request.uid = user.id
            request.disable_db = False
            request.session.get_context()
            
            # Set user's context
            user_context = request.env(request.cr, request.session.uid)['res.users'].context_get().copy()
            request.session.context = request.context = user_context
            request.env.user = uid
            # uid = request.session.authenticate(request.session.db, uid=payload['sub'], password=token)
            if not uid:
                result['message'] = 'Token invalid or expired'
                result['code'] = 498
                return result

            result['status'] = True
            return result
        except jwt.ExpiredSignatureError as ex :
            result['code'] = 498
            result['message'] = 'Signature has expired'
            _logger.error(traceback.format_exc())

        except (jwt.InvalidTokenError, Exception) as e:
            record = request.env['jwt_provider.access_token'].sudo().search([
                ('token', '=', token)
            ])
            if not record:
                result['message'] = 'Token not found'
                result['code'] = 497
                return result
            else:
                result['code'] = 498
                result['message'] = 'Token invalid'
                _logger.error(traceback.format_exc())
            return result

    def refresh_token(self, token):
        try:
            result = {
                'status': False,
                'message': None,
                'code':200
            }
            record = request.env['jwt_provider.access_token'].sudo().search([
                ('token', '=', token)
            ])

            if len(record) != 1 or not record:
                result['message'] = 'Token not found'
                result['code'] = 497
                return result

            payload = jwt.decode(token, SECRET_KEY ,algorithms='HS256')
            user = request.env['res.users'].sudo().search([('id', '=',payload['sub'])], limit=1)
            if not user:
                result['message'] = 'Token for user not found'
                result['code'] = 497
                return result

            request.env['jwt_provider.access_token'].sudo().search([
                ('token', '=', token)
            ]).unlink()
            result['status'] = True
            result['code'] == 200
            result['data'] = {'token':self.create_token(user)}
            return result
        except jwt.ExpiredSignatureError as ex :
            request.env['jwt_provider.access_token'].sudo().search([
                ('token', '=', token)
            ]).unlink()
            result['status'] = True
            result['code'] == 200
            result['data'] = {'token':self.create_token(user)}
            _logger.error(traceback.format_exc())

        except (jwt.InvalidTokenError, Exception) as e:
            record = request.env['jwt_provider.access_token'].sudo().search([
                ('token', '=', token)
            ])
            if not record:
                result['message'] = 'Token not found'
                result['code'] = 497
                return result
            else:
                result['code'] = 498
                result['message'] = 'Token invalid'
                _logger.error(traceback.format_exc())
            return result


    def validate_token(self, token):
        try:
            result = {
                'status': False,
                'message': None,
                'code':200
            }
            record = request.env['jwt_provider.access_token'].sudo().search([
                ('token', '=', token)
            ])

            if len(record) != 1 or not record:
                result['message'] = 'Token not found'
                result['code'] = 497
                return result

            payload = jwt.decode(token, SECRET_KEY ,algorithms='HS256')
            user = request.env['res.users'].sudo().search([('id', '=',payload['sub'])], limit=1)
            if not user:
                result['message'] = 'Token for user not found'
                result['code'] = 497
                return result

            uid =self.verify(token) #request.session.finalize()
            # uid = request.session.authenticate(request.session.db, uid=payload['sub'], password=token)
            if not uid:
                result['message'] = 'Token invalid or expired'
                result['code'] = 498
                return result
            result['data'] = {}
            return result
        except jwt.ExpiredSignatureError as ex :
            request.env['jwt_provider.access_token'].sudo().search([
                ('token', '=', token)
            ]).unlink()
            result['message'] = 'Token invalid or expired'
            result['code'] = 498
            _logger.error(traceback.format_exc())
            return result

        except (jwt.InvalidTokenError, Exception) as e:
            record = request.env['jwt_provider.access_token'].sudo().search([
                ('token', '=', token)
            ])
            if not record:
                result['message'] = 'Token not found'
                result['code'] = 497
                return result
            else:
                result['code'] = 498
                result['message'] = 'Token invalid'
                _logger.error(traceback.format_exc())
            return result


validator = Validator()

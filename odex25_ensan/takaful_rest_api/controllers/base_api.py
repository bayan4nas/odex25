# -*- coding: utf-8 -*-
from .main import *
import json
import logging
from odoo import http, modules

_logger = logging.getLogger(__name__)
from odoo.http import request
from odoo import _


class TakafulPortal(http.Controller):
    # Login in System database in website.
    @http.route('/portal/auth/login', auth='public', website=True, methods=['POST'], csrf=False)
    def user_auth_login(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        # User = request.env.user
        #       User.sudo().user_has_groups('base.group_user'))

        try:
            username = kw.get('username', False)
            password = kw.get('password', False)

            # Empty 'username' or 'password:
            if not username or not password:
                message = _("Empty value of 'username' or 'password'!")
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return successful_response(400, data)
                return json.dumps(data)

            # Login in System database:
            try:
                request.session.authenticate(db_name, username, password)
            except:
                # Invalid database:
                message = _("Invalid database!")
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return error_response(500, data)
                return json.dumps(data)

            uid = request.session.uid

            # System login failed:
            if not uid:
                message = _("System User authentication failed!")
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return error_response(401, data)
                return json.dumps(data)

            user_context = request.session.get_context() if uid else None
            company_id = request.env.user.company_id.id if uid else 'null'
            # request.session['taka_us'] = uid
            # request.session['taka_com'] = company_id
            # taka_com = request.session.pop('taka_com') or False
            # taka_us = request.session.pop('taka_us') or False

            # Successful response.
            return successful_response(OUT_SUCCESS_CODE, {
                'status': True,
                'user': {
                    'uid': uid,
                    'mobile': request.env.user.mobile or request.env.user.partner_id.mobile or None,
                    'user_context': user_context,
                    'company_id': company_id,
                },
                'msg': _('Successfully login'),
            })
            return json.dumps({
                'status': True,
                'user': {
                    'uid': uid,
                    'mobile': request.env.user.mobile or request.env.user.partner_id.mobile or None,
                    'user_context': user_context,
                    'company_id': company_id,
                },
                'msg': _('Successfully login'),
            })

        except Exception as e:
            _logger.error(str(e))
            message = str(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    # Login out from System database in website.
    @http.route('/portal/auth/logout', methods=['POST'], auth='user', website=True, csrf=False)
    def user_auth_logout(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        try:
            # Logout from System and close current 'login' session:
            request.session.logout()
            # Successful response:
            return json.dumps({
                'status': True,
                'msg': _('Successfully logout'),
            })

        except Exception as e:
            _logger.error(str(e))
            message = str(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    # Do Verify OTP
    @http.route('/portal/user/verify_otp', auth='public', website=True, methods=['POST'], csrf=False)
    def verify_otp_post_api(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        try:
            mobile = kw.get('mobile', False)
            otp = kw.get('otp', '')

            # Checking and validation
            if all([mobile, otp]):
                if re.match(SAUDI_MOBILE_PATTERN, str(mobile)) == None:
                    message = _('Enter a valid Saudi mobile number')
                    _logger.error(message)
                    data = {'status': False, 'msg': message}
                    return json.dumps(data)

                # OTP verify processing..
                user_id = request.env['res.users'].sudo().search([('mobile', '=', mobile)], limit=1)
                if not user_id:
                    message = _('User account does not exist')
                    _logger.error(message)
                    data = {'status': False, 'msg': message}
                    return json.dumps(data)

                result = user_id.sudo().verify_otp(otp)
                if result['code'] == 200:
                    return json.dumps({
                        'status': True,
                        'msg': _('Verification is successful'),
                    })
                else:
                    message = result['error_descrip']
                    _logger.error(message)
                    data = {'status': False, 'msg': message}
                    return json.dumps(data)

            else:
                message = _('Some or all data is missing')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

        except Exception as e:
            _logger.error(str(e))
            message = str(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    @http.route('/portal/user/request_otp', auth='public', website=True, methods=['POST'], csrf=False)
    def request_otp_post_api(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        try:
            mobile_or_email = kw.get('auth_key', False)
            if not mobile_or_email:
                message = _('Some or all data is missing')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            user_id = request.env['res.users'].sudo().search(
                ['|', ('login', '=', mobile_or_email), ('mobile', '=', mobile_or_email)], limit=1)
            if not user_id:
                message = _('User account does not exist')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            mobile = user_id.mobile or False

            if mobile:
                result = user_id.sudo().request_otp(mobile)
                if result['code'] == 200:
                    return json.dumps({
                        'status': True,
                        'otp': result['results'],
                        'msg': _('OTP code is successfully sent'),
                    })
                else:
                    message = result['error_descrip']
                    _logger.error(message)
                    data = {'status': False, 'msg': message}
                    return json.dumps(data)

            else:
                message = _('This account has not a mobile number')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

        except Exception as e:
            _logger.error(str(e))
            message = str(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    @http.route('/portal/user/reset_password', auth='public', website=True, methods=['POST'], csrf=False)
    def reset_password_user_post_api(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        try:
            password1 = kw.get('password1', False)
            password2 = kw.get('password2', False)
            otp = kw.get('otp', False)
            mobile_or_email = kw.get('auth_key', False)

            if all([mobile_or_email, password1, password2, otp]):

                if password1 != password2:
                    message = _('The entered password does not match')
                    _logger.error(message)
                    data = {'status': False, 'msg': message}
                    return json.dumps(data)

                user_id = request.env['res.users'].sudo().search(
                    ['|', ('login', '=', mobile_or_email), ('mobile', '=', mobile_or_email)], limit=1)
                if not user_id:
                    message = _('User account does not exist')
                    _logger.error(message)
                    data = {'status': False, 'msg': message}
                    return json.dumps(data)

                # Reset..
                result = user_id.sudo().reset_password_using_otp(password1, password2, otp)
                if result['code'] == 200:
                    return json.dumps({
                        'status': True,
                        'msg': _('Password is successfully reset'),
                    })
                else:
                    message = result['error_descrip']
                    _logger.error(message)
                    data = {'status': False, 'msg': message}
                    return json.dumps(data)

            else:
                message = _('Some or all data is missing')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

        except Exception as e:
            _logger.error(str(e))
            message = str(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    @http.route('/portal/user/email_verification', auth='public', website=True, methods=['POST'], csrf=False)
    def email_verification_user_post_api(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        try:
            mobile_or_email = kw.get('auth_key', False)
            if not mobile_or_email:
                message = _('Some or all data is missing')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            user_id = request.env['res.users'].sudo().search(
                ['|', ('login', '=', mobile_or_email), ('mobile', '=', mobile_or_email)], limit=1)
            if user_id:
                # Email verification processing..
                result = user_id.sudo().reset_password_using_email()
                if result['code'] == 200:
                    return json.dumps({
                        'status': True,
                        'email': result['results'],
                        'msg': _('Email verification is successfully sent'),
                    })
                else:
                    message = result['error_descrip']
                    _logger.error(message)
                    data = {'status': False, 'msg': message}
                    return json.dumps(data)
            else:
                message = _('User account does not exist')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

        except Exception as e:
            _logger.error(str(e))
            message = str(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    # The first stage
    @http.route('/portal/create_account', auth='public', website=True, methods=['POST'], csrf=False)
    def get_create_account(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        try:
            # Get parmeters
            account_type = kw.get('account_type', '')
            user_type = kw.get('user_type', 'person')
            first_name = kw.get('first_name', False)
            second_name = kw.get('second_name', False)
            middle_name = kw.get('middle_name', False)
            family_name = kw.get('family_name', False)
            name = kw.get('name', False)
            kw['birth_date'] = kw.pop('DOB')
            mobile = kw.get('mobile', False)
            kw['phone'] = kw.pop('mobile')
            email = kw.get('email', False)
            id_number = kw.get('id_number', False)
            city_id = kw.get('city_id', False)
            gender = kw.get('gender', False)
            activation_mode = kw.get('activation_mode', False)

            # Select which fileds are required or not based on conditions
            if user_type == 'person':
                keys = all(
                    [account_type, first_name, second_name, middle_name, family_name, gender, id_number, mobile, email,
                     city_id, activation_mode])
            elif user_type in ['company', 'charity']:
                keys = all([account_type, name, id_number, mobile, email, city_id, activation_mode])

            if not keys:
                message = _('Some or all data is missing')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            if not account_type in ['benefit', 'sponsor', 'volunteer']:
                message = _('User type value is invalid or missing')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            # Validation Part
            if user_type == 'person':
                if not gender in ['male', 'female']:
                    message = _('Gender value is invalid')
                    _logger.error(message)
                    data = {'status': False, 'msg': message}
                    return json.dumps(data)

            if not user_type in ['person', 'company', 'charity']:
                message = _('User type value is invalid or missing')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            if not activation_mode in ['sms', 'email']:
                message = _('Activation mode value is invalid')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            # Check the city if exist
            city = request.env['res.country.city'].sudo().search([('id', '=', city_id)])
            if not city:
                message = _('This city does not already exist in the system')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            if re.match(SAUDI_MOBILE_PATTERN, str(mobile)) == None:
                message = _('Enter a valid Saudi mobile number')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            # Check the id_number if exist
            res = request.env['res.partner'].sudo().search([('id_number', '=', id_number)])
            if res and len(res) >= 1:
                message = _('This Id Number is already exist')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            res = request.env['res.partner'].sudo().search([('mobile', '=', mobile)])
            if res and len(res) >= 1:
                message = _('This mobile number is already exist')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            res = request.env['res.users'].sudo().search([('login', '=', email)])
            if res and len(res) >= 1:
                message = _('This email is already exist')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            # Todo
            # create user
            # create partner
            # send sms or email
            user = None
            if account_type == 'benefit':
                sponsor_id = request.env['takaful.sponsor'].sudo().search(
                    ['|', ('email', '=', email), ('mobile', '=', mobile)], limit=1)
                user_id = request.env['res.users'].sudo().search(['|', ('email', '=', email), ('mobile', '=', mobile)],
                                                                 limit=1)
                if sponsor_id and user_id and user_id.active is True:
                    message = _('This is moble or email for Sponser acount')
                    _logger.error(message)
                    data = {'status': False, 'msg': message}
                    return json.dumps(data)

                full_name = first_name + " " + second_name + " " + middle_name + " " + family_name
                # user = request.env['res.users'].sudo().with_context(no_reset_password=True).create({
                #     'name': full_name,
                #     'login': email,
                #     'active': True,
                # })

                values = {}
                values['benefit_type'] = 'benefit'
                values['is_responsible'] = True
                values['name'] = full_name
                # values['user_id'] =   user.id
                for field_name, field_value in kw.items():
                    if field_name != "id_number_attach":
                        values[field_name] = field_value

                for fname, fvalue in http.request.httprequest.files.items():
                    datas = base64.encodestring(fvalue.read())
                    if fname in ['iban_attach','id_number_attach','instrument_attach','water_bill_account_attach','electricity_bill_account_attach']:
                        file_name = fvalue.filename
                        attachment_data = {
                        'name':file_name,
                        'datas_fname':file_name,
                        'datas':datas,
                        'res_model':"grant.benefit",
                        }
                        attachment_id = request.env['ir.attachment'].create(attachment_data)                                   
                        values[fname] = [(4,attachment_id.id)]
                    else:
                        values[fname] = datas
                    # values['fname'] = base64.b64encode(fvalue.read())
                partner = request.env['grant.benefit'].sudo().create(values)
                partner.create_user()
                user = partner.user_id
                # print("*******************************")
                # print(partner)
                # partner.sudo().get_benefit_name()
                # End Benefit
            elif account_type == 'volunteer':
                full_name = first_name + " " + second_name + " " + middle_name + " " + family_name
                values = {}

                for field_name, field_value in kw.items():
                    values[field_name] = field_value
                values['name'] = full_name
                values['state'] = 'completing_data'
                partner = request.env['volunteer.volunteer'].sudo().create(values)
                partner.create_user()
                user = partner.user_id
                # pass
            elif account_type == 'sponsor':
                # Create Sponser from here, and all his staff.
                if user_type == 'person':
                    full_name = first_name + " " + second_name + " " + middle_name + " " + family_name

                    sponsor = request.env['takaful.sponsor'].sudo().create({
                        'name': full_name,
                        'first_name': first_name,
                        'second_name': second_name,
                        'middle_name': middle_name,
                        'family_name': family_name,
                        'gender': gender,
                        'id_number': id_number,
                        'company_type': user_type,
                        'email': email,
                        'mobile': mobile,
                        'city_id': city.id if city else False,
                    })
                else:
                    sponsor = request.env['takaful.sponsor'].sudo().create({
                        'name': name,
                        'id_number': id_number,
                        'company_type': user_type,
                        'email': email,
                        'mobile': mobile,
                        'city_id': city.id if city else False,
                    })
                user = sponsor.user_id
                # End Sponsor

            if user:
                # Remove any defualt groups
                user.sudo().remove_access_groups()
                user.sudo().write({
                    'groups_id': [(4, request.env.ref('base.group_portal', False).id)],
                })
                user.sudo().write({
                    'groups_id': [(3, request.env.ref('base.group_user', False).id)],
                })

                # Assign access groups according to account_type
                if account_type == 'sponsor':
                    user.sudo().write({
                        'groups_id': [(4, request.env.ref('odex_takaful.takaful_group_user_sponsor', False).id)],
                    })

            if activation_mode == 'sms' and user:
                # With SMS Verification
                result = user.sudo().request_otp(mobile)
                return json.dumps({
                    'status': True,
                    'user': {'mobile': mobile},
                })
            elif activation_mode == 'email' and user:
                # With Email Verification
                result = user.sudo().reset_password_using_email()
                return json.dumps({
                    'status': True,
                    'user': {'email': email},
                })

            # Return OK
            # return json.dumps({'status': True,})
        except Exception as e:
            _logger.error(str(e))
            message = str(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    # Fetch All the country
    @http.route('/portal/country', auth='public', website=True, csrf=False)
    def get_countries(self):
        try:
            country = http.request.env['res.country'].sudo().search([])
            return json.dumps({'country': [(s.id, s.name) for s in country]})
        except Exception as e:
            _logger.error(str(e))
            message = str(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    # Fetch All the States
    @http.route('/portal/states', auth='public', website=True, csrf=False)
    def load_states(self):
        try:
            states = http.request.env['res.country.state'].sudo().search([])
            return json.dumps({'states': [(s.id, s.name) for s in states]})
        except Exception as e:
            _logger.error(str(e))
            message = str(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    # Fetch All the cities for portal
    @http.route('/portal/sys/city_list', methods=["GET"], auth='public', website=True, csrf=False)
    def get_portal_city_list(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        try:
            # Set parmeters.
            model = 'res.country.city'
            fields = ['id', 'name']
            result = request.env[model].sudo().search_read([], fields)
            dict_data = {
                'status': True,
                'count': len(result),
                'results': result or [],
            }
            return json.dumps(dict_data)
        except Exception as e:
            _logger.error(str(e))
            message = str(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    @http.route('/portal/cities', auth='public', methods=["GET"], website=True, csrf=False)
    def load_cities(self, **kw):
        try:
            state_id = kw.get('state_id')
            domain = []
            if state_id:
                domain = [('state_id', '=', int(state_id))]
            cities = http.request.env['res.country.city'].sudo().search(domain)
            return json.dumps({'cities': [(s.id, s.name) for s in cities]})
        except Exception as e:
            _logger.error(str(e))
            message = str(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    def successful_response(self, dict_data, status=200, ):
        resp = werkzeug.wrappers.Response(
            status=status,
            content_type='application/json; charset=utf-8',
            # headers = None,
            response=json.dumps(dict_data),
        )
        # Remove cookie session
        resp.set_cookie = lambda *args, **kwargs: None
        return resp

    # Fetch All the banks
    @http.route('/api/banks', auth='public', methods=["GET"], csrf=False, type='http')
    def get_banks(self):
        try:
            model = 'res.bank'
            fields = ['id', 'name']
            result = []
            result.append({'id': 0, 'name': ("لايوجد")})
            result.extend(request.env[model].sudo().search_read([], fields))
            dict_data = {
                'status': True,
                'count': len(result),
                'results': result or [],
            }
            return self.successful_response(dict_data)
        except Exception as e:
            _logger.error(str(e))
            message = str(e)
            data = {'status': False, 'msg': message}
            return self.successful_response(dict_data, 500)

# -*- coding: utf-8 -*-
from .main import *

import logging
from ast import literal_eval

from odoo import _
from odoo import http
from odoo.http import request
from dateutil.parser import parse

from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)


class ControllerREST(http.Controller):
    @http.route('/api/data/push',auth='none', type='http', methods=["POST"], csrf=False)
    @make_response()
    def test_push_data(self, **kw):
        eval_request_params(kw)
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context
        # user = request.env['res.users'].sudo().search([('id', '=', 1)], limit=1)
        model = 'res.partner'
        fields = ['id', 'city_id']
        result = request.env[model].sudo().search_read([], fields)

        return {
            # "code": 201,
            'dict_data': {
                "is_null": '',
                'result': result,
                # 'user': props(user),
                "is_none": None,
                'is_read': True,
                'is_gift': False,
                "status": "data-valid",
                "message": _('Email verification is successfully sent'),
            }
        }

    def get_default_sponsorship_amount(self):
        # Get from config
        sudoConf = request.env['ir.config_parameter'].sudo()
        min_kafala = float(sudoConf.get_param('odex_takaful_base.min_kafala', 300))
        return min_kafala

    def get_user_sponsor_info(self, uid):
        user_id = request.env['res.users'].sudo().browse(uid)
        partner_id = user_id.partner_id
        sponsor_id = request.env['takaful.sponsor'].sudo().search([('partner_id', '=', partner_id.id)], limit=1)
        
        return {
            "user_id": user_id, 
            "sponsor_id": sponsor_id, 
            "partner_id": partner_id, 
        }

    def get_sponsorship_benefit_info(self, benefit_id, benefit_type, full=True):
        data = {}

        if not benefit_id or not benefit_type:
            return False
        
        benefit = request.env['grant.benefit'].sudo().search([('id', '=', benefit_id)], limit=1)
        
        if not benefit:
            return False

        if benefit.benefit_type != benefit_type:
            return False
  
        data['id'] = benefit.id

        if full:
            data['name'] = benefit.name
        else:
            data['first_name'] = benefit.first_name

        data['age'] = benefit.age
        data['city_id'] = benefit.city_id.name
        data['number'] = benefit.housing_id.house_number
        data['benefit_type'] = benefit.benefit_type
        data['has_needs'] = benefit.has_needs
        data['has_arrears'] = benefit.has_arrears
        
        if benefit_type == "widow":
            data['total_income'] = benefit.total_income
            data['orphan_ids'] = benefit.orphan_ids.ids
            data['orphan_count'] = len(benefit.orphan_ids) or 0

            salary_resouces = []
            for source in benefit.salary_ids:
                if source.salary_type:
                    salary_resouces.append(source.salary_type)
            data['salary_resouces'] = salary_resouces
            
        if benefit_type == "orphan":
            data['gender'] = benefit.gender
            data['orphan_status'] = benefit.orphan_status

            data['education_level'] = benefit.education_level
            data['class_room'] = benefit.classroom
            data['quran_parts'] = benefit.number_parts or 0

        data['responsible'] = benefit.responsible
        data['health_status'] = benefit.health_status

        data['housing_status'] = benefit.housing_id.property_type
        data['education_status'] = benefit.education_status

        skills = []
        for skill in benefit.craft_skill_ids:
            skills.append(skill.name)

        for skill in benefit.training_inclinations_ids:
            skills.append(skill.name)

        data['skills'] = skills

        data['benefit_available_need'] = float(format(benefit.benefit_needs_value, '.2f'))
        data['benefit_needs_percent'] = float(format(benefit.benefit_needs_percent, '.2f'))
        data['benefit_arrears_value'] = float(format( benefit.benefit_arrears_value, '.2f'))
        try:
            data['benefit_total_need'] = float(format(benefit.total_expenses, '.2f'))
        except Exception as e:
            data['benefit_total_need'] = 0
        
        # Needs of benefit
        domain = [
            '&',
            ('benefit_id','=', benefit.id),
            ('remaining_amount','>', 0),
            ('state','=', 'published'), 
        ]
        needs = request.env['benefits.needs'].sudo().search_read(domain, ['name']) or []
        data['needs'] = needs

        return data


    @http.route('/api/sponsor/registeration', methods=["POST"], type='http', auth='none',  csrf=False)
    def register_user_post_api(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        user_type_kw = kw.get('user_type', '')
        first_name = kw.get('first_name', False)
        second_name = kw.get('second_name', False)
        middle_name = kw.get('middle_name', False)
        family_name = kw.get('family_name', False)
        name = kw.get('name', False)

        mobile_kw = kw.get('mobile', False)
        email_kw = kw.get('email', False)
        id_number = kw.get('id_number', False)
        city_kw = kw.get('city', False)
        gender_kw = kw.get('gender', False)
        activation_mode_kw = kw.get('activation_mode', False)

        if not user_type_kw in ['person', 'company']:
            error_descrip = _('User type value is invalid or missing')
            error = 'invalid_user_type'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        if user_type_kw == 'person':
            keys = all([first_name, second_name, middle_name, family_name, gender_kw, id_number, mobile_kw, email_kw, city_kw, activation_mode_kw])
        else:
            keys =all([name, id_number, mobile_kw, email_kw, city_kw, activation_mode_kw])

        if not keys:
            error_descrip = _('Some or all data is missing')
            error = 'missing_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        # Validation Part
        if user_type_kw == 'person':
            if not gender_kw in ['male', 'female']:
                error_descrip = _('Gender value is invalid')
                error = 'invalid_gender'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

        if not activation_mode_kw in ['sms', 'email']:
            error_descrip = _('Activation mode value is invalid')
            error = 'invalid_activation_mode'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)
    
        # Check the city if exist
        city = request.env['res.country.city'].sudo().search([('id','=',city_kw)])
        if not city:
            error_descrip = _('This city does not already exist in the system')
            error = 'does_not_exist'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)
            
        if re.match(SAUDI_MOBILE_PATTERN, str(mobile_kw)) == None:
            error_descrip = _('Enter a valid Saudi mobile number')
            error = 'invalid_mobile'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        res = request.env['res.partner'].sudo().search([('id_number','=',id_number)])
        if res and len(res) >=1:
            error_descrip = _('This Id Number is already exist')
            error = 'already_exist'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        res = request.env['res.partner'].sudo().search([('mobile','=',mobile_kw)])
        if res and len(res) >=1:
            error_descrip = _('This mobile number is already exist')
            error = 'already_exist'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        res = request.env['res.users'].sudo().search([('login','=',email_kw)])
        if res and len(res) >=1:
            error_descrip = _('This email is already exist')
            error = 'already_exist'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)
            
        # Create Sponser from here, and complete its record later.
        if user_type_kw == 'person':
            full_name = first_name + " " + second_name + " " + middle_name + " " + family_name

            sponsor = request.env['takaful.sponsor'].sudo().create({
                'name': full_name,
                'first_name': first_name,
                'second_name': second_name,
                'middle_name': middle_name,
                'family_name': family_name,
                'gender': gender_kw,
                'id_number': id_number,
                'company_type': user_type_kw,
                'email': email_kw,
                'mobile': mobile_kw,
                'city_id': city.id if city else False,
                })
        else:
            sponsor = request.env['takaful.sponsor'].sudo().create({
                'name': name,
                'id_number': id_number,
                'company_type': user_type_kw,
                'email': email_kw,
                'mobile': mobile_kw,
                'city_id': city.id if city else False,
                })

        if activation_mode_kw == 'email':
            # With Email Verification
            result = sponsor.user_id.sudo().reset_password_using_email()
            if result['code']==200:
                return successful_response( 
                    status = OUT_SUCCESS_CODE,
                    dict_data = result['results']
                )
            else:
                code = result['code']
                error_descrip = result['error_descrip']
                error = result['error']
                _logger.error(error_descrip)
                return error_response(code, error, error_descrip)
        else:
            # With SMS Verification
            result = sponsor.user_id.sudo().request_otp(mobile_kw)
            if result['code']==200:
                return successful_response( 
                    status = OUT_SUCCESS_CODE,
                    dict_data = result['results']
                )
            else:
                code = result['code']
                error_descrip = result['error_descrip']
                error = result['error']
                _logger.error(error_descrip)
                return error_response(code, error, error_descrip)
           

    @http.route('/api/sys/get_sponsorship_value', methods=['GET'], type='http', auth='none')
    @check_permissions
    def sys_sponsorship_value(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context
        
        sponsorship_value = {'sponsorship_value': self.get_default_sponsorship_amount()}
        # send HTTP response
        return successful_response( 
            status = OUT_SUCCESS_CODE,
            dict_data = sponsorship_value,
        )

    # For notifications
    @http.route('/api/sponsor/notifications/page/<page>', methods=["GET"], type='http', auth='none')
    @check_permissions
    def get_notification_list(self, page, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        if page:
            try:
                offset = (int(page) * PAGE_SIZE) - PAGE_SIZE
                limit = PAGE_SIZE
            except Exception as e:
                return error_response_404_url_not_found()       
        else:
            offset = 0
            limit=None

        is_read = kw.get('is_read', '')
        
        uid = request.session.uid
        # Set parmeters.
        model = "takaful.push.notification"
        fields = [
            'id',
            'title',
            'body',
            'sent_on',
            'is_read',
            'end_date',
        ]

        if is_read == 'yes':
            domain = [('user_id', '=', uid), ('is_read', '=', True)]
        elif is_read == 'no':
            domain = [('user_id', '=', uid), ('is_read', '=', False)]
        else:
            domain = [('user_id', '=', uid)]

        result = request.env[model].sudo().search_read(domain,fields, offset=offset, limit=limit)
        if result:
            count = len(result)
        else:
            result = []
            count = 0
        return successful_response( 
            status = OUT_SUCCESS_CODE,
            dict_data = {
                'count': count,
                'results': result,
                }
        )

    # For notifications: Read one
    @http.route('/api/sponsor/notify/read/<id>', methods=["GET"], type='http', auth='none')
    @check_permissions
    def read_notification_id(self, id, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        try:
            object_id = int(id)
        except Exception as e:
            return error_response_404_url_not_found()

        # Set parmeters.
        model = "takaful.push.notification"
        uid = request.session.uid
        domain = [('id', '=', object_id), ('user_id', '=', uid)]

        res = request.env[model].sudo().search(domain, limit=1)
        if res:  
            return successful_response( 
                status = OUT_SUCCESS_CODE,
                dict_data = {
                    'id': res.id,
                    'title': res.title,
                    'body': res.body,
                    'sent_on': res.sent_on,
                    # 'is_read': res.is_read,
                    }
            )
        else:
            error_descrip = _('No notification is found')
            error = 'does_not_exist'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

    # For notifications: Delete one
    @http.route('/api/sponsor/notify/delete/<id>', methods=["GET"], type='http', auth='none')
    @check_permissions
    def delete_notification_id(self, id, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        try:
            object_id = int(id)
        except Exception as e:
            return error_response_404_url_not_found()

        # Set parmeters.
        model = "takaful.push.notification"
        uid = request.session.uid
        domain = [('id', '=', object_id), ('user_id', '=', uid)]

        res = request.env[model].sudo().search(domain, limit=1)
        if res: 
            try:
                res.unlink()
                return successful_response( 
                    status = OUT_SUCCESS_CODE,
                    dict_data = {}
                )
            except Exception as e:
                error_descrip = _('Cannot delete this notification')
                error = 'failed_operation'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)
            
        else:
            error_descrip = _('This notification is found')
            error = 'does_not_exist'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

    # For Sponsor Info
    @http.route('/api/sponsor/profile', methods=["GET"], type='http', auth='none')
    @check_permissions
    def get_sponsor_info(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        # Set parmeters.
        uid = request.session.uid
        user_data = self.get_user_sponsor_info(uid)
        sponsor_id = user_data["sponsor_id"]

        if sponsor_id:   
            if sponsor_id.company_type == "company":
                dict_data = {
                    'id': sponsor_id.id,
                    'name': sponsor_id.name,
                    'id_number': sponsor_id.id_number,
                    'company_type': sponsor_id.company_type,
                    'email': sponsor_id.email,
                    'mobile': sponsor_id.mobile,
                    'city_name': sponsor_id.city_id.name,
                    # Bank info
                    'account_number': sponsor_id.account_number,
                    'iban': sponsor_id.iban,
                    'bank_id': sponsor_id.bank_id.id,
                    'bank_name': sponsor_id.bank_id.name,
                    'bank_entity_name': sponsor_id.bank_entity_name,
                }
            else:
                dict_data = {
                    'id': sponsor_id.id,
                    'name': sponsor_id.name,
                    'first_name': sponsor_id.first_name,
                    'second_name': sponsor_id.second_name,
                    'middle_name': sponsor_id.middle_name,
                    'family_name': sponsor_id.family_name,
                    'gender': sponsor_id.gender,
                    'id_number': sponsor_id.id_number,
                    'company_type': sponsor_id.company_type,
                    'email': sponsor_id.email,
                    'mobile': sponsor_id.mobile,
                    'city_id': sponsor_id.city_id.id,
                    'city_name': sponsor_id.city_id.name,
                    # Bank info
                    'account_number': sponsor_id.account_number,
                    'iban': sponsor_id.iban,
                    'bank_id': sponsor_id.bank_id.id,
                    'bank_name': sponsor_id.bank_id.name,
                    'bank_entity_name': sponsor_id.bank_entity_name,
                }
            return successful_response( 
                status = OUT_SUCCESS_CODE,
                dict_data = dict_data
            )
        else:
            error_descrip = _('No sponsor is found')
            error = 'does_not_exist'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

    # Update Record for Sponsor
    @http.route('/api/sponsor/profile/update', methods=['POST'], type='http', auth='none',  csrf=False)
    @check_permissions
    def do_update_sponsor_profile(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        updated_fields = [
            'mobile',
            'city_id',
            # Bank info
            'account_number',
            'iban',
            'bank_id',
            'bank_entity_name',
        ]
        values = {}
        for field_name, field_value in kw.items():
            if not field_name in updated_fields:
                error_descrip = _('Cannot update this field: %s ') % field_name
                error = 'invalid_data'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)
            values[field_name] = field_value
        
        if not values:
            error_descrip = _('Some or all data is missing')
            error = 'missing_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        mobile = values.get('mobile', False)
        if mobile and re.match(SAUDI_MOBILE_PATTERN, str(mobile)) == None:
            error_descrip = _('Enter a valid Saudi mobile number')
            error = 'invalid_mobile'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        uid = request.session.uid
        user_data = self.get_user_sponsor_info(uid)
        sponsor_id = user_data["sponsor_id"]

        if sponsor_id:   
            try:
                # Update Record forthis Sponsor
                sponsor_id.sudo().write(values)
                return successful_response( 
                    OUT_SUCCESS_CODE,
                    {},
                )
            except Exception as e:
                error_descrip = _('Faield to update this sponsor')
                error = 'failed_operation'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)
        else:
            error_descrip = _('No sponsor is found')
            error = 'does_not_exist'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

    # Sponsor notify_setting
    @http.route('/api/sponsor/notify_setting', methods=["GET"], type='http', auth='none')
    @check_permissions
    def get_sponsor_notify_setting(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        # Set parmeters.
        uid = request.session.uid
        user_data = self.get_user_sponsor_info(uid)
        sponsor_id = user_data["sponsor_id"]

        if sponsor_id:   
            dict_data = {
                # notify info
                'notify_by_app': sponsor_id.notify_by_app,
                'notify_by_sms': sponsor_id.notify_by_sms,
                'notify_month_day': sponsor_id.notify_month_day,
                'notify_pay_by_app': sponsor_id.notify_pay_by_app,
                'notify_pay_by_sms': sponsor_id.notify_pay_by_sms,
            }
            return successful_response( 
                status = OUT_SUCCESS_CODE,
                dict_data = dict_data
            )
        else:
            error_descrip = _('No sponsor is found')
            error = 'does_not_exist'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

    # Update notify settings for Sponsor
    @http.route('/api/sponsor/notify_setting/update', methods=['POST'], type='http', auth='none',  csrf=False)
    @check_permissions
    def do_update_sponsor_notify_setting(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        updated_fields = [
            'notify_by_app',
            'notify_by_sms',
            'notify_month_day',
            'notify_pay_by_app',
            'notify_pay_by_sms',
        ]
        values = {}
        for field_name, field_value in kw.items():
            if not field_name in updated_fields:
                error_descrip = _('Cannot update this field: %s ') % field_name
                error = 'invalid_data'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)
            values[field_name] = field_value
        
        if not values:
            error_descrip = _('Some or all data is missing')
            error = 'missing_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        uid = request.session.uid
        user_data = self.get_user_sponsor_info(uid)
        sponsor_id = user_data["sponsor_id"]

        if sponsor_id:   
            try:
                # Update Record forthis Sponsor
                sponsor_id.sudo().write(values)
                return successful_response( 
                    OUT_SUCCESS_CODE,
                    {},
                )
            except Exception as e:
                error_descrip = _('Faield to update these settings')
                error = 'failed_operation'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)
        else:
            error_descrip = _('No sponsor is found')
            error = 'does_not_exist'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

    # Sponsor certificate_setting
    @http.route('/api/sponsor/certificate_setting', methods=["GET"], type='http', auth='none')
    @check_permissions
    def get_sponsor_certificate_setting(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        # Set parmeters.
        uid = request.session.uid
        user_data = self.get_user_sponsor_info(uid)
        sponsor_id = user_data["sponsor_id"]

        if sponsor_id:   
            dict_data = {
                # name_in_certificate info
                'name_in_certificate': sponsor_id.name_in_certificate,
                'type_in_certificate': sponsor_id.type_in_certificate,
                'duration_in_certificate': sponsor_id.duration_in_certificate,
            }
            return successful_response( 
                status = OUT_SUCCESS_CODE,
                dict_data = dict_data
            )
        else:
            error_descrip = _('No sponsor is found')
            error = 'does_not_exist'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

    # Update certificate settings for Sponsor
    @http.route('/api/sponsor/certificate_setting/update', methods=['POST'], type='http', auth='none',  csrf=False)
    @check_permissions
    def do_update_sponsor_certificate_setting(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context
 
        updated_fields = [
            'name_in_certificate',
            'type_in_certificate',
            'duration_in_certificate',
        ]
        values = {}
        for field_name, field_value in kw.items():
            if not field_name in updated_fields:
                error_descrip = _('Cannot update this field: %s ') % field_name
                error = 'invalid_data'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)
            values[field_name] = field_value
        
        if not values:
            error_descrip = _('Some or all data is missing')
            error = 'missing_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        uid = request.session.uid
        user_data = self.get_user_sponsor_info(uid)
        sponsor_id = user_data["sponsor_id"]

        if sponsor_id:   
            try:
                # Update Record forthis Sponsor
                sponsor_id.sudo().write(values)
                return successful_response( 
                    OUT_SUCCESS_CODE,
                    {},
                )
            except Exception as e:
                error_descrip = _('Faield to update these settings')
                error = 'failed_operation'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)
        else:
            error_descrip = _('No sponsor is found')
            error = 'does_not_exist'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

    # Get Benefit Filters
    @http.route('/api/sys/benefit_filters', methods=['GET'], type='http', auth='none')
    @check_permissions
    def get_benefit_filters(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        benefit_type = kw.get('benefit_type', False)
        if not benefit_type:
            error_descrip = _('Missing data for Orphan or Widow')
            error = 'missing_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        if not benefit_type in ['orphan', 'widow']:
            error_descrip = _('Invalid Orphan or Widow')
            error = 'invalid_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        if benefit_type == 'orphan':
            filters = [
                # For Field of: gender
                {
                    'name': 'gender',
                    'value': 'male',
                    'title': _('Male'),
                    'state': True,
                },
                {
                    'name': 'gender',
                    'value': 'female',
                    'title': _('Female'),
                    'state': True,
                },
                # For Field of: orphan_status
                {
                    'name': 'orphan_status',
                    'value': 'parent',
                    'title': _('Parent-Orphan'),
                    'state': True,
                },
                {
                    'name': 'orphan_status',
                    'value': 'father',
                    'title': _('Father-Orphan'),
                    'state': True,
                },
                {
                    'name': 'orphan_status',
                    'value': 'mother',
                    'title': _('Mother-Orphan'),
                    'state': True,
                },
                # For Field of: has_needs
                {
                    'name': 'has_needs',
                    'value': 'true',
                    'title': _('Has Needs'),
                    'state': False,
                },
                # For Field of: has_arrears
                {
                    'name': 'has_arrears',
                    'value': True,
                    'title': _('Has Arrears'),
                    'state': False,
                },
                
            ]
        else:
            filters = [
                # For Field of: has_needs
                {
                    'name': 'has_needs',
                    'value': 'true',
                    'title': _('Has Needs'),
                    'state': False,
                },
                # For Field of: has_arrears
                {
                    'name': 'has_arrears',
                    'value': True,
                    'title': _('Has Arrears'),
                    'state': False,
                },
                            
            ]

        # Return Benefitfilters
        return successful_response( 
            status = OUT_SUCCESS_CODE,
            dict_data = filters
        )

    @http.route('/api/sys/benefits/page/<page>', methods=["GET"], type='http', auth='none')
    @check_permissions
    def sys_get_benefits(self, page, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        if page:
            try:
                offset = (int(page) * PAGE_SIZE) - PAGE_SIZE
                limit = PAGE_SIZE
            except Exception as e:
                return error_response_404_url_not_found()       
        else:
            offset = 0
            limit=None

        benefit_type = kw.get('benefit_type', False)
        
        if not benefit_type:
            error_descrip = _('Missing data for Orphan or Widow')
            error = 'missing_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        if not benefit_type in ['orphan', 'widow']:
            error_descrip = _('Invalid Orphan or Widow')
            error = 'invalid_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        filters = []
        domain = [['benefit_type', '=', benefit_type]]
        for field_name, field_value in kw.items():
            if field_value and type(field_value) is str:
                if field_value == "true":
                    filters.append([field_name, '=', True])
                    continue
                elif field_value == "false":
                    filters.append([field_name, '=', False])
                    continue

                try:
                    field_value = literal_eval(field_value)
                except Exception as e:
                    pass

                if type(field_value) is list:
                    filters.append([field_name, 'in', field_value])
                elif type(field_value) is str or type(field_value) is int or type(field_value) is float:
                    filters.append([field_name, '=', field_value])

            elif field_value and type(field_value) is list:
                filters.append([field_name, 'in', field_value])

            elif field_value and (type(field_value) is list or type(field_value) is int or type(field_value) is float):
                filters.append([field_name, '=', field_value])

        if filters:
            domain += filters

        # Get from config
        sudoConf = request.env['ir.config_parameter'].sudo()
        new_kafala = sudoConf.get_param('odex_takaful_base.new_kafala')

        # Set parmeters.
        model = 'grant.benefit'
        if new_kafala == "always":
            full=True
        else:
            full=False

        benefits = request.env[model].sudo().search(domain, offset=offset, limit=limit)
        result = []
        for ben in benefits:
            res = self.get_sponsorship_benefit_info(str(ben.id), benefit_type, full=full)
            if res:
                result.append(res)
    
        if result:
            count = len(result)
        else:
            result = []
            count = 0
        return successful_response( 
            status = OUT_SUCCESS_CODE,
            dict_data = {
                'count': count,
                'results': result,
                }
        )

    # Get User Sponsorships
    @http.route('/api/sponsor/sponsorships/page/<page>', methods=["GET"], type='http', auth='none')
    @check_permissions
    def user_get_sponsorships(self, page, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        if page:
            try:
                offset = (int(page) * PAGE_SIZE) - PAGE_SIZE
                limit = PAGE_SIZE
            except Exception as e:
                return error_response_404_url_not_found()       
        else:
            offset = 0
            limit=None

        
        benefit_type = kw.get('benefit_type', False)
        if not benefit_type:
            error_descrip = _('Missing data for Orphan or Widow')
            error = 'missing_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        if not benefit_type in ['orphan', 'widow']:
            error_descrip = _('Invalid Orphan or Widow')
            error = 'invalid_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        uid = request.session.uid
        user_data = self.get_user_sponsor_info(uid)
        sponsor_id = user_data["sponsor_id"]

        # Set parmeters.
        model = "takaful.sponsorship"
        fields = [
            'id',
            'state',
            'start_date',
            'next_due_date',
            'expected_cancel_date',
            'end_date',
            'month_count',
            'paid_month_count',
            'contribution_value',
            'sponsorship_class',
            'sponsorship_duration',
            'benefit_ids',
            'benefit_id',
            'has_delay',
            'has_needs',
        ]
        

        if benefit_type == 'widow':
            fields += [
                'is_widow_orphan',
                'orphan_ids',
            ]

        filters = []
        domain = [['sponsor_id', '=', sponsor_id.id], ['benefit_type', '=', benefit_type]]
        for field_name, field_value in kw.items():
            if field_value and type(field_value) is str:
                if field_value == "true":
                    filters.append([field_name, '=', True])
                    continue
                elif field_value == "false":
                    filters.append([field_name, '=', False])
                    continue

                try:
                    field_value = literal_eval(field_value)
                except Exception as e:
                    pass

                if type(field_value) is list:
                    filters.append([field_name, 'in', field_value])
                elif type(field_value) is str or type(field_value) is int or type(field_value) is float:
                    filters.append([field_name, '=', field_value])

            elif field_value and type(field_value) is list:
                filters.append([field_name, 'in', field_value])

            elif field_value and (type(field_value) is list or type(field_value) is int or type(field_value) is float):
                filters.append([field_name, '=', field_value])

        if filters:
            domain += filters
        else:
            if benefit_type == 'orphan':
                filters = [
                    ['gender', 'in', ['male', 'female']],
                    ['state', 'in', ['draft', 'confirmed', 'wait_pay', 'progress', 'to_cancel', 'canceled', 'closed']],
                ]
                domain += filters
            elif benefit_type == 'widow':
                filters = [
                    ['state', 'in', ['draft', 'confirmed', 'wait_pay', 'progress', 'to_cancel', 'canceled', 'closed']],
                ]
                domain += filters

        result = request.env[model].sudo().search_read(domain,fields, offset=offset, limit=limit)
        if result:
            count = len(result)
        else:
            result = []
            count = 0
        return successful_response( 
            status = OUT_SUCCESS_CODE,
            dict_data = {
                'count': count,
                'results': result,
                }
        )

    # Get Beneficiary Details
    @http.route('/api/sponsor/benefit/info', methods=["GET"], type='http', auth='none')
    @check_permissions
    def user_get_benefit(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        benefit_type = kw.get('benefit_type', False)
        benefit_id = kw.get('benefit_id', False)
        
        if not all([benefit_type, benefit_id]):
            error_descrip = _('Some or all data is missing')
            error = 'missing_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        if not benefit_type in ['orphan', 'widow']:
            error_descrip = _('Invalid Orphan or Widow')
            error = 'invalid_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        try:
            benefit_id = int(benefit_id)
        except Exception as e:
            error_descrip = _('Invalid Id for Orphan or Widow')
            error = 'invalid_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        record = self.get_sponsorship_benefit_info(benefit_id, benefit_type)
        if not record:
            return error_response_404__not_found_object_in_system()

        return successful_response( 
            status = OUT_SUCCESS_CODE,
            dict_data = record
        )

    # Get Cancel Reasons List
    @http.route('/api/sys/reason_list', methods=["GET"], type='http', auth='none')
    @check_permissions
    def get_reason_list(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_SY'})
        request.env.context = context

        # Set parmeters.
        model = 'sponsorship.reason.stop'
        fields = ['id', 'name']
        result = request.env[model].sudo().search_read([],fields)
        return successful_response( 
            status = OUT_SUCCESS_CODE,
            dict_data = {
                'count': len(result),
                'results': result,
                }
        )

    # Create Cancel Record for Sponsorship: Do Cancel for Sponsorship
    @http.route('/api/sponsor/sponsorships/cancel', methods=['POST'], type='http', auth='none',  csrf=False)
    @check_permissions
    def do_cancel_sponsorship(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_SY'})
        request.env.context = context

        sponsorship_id = kw.get('sponsorship_id', False)
        reason_id = kw.get('reason_id', False)
        
        if not all([sponsorship_id, reason_id]):
            error_descrip = _('Some or all data is missing')
            error = 'missing_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        try:
            sponsorship_id = int(sponsorship_id)
            reason_id = int(reason_id)
        except Exception as e:
            error_descrip = _('Invalid Id for Sponsorship or Reason')
            error = 'invalid_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        reason = request.env['sponsorship.reason.stop'].sudo().search([('id','=',reason_id)], limit=1)
        if not reason:
            error_descrip = _('This Reason does not exist in the system')
            error = 'does_not_exist'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        uid = request.session.uid
        user_data = self.get_user_sponsor_info(uid)
        sponsor_id = user_data["sponsor_id"]

        sponsorship = request.env['takaful.sponsorship'].sudo().search([('id','=',sponsorship_id), ('sponsor_id','=',sponsor_id.id)], limit=1)
        if not sponsorship:
            error_descrip = _('This Sponsorship does not exist in the system')
            error = 'does_not_exist'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        if sponsorship.state == "canceled":
            error_descrip = _('This Sponsorship is already canceled')
            error = 'already_canceled'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        cancel_reason_id = request.env['sponsorship.cancellation'].sudo().search([('sponsorship_id','=', sponsorship.id)], limit=1)
        if cancel_reason_id:
            error_descrip = _('This Sponsorship is under review for cancel')
            error = 'under_review'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        # Create Manual cancellation record by current user
        draft_cancel = request.env['sponsorship.cancellation'].sudo().create({
            'sponsorship_id': sponsorship_id,
            'reason_id': reason_id,
            'cancel_type': "user",
            'state': "draft",
            'cancel_user_id': uid,
            'note': _('The Sponsor request to cancel this Sponsorship'),
        })
        
        return successful_response( 
            OUT_SUCCESS_CODE,
            {},
        )


    @http.route('/api/sys/sponsorship_filters', methods=['GET'], type='http', auth='none')
    @check_permissions
    def get_sponsorship_filters(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_SY'})
        request.env.context = context

        benefit_type = kw.get('benefit_type', False)
       
        if not benefit_type in ['orphan', 'widow']:
            error_descrip = _('Invalid Orphan or Widow')
            error = 'invalid_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)
        
        if benefit_type == 'orphan':
            filters = [
                # For Field of: gender
                {
                    'name': 'gender',
                    'value': 'male',
                    'title': _('Male'),
                    'state': True,
                },
                {
                    'name': 'gender',
                    'value': 'female',
                    'title': _('Female'),
                    'state': True,
                },
                {
                    'name': 'orphan_status',
                    'value': 'parent',
                    'title': _('Parent-Orphan'),
                    'state': True,
                },
                {
                    'name': 'orphan_status',
                    'value': 'father',
                    'title': _('Father-Orphan'),
                    'state': True,
                },
                {
                    'name': 'orphan_status',
                    'value': 'mother',
                    'title': _('Mother-Orphan'),
                    'state': True,
                },
                # For Field of: has_dalay
                {
                    'name': 'has_dalay',
                    'value': 'true',
                    'title': _('Has Delay Payments'),
                    'state': False,
                },
                # For Field of: state (Sponsorship Status)
                {
                    'name': 'state',
                    'value': 'draft',
                    'title': _('Waiting To Confirm'),
                    'state': True,
                },
                {
                    'name': 'state',
                    'value': 'confirmed',
                    'title': _('Confirmed'),
                    'state': True,
                },
                {
                    'name': 'state',
                    'value': 'wait_pay',
                    'title': _('Waiting Payment'),
                    'state': True,
                },
                {
                    'name': 'state',
                    'value': 'progress',
                    'title': _('In Progress'),
                    'state': True,
                },
                {
                    'name': 'state',
                    'value': 'to_cancel',
                    'title': _('About To Cancel'),
                    'state': True,
                },
                {
                    'name': 'state',
                    'value': 'canceled',
                    'title': _('Canceled'),
                    'state': True,
                },
                {
                    'name': 'state',
                    'value': 'closed',
                    'title': _('Closed'),
                    'state': True,
                },
                # For Field of: has_needs
                {
                    'name': 'has_needs',
                    'value': 'true',
                    'title': _('Has Needs'),
                    'state': False,
                },
                
            ]

        else:
            filters = [
                # For Field of: has_dalay
                {
                    'name': 'has_dalay',
                    'value': 'true',
                    'title': _('Has Delay Payments'),
                    'state': False,
                },
                # For Field of: state (Sponsorship Status)
                {
                    'name': 'state',
                    'value': 'draft',
                    'title': _('Draft'),
                    'state': True,
                },
                {
                    'name': 'state',
                    'value': 'confirmed',
                    'title': _('Confirmed'),
                    'state': True,
                },
                {
                    'name': 'state',
                    'value': 'wait_pay',
                    'title': _('Waiting Payment'),
                    'state': True,
                },
                {
                    'name': 'state',
                    'value': 'progress',
                    'title': _('In Progress'),
                    'state': True,
                },
                {
                    'name': 'state',
                    'value': 'to_cancel',
                    'title': _('About To Cancel'),
                    'state': True,
                },
                {
                    'name': 'state',
                    'value': 'canceled',
                    'title': _('Canceled'),
                    'state': True,
                },
                {
                    'name': 'state',
                    'value': 'closed',
                    'title': _('Closed'),
                    'state': True,
                },
                # For Field of: has_needs
                {
                    'name': 'has_needs',
                    'value': 'true',
                    'title': _('Has Needs'),
                    'state': False,
                },
                
            ]

        # Return sponsorship filters
        return successful_response( 
            status = OUT_SUCCESS_CODE,
            dict_data = filters
        )

    # Get Need Filters
    @http.route('/api/sys/need_filters', methods=['GET'], type='http', auth='none')
    @check_permissions
    def get_need_filters(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_SY'})
        request.env.context = context

        filters = [
            # For Field of: need_status (Need Status)
            {
                'name': 'need_status',
                'value': 'urgent',
                'state': False,
            },
            {
                'name': 'need_status',
                'value': 'not_urgent',
                'state': False,
            },
            # For Field of: benefit_need_type (Need Type)
            {
                'name': 'benefit_need_type',
                'value': 'special',
                'state': False,
            },
            {
                'name': 'benefit_need_type',
                'value': 'general',
                'state': False,
            },
            # For Field of: benefit_type (Benefit Type)
            {
                'name': 'benefit_type',
                'value': 'orphans',
                'state': False,
            },
            {
                'name': 'benefit_type',
                'value': 'widows',
                'state': False,
            },
            {
                'name': 'benefit_type',
                'value': 'both',
                'state': False,
            },
        ]

        # Return need filters
        return successful_response( 
            status = OUT_SUCCESS_CODE,
            dict_data = filters
        )

    # Get all need categories list
    @http.route('/api/sys/need_category_list', methods=["GET"], type='http', auth='none')
    def get_city_list(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_SY'})
        request.env.context = context

        # Set parmeters.
        model = 'needs.categories'
        fields = ['id', 'name']
        result = request.env[model].sudo().search_read([], fields)
        return successful_response(
            status=OUT_SUCCESS_CODE,
            dict_data={
                'count': len(result),
                'results': result,
            }
        )

    # Get Need Types Based on Need Categoey Id
    @http.route('/api/sys/need_types/page/<page>', methods=["GET"], type='http', auth='none')
    @check_permissions
    def get_need_types(self, page, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_SY'})
        request.env.context = context

        if page:
            try:
                offset = (int(page) * PAGE_SIZE) - PAGE_SIZE
                limit = PAGE_SIZE
            except Exception as e:
                return error_response_404_url_not_found()       
        else:
            offset = 0
            limit=None

        need_category_id = kw.get('need_category_id', False)
        need_status = kw.get('need_status', False)
        benefit_id = kw.get('benefit_id', False)
        benefit_type = kw.get('benefit_type', False)
        benefit_need_type = kw.get('benefit_need_type', False)
        
        model = 'benefits.needs'
        fields = [
            'id', 
            'name', 
            'need_status', 
            'benefit_need_type', 
            'benefit_id',
            'benefit_ids',
            'benefit_type',
            'need_category',
            'category_name',
            'state_id',
            'state_name',
            'target_amount',
            'paid_amount',
            'remaining_amount',
            'completion_ratio',
        ]
        domain = [
            '&',
            ('remaining_amount','>', 0),
            ('state','=', 'published'), 
        ]

        if need_category_id:
            try:
                need_category_id = int(need_category_id)
            except Exception as e:
                error_descrip = _('Invalid value for %s ') % 'need_category_id'
                error = 'invalid_data'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)
            domain += [('need_category','=', need_category_id)]

        if benefit_id:
            try:
                benefit_id = int(benefit_id)
            except Exception as e:
                error_descrip = _('Invalid value for %s ') % 'benefit_id'
                error = 'invalid_data'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)
            domain += [('benefit_id','=', benefit_id)]

        if benefit_type:
            if not benefit_type in ['orphans', 'widows' , 'both']:
                error_descrip = _('Invalid value for %s ') % 'benefit_type'
                error = 'invalid_data'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)
            domain += [('benefit_type','=', benefit_type)]

        if need_status:
            if not need_status in ['urgent', 'not_urgent']:
                error_descrip = _('Invalid value for %s ') % 'need_status'
                error = 'invalid_data'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)
            domain += [('need_status','=', need_status)]

        if benefit_need_type:
            if not benefit_need_type in ['special', 'general']:
                error_descrip = _('Invalid value for %s ') % 'benefit_need_type'
                error = 'invalid_data'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

            domain += [('benefit_need_type','=', benefit_need_type)]
            if benefit_need_type == 'general':
                fields.append('benefit_ids')
            else:
                fields.append('benefit_id')

        result = request.env[model].sudo().search_read(domain, fields, offset=offset, limit=limit)
        return successful_response( 
            status = OUT_SUCCESS_CODE,
            dict_data = {
                'count': len(result),
                'results': result,
                }
        )

    # Get Select a group of Benefit List
    @http.route('/api/sys/select_benefit', methods=["GET"], type='http', auth='none')
    @check_permissions
    def get_selected_benefit(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_SY'})
        request.env.context = context
       
        benefit_type = kw.get('benefit_type', False)
        need_limit = kw.get('need_limit', False)
        age_limit = kw.get('age_limit', False)

        orphan_ids = kw.get('orphan_ids', [])
        fields = ['id', 'first_name', 'benefit_needs_value', 'benefit_needs_percent']
        
        params = False
        if orphan_ids:
            try:
                orphan_ids = literal_eval(orphan_ids)
            except Exception as e:
                error_descrip = _('Invalid orphan ids')
                error = 'invalid_data'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

            domain = [('id','in', orphan_ids), ('benefit_type','=', 'orphan')]
            result = request.env['grant.benefit'].sudo().search_read(domain, fields)
            return successful_response( 
                status = OUT_SUCCESS_CODE,
                dict_data = {
                    'count': len(result),
                    'results': result,
                    }
            )
        else:
            params = all([benefit_type, need_limit, age_limit])
        
        if not params:
            error_descrip = _('Some or all data is missing')
            error = 'missing_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        if not benefit_type in ['orphan', 'widow']:
            error_descrip = _('Invalid Orphan or Widow')
            error = 'invalid_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        try:
            age_limit = int(age_limit)
            need_limit = int(need_limit)
        except Exception as e:
            error_descrip = _('Invalid value for ages limit or needs limit')
            error = 'invalid_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        if age_limit <=0 or need_limit <=0:
            error_descrip = _('Invalid value for ages limit or needs limit')
            error = 'invalid_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        domain = [('benefit_type','=', benefit_type), ('benefit_needs_percent','>', need_limit), ('age','>', age_limit)]
        result = request.env['grant.benefit'].sudo().search_read(domain, fields)
        return successful_response( 
            status = OUT_SUCCESS_CODE,
            dict_data = {
                'count': len(result),
                'results': result,
                }
        )

    # Get anothor Sponsor
    @http.route('/api/sys/sponsor_search', methods=["GET"], type='http', auth='none')
    @check_permissions
    def get_anothor_sponsor(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_SY'})
        request.env.context = context

        mobile = kw.get('mobile', False)

        if not mobile:
            error_descrip = _('Missing mobile number')
            error = 'missing_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        if re.match(SAUDI_MOBILE_PATTERN, str(mobile)) == None:
                error_descrip = _('Enter a valid Saudi mobile number')
                error = 'invalid_mobile'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

        uid = request.session.uid
        user_data = self.get_user_sponsor_info(uid)
        sponsor_id = user_data["sponsor_id"]
        mobile1 = '966' + str(mobile).lstrip('0')
        mobile2 = '966' + str(sponsor_id.mobile).lstrip('0')
        if mobile1 == mobile2:
            error_descrip = _('Enter anothor sponsor mobile number')
            error = 'invalid_mobile'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        res = request.env['takaful.sponsor'].sudo().search([('mobile','=',mobile)], limit=1)
        if res:  
            return successful_response( 
                status = OUT_SUCCESS_CODE,
                dict_data = {
                    'id': res.id,
                    'name': res.name,
                    }
            )
        else:
            error_descrip = _('This sponsor does not exist')
            error = 'does_not_exist'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

    # Create a new Sponsorship
    @http.route('/api/sponsor/sponsorships/create', methods=['POST'], type='http', auth='none',  csrf=False)
    @check_permissions
    def do_create_sponsorship(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_SY'})
        request.env.context = context

        benefit_id = kw.get('benefit_id', False)
        benefit_type = kw.get('benefit_type', False)

        is_group = kw.get('is_group', 'no')
        benefit_ids = kw.get('benefit_ids', [])
        benefit_count = kw.get('benefit_count', False)

        is_gift = kw.get('is_gift', 'Unknown')
        with_orphan = kw.get('with_orphan', '')
        orphan_value = kw.get('orphan_value', False)
        months_number = kw.get('months_number', False)
        orphan_ids = kw.get('orphan_ids', [])
        benefits = []
        
        if orphan_ids:
            try:
                orphan_ids = literal_eval(orphan_ids)
            except Exception as e:
                error_descrip = _('Invalid orphan ids')
                error = 'invalid_data'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

        gifter_id = kw.get('gifter_id', False)
        gifter_name = kw.get('gifter_name', '')
        gifter_mobile = kw.get('gifter_mobile', False)
        gifter_message = kw.get('gifter_message', '')

        sponsorship_duration = kw.get('sponsorship_duration', False)
        month_amount = kw.get('month_amount', False)
        sponsorship_class = kw.get('sponsorship_class', False)
        payment_option = kw.get('payment_option', False)

        if is_group and is_group != 'no':
            if is_group != 'yes':
                error_descrip = _('invalid is_group value')
                error = 'invalid_group_value'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)
           
            keys = all([benefit_type, benefit_ids, payment_option, sponsorship_duration, month_amount])
        else:
            keys = all([is_gift, benefit_id, benefit_type, payment_option, sponsorship_duration, month_amount])

        if not keys:
            error_descrip = _('Some or all data is missing')
            error = 'missing_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)
        
        if not benefit_type in ['orphan', 'widow']:
            error_descrip = _('Invalid Orphan or Widow')
            error = 'invalid_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        if not sponsorship_duration in ['temporary', 'permanent']:
            error_descrip = _('Invalid Sponsorship Period')
            error = 'invalid_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        if not sponsorship_class in ['fully', 'partial']:
            error_descrip = _('Invalid Sponsorship Class')
            error = 'invalid_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        if not payment_option in ['once', 'month']:
            error_descrip = _('Invalid Payment Recurrence')
            error = 'invalid_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        try:
            month_amount = float(month_amount)
        except Exception as e:
            error_descrip = _('Invalid Month Amount')
            error = 'invalid_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        # Get the default amount for sponsorship
        default_sponsorship = self.get_default_sponsorship_amount()

        if month_amount <=0:
            error_descrip = _('Invalid Month Amount')
            error = 'invalid_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        end_date = None
        if sponsorship_duration == "temporary":
            if months_number:
                try:
                    months_number = int(months_number)
                except Exception as e:
                    error_descrip = _('Invalid Months Number')
                    error = 'invalid_data'
                    _logger.error(error_descrip)
                    return error_response(400, error, error_descrip)
            else:
                error_descrip = _('Missing Months Number')
                error = 'missing_data'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

            if months_number <=0:
                error_descrip = _('Invalid Months Number')
                error = 'invalid_data'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

            sudoConf = request.env['ir.config_parameter'].sudo()
            allowed_days = int(sudoConf.get_param('odex_takaful_base.allowed_pay_days'))
            start_date = get_first_day_of_next_month()
            end_date = start_date + relativedelta(months=months_number, days=(start_date.day + allowed_days))
        # For Group
        if is_group == 'yes':
            try:
                benefit_count = int(benefit_count)
            except Exception as e:
                error_descrip = _('Invalid Benefits count')
                error = 'invalid_data'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

            if benefit_count <= 1:
                error_descrip = _('Invalid Benefits Count')
                error = 'invalid_data'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

            try:
                benefit_ids = literal_eval(benefit_ids)
            except Exception as e:
                error_descrip = _('Invalid Benefits ids')
                error = 'invalid_data'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

            benefits = request.env['grant.benefit'].sudo().search([('id','in', benefit_ids)])
            if not benefits:
                error_descrip = _('No Benefits found for ids')
                error = 'does_not_exist'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

            if len(benefits) != benefit_count:
                error_descrip = _('Invalid Benefits, mismatch in count')
                error = 'invalid_data'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

            # rec_sum = sum(benefits.filtered(lambda x: x).mapped('id'))
            if sponsorship_class == "fully":
                total_sponsorship = sum(benefits.mapped('benefit_needs_value'))
            else:
                total_sponsorship = default_sponsorship * benefit_count
            
            if month_amount < total_sponsorship:
                error_descrip = _('Invalid Month Amount, At least %s') % total_sponsorship 
                error = 'invalid_data'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

            # Get Sponsor Info...
            uid = request.session.uid
            user_data = self.get_user_sponsor_info(uid)
            sponsor_id = user_data["sponsor_id"]

            # Create a group Sponsorship
            group_sponsorship = request.env['takaful.sponsorship'].sudo().create({
                'name': "New",
                'sponsorship_type': "group",
                'sponsor_id': sponsor_id.id,
                'benefit_type': benefit_type,
                'sponsorship_duration': sponsorship_duration,
                'sponsorship_class': sponsorship_class,
                'payment_option': payment_option,
                'contribution_value': month_amount,
                'end_date': end_date,
            })
            # Add a group of benefits
            min_max = []
            for ben in benefits:
                min_max.append(float(ben.benefit_needs_percent))
                group_sponsorship.sudo().write({'benefit_ids': [(4, ben.id)]})

            group_sponsorship.sudo().write({
                'min_needs_percent': min(min_max),
                'max_needs_percent': max(min_max),
            })
            
            # Return OK
            return successful_response( 
                OUT_SUCCESS_CODE,
                {},
            )

        if month_amount < default_sponsorship:
            error_descrip = _('Invalid Month Amount, At least %s') % default_sponsorship 
            error = 'invalid_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        # For Person
        if not is_gift in ['yes', 'no']:
            error_descrip = _('Gift value is invalid or missing')
            error = 'invalid_gift_value'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)
            
        try:
            benefit_id = int(benefit_id)
        except Exception as e:
            error_descrip = _('Invalid or Missing Id for Benefit')
            error = 'invalid_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        benefit = request.env['grant.benefit'].sudo().search([('id','=', benefit_id)], limit=1)
        if not benefit:
            error_descrip = _('This Benefit does not exist')
            error = 'does_not_exist'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        if is_gift == 'yes':
            if sponsorship_duration == "temporary": 
                if months_number < 12:
                    error_descrip = _('At Least 12 Months for Gift')
                    error = 'invalid_data'
                    _logger.error(error_descrip)
                    return error_response(400, error, error_descrip)

            if gifter_id:
                try:
                    gifter_id = int(gifter_id)
                except Exception as e:
                    error_descrip = _('Invalid Id for Gifter')
                    error = 'invalid_gifter_id'
                    _logger.error(error_descrip)
                    return error_response(400, error, error_descrip)

                gifter = request.env['takaful.sponsor'].sudo().search([('id', '=', gifter_id)], limit=1)
                
                if not gifter:
                    error_descrip = _('Gifter does not exist for this Id')
                    error = 'does_not_exist'
                    _logger.error(error_descrip)
                    return error_response(400, error, error_descrip)

                gifter_name = gifter.name
                gifter_mobile = gifter.mobile
                gifter_id = gifter.id
            
            if not gifter_name:
                error_descrip = _('Missing Gifter Name')
                error = 'missing_data'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

            if not gifter_mobile:
                error_descrip = _('Missing Gifter Mobile Number')
                error = 'missing_data'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

            if not gifter_id and (gifter_name and gifter_mobile):
                gifter_id = False
                if re.match(SAUDI_MOBILE_PATTERN, str(gifter_mobile)) == None:
                    error_descrip = _('Enter a valid Saudi mobile number')
                    error = 'invalid_mobile'
                    _logger.error(error_descrip)
                    return error_response(400, error, error_descrip)

        if benefit_type == 'widow':
            if not with_orphan in ['yes', 'no']:
                error_descrip = _('Including Orphans value is invalid or missing')
                error = 'invalid_with_orphan'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

            if with_orphan == 'yes' and orphan_value:
                try:
                    orphan_value = float(orphan_value)
                except Exception as e:
                    error_descrip = _('Invalid orphan value')
                    error = 'invalid_data'
                    _logger.error(error_descrip)
                    return error_response(400, error, error_descrip)

                if orphan_value <= 0:
                    error_descrip = _('Invalid orphan value')
                    error = 'invalid_data'
                    _logger.error(error_descrip)
                    return error_response(400, error, error_descrip)

                if sponsorship_class == "fully":
                    default_sponsorship = max(benefits.mapped('benefit_needs_value'))

                if orphan_value < default_sponsorship:
                    error_descrip = _('Invalid orphan value, At least %s') % default_sponsorship 
                    error = 'invalid_data'
                    _logger.error(error_descrip)
                    return error_response(400, error, error_descrip)

            elif with_orphan == 'yes' and not orphan_value:
                error_descrip = _('Missing orphan value')
                error = 'missing_data'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

            benefits = request.env['grant.benefit'].sudo().search([('id','in', orphan_ids)])
            if with_orphan == 'yes' and not benefits:
                error_descrip = _('Invalid or missing orphan ids')
                error = 'invalid_orphan_ids'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

        # Get Sponsor Info...
        uid = request.session.uid
        user_data = self.get_user_sponsor_info(uid)
        sponsor_id = user_data["sponsor_id"]

        # Create Sponsorships
        if is_gift == 'yes':
            main_sponsorship = request.env['takaful.sponsorship'].sudo().create({
                'name': "New",
                'sponsorship_type': "person", #group 
                'sponsor_id': sponsor_id.id,
                'benefit_id': benefit.id,
                'benefit_type': benefit_type,
                'sponsorship_duration': sponsorship_duration,
                'sponsorship_class': sponsorship_class,
                'payment_option': payment_option,
                'contribution_value': month_amount,
                'gifter_id': gifter_id,
                'gifter_name': gifter_name,
                'gifter_mobile': gifter_mobile,
                'gifter_message': gifter_message,
                'end_date': end_date,
                'is_gift': is_gift,
            })
        else:
            main_sponsorship = request.env['takaful.sponsorship'].sudo().create({
                'name': "New",
                'sponsorship_type': "person", #group 
                'sponsor_id': sponsor_id.id,
                'benefit_id': benefit.id,
                'benefit_type': benefit_type,
                'sponsorship_duration': sponsorship_duration,
                'sponsorship_class': sponsorship_class,
                'payment_option': payment_option,
                'contribution_value': month_amount,
                'end_date': end_date,
                'is_gift': is_gift,
            })

        if with_orphan == 'yes' and is_gift == 'yes' and benefits:
            for ben in benefits:
                orphan_sponsorship = request.env['takaful.sponsorship'].sudo().create({
                    'name': "New",
                    'sponsorship_type': "person", #group 
                    'sponsor_id': sponsor_id.id,
                    'benefit_id': ben.id,
                    'benefit_type': 'orphan',
                    'sponsorship_duration': sponsorship_duration,
                    'sponsorship_class': sponsorship_class,
                    'payment_option': payment_option,
                    'contribution_value': orphan_value,
                    'gifter_id': gifter_id,
                    'gifter_name': gifter_name,
                    'gifter_mobile': gifter_mobile,
                    'gifter_message': gifter_message,
                    'end_date': end_date,
                    'is_gift': is_gift,
                })
                main_sponsorship.sudo().write({'with_orphan_ids': [(4, ben.id)]})
            main_sponsorship.sudo().write({'is_widow_orphan': True})

        elif with_orphan == 'yes' and benefits:
            for ben in benefits:
                orphan_sponsorship = request.env['takaful.sponsorship'].sudo().create({
                    'name': "New",
                    'sponsorship_type': "person", #group 
                    'sponsor_id': sponsor_id.id,
                    'benefit_id': ben.id,
                    'benefit_type': 'orphan',
                    'sponsorship_duration': sponsorship_duration,
                    'sponsorship_class': sponsorship_class,
                    'payment_option': payment_option,
                    'contribution_value': orphan_value,
                    'end_date': end_date,
                    'is_gift': is_gift,
                })
                main_sponsorship.sudo().write({'with_orphan_ids': [(4, ben.id)]})
            main_sponsorship.sudo().write({'is_widow_orphan': True})
        
        return successful_response( 
            OUT_SUCCESS_CODE,
            {},
        )


    # Create a New Financial Gift
    @http.route('/api/sponsor/contributions/save', methods=['POST'], type='http', auth='none',  csrf=False)
    @check_permissions
    def do_save_contribution(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_SY'})
        request.env.context = context

        benefit_id = kw.get('benefit_id', False)
        need_id = kw.get('need_id', False)
        benefit_type = kw.get('benefit_type', False)
        operation_type = kw.get('operation_type', 'gift')
        amount = kw.get('amount', False)
        message = kw.get('message', '')
        benefit_ids = []

        name = ''
        if operation_type and operation_type != 'gift':
            if is_group != 'contribution':
                error_descrip = _('Invalid value for %s ') % 'operation_type'
                error = 'invalid_data'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)
           
            keys = all([need_id, benefit_type, amount])
        else:
            keys = all([benefit_id, benefit_type, amount])

        if not keys:
            error_descrip = _('Some or all data is missing')
            error = 'missing_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        try:
            amount = float(amount)
        except Exception as e:
            error_descrip = _('Invalid value for %s ') % 'amount'
            error = 'invalid_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        if not benefit_type in ['orphan', 'widow' , 'general']:
                error_descrip = _('Invalid value for %s ') % 'benefit_type'
                error = 'invalid_data'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)
        
        if operation_type == 'gift':
            try:
                benefit_id = int(benefit_id)
            except Exception as e:
                error_descrip = _('Invalid value for %s ') % 'benefit_id'
                error = 'invalid_data'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

            benefit = request.env['grant.benefit'].sudo().search([('id','=', benefit_id), ('benefit_type','=', benefit_type)], limit=1)
            if not benefit:
                error_descrip = _('This Benefit does not exist')
                error = 'does_not_exist'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)
        else:
            try:
                need_id = int(need_id)
            except Exception as e:
                error_descrip = _('Invalid value for %s ') % 'need_id'
                error = 'invalid_data'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

            need_type = request.env['benefits.needs'].sudo().search([('need_id','=', need_id)], limit=1)
            if not need_type:
                error_descrip = _('This Need does not exist')
                error = 'does_not_exist'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)
            
            if benefit_id and need_type.benefit_id and need_type.benefit_id != benefit_id:
                error_descrip = _('Mismatch Need for Benefit')
                error = 'invalid_data'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

            # Get info
            if need_type.benefit_ids:
                benefit_ids = need_type.benefit_ids.ids

            elif need_type.benefit_id:
                benefit_id = need_type.benefit_id.id
            name = need_type.name

        # Get Sponsor Info...
        uid = request.session.uid
        user_data = self.get_user_sponsor_info(uid)
        sponsor_id = user_data["sponsor_id"]

        if operation_type == 'gift':
            name = u'إهداء مالي'
            contribution = request.env['takaful.contribution'].sudo().create({
                'name': name,
                'benefit_id': benefit_id,
                'sponsor_id': sponsor_id.id,
                'benefit_type': benefit_type,
                'operation_type': operation_type,
                'amount': amount,
                'note': message
            })
        else:
            contribution = request.env['takaful.contribution'].sudo().create({
                'name': name,
                'need_id': need_id,
                'sponsor_id': sponsor_id.id,
                'benefit_type': benefit_type,
                'operation_type': operation_type,
                'amount': amount,
                'note': message
            })

            if benefit_ids:
                for id_ in benefit_ids:
                    contribution.sudo().write({'benefit_ids': [(4, id_)]})
            else:
                contribution.sudo().write({'benefit_id': [(4, benefit_id)]})

        # Return OK
        return successful_response( 
            OUT_SUCCESS_CODE,
            {},
        )

    @http.route('/api/sponsorships/test', methods=['GET'], type='http', auth='none')
    @check_permissions
    def a_test(self, **kw):
        # get System env params
        cr, uid = request.cr, request.session.uid
        # get any model as ordinary System object
        system_model_obj = request.env(cr, uid)['res.partner']
        # make models manipulations, actions, computations etc. And if you need, fill the results dictionary
        your_custom_dict_data = {'your_vals': '...'}
        # send HTTP response
        return successful_response(status=200, dict_data=your_custom_dict_data)

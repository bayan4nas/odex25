# -*- coding: utf-8 -*-
import sys
import traceback
from .main import *

import logging
from ast import literal_eval

from odoo import _
from odoo import http
from odoo.http import request
from dateutil.parser import parse

from dateutil.relativedelta import relativedelta

_logger = logging.getLogger(__name__)

_NOT_FOUND_SRT = _("لايوجد")
_NOT_FOUND_INT = 0
_NOT_FOUND_LIST = []
_NOT_FOUND_FLOAT = 0.0
_NOT_FOUND_DATE = _("لايوجد")


class ControllerAppREST(http.Controller):
    # Fetch All the cities
    @http.route('/api/sys/city_list', methods=["GET"], type='http', auth='none')
    def get_city_list(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        # Set parmeters.
        model = 'res.country.city'
        fields = ['id', 'name']
        result = request.env[model].sudo().search_read([], fields)
        return successful_response(
            status=OUT_SUCCESS_CODE,
            dict_data={
                'count': len(result),
                'results': result or [],
            }
        )

    def get_default_sponsorship_amount(self):
        # Get from config
        sudoConf = request.env['ir.config_parameter'].sudo()
        min_kafala = float(sudoConf.get_param(
            'odex_takaful_base.min_kafala', 300))
        return min_kafala

    def get_user_sponsor_info(self, uid):
        user_id = request.env['res.users'].sudo().browse(uid)
        partner_id = user_id.partner_id
        sponsor_id = request.env['takaful.sponsor'].sudo().search(
            [('partner_id', '=', partner_id.id)], limit=1)

        return {
            "user_id": user_id,
            "sponsor_id": sponsor_id,
            "partner_id": partner_id,
        }

    def add_info_widow_sponsorships(self, result, benefit_type):
        info = []
        if benefit_type == 'orphan':
            for res in result:
                data = {}
                data = dict(res)
                data['benefit_id'] = self.get_sponsorship_benefit_info(
                    res['benefit_id'], benefit_type)
                info.append(data)

        else:
            # Set parmeters.
            uid = request.session.uid
            user_data = self.get_user_sponsor_info(uid)
            sponsor_id = user_data["sponsor_id"]

            for res in result:
                data = {}
                data = dict(res)
                sponsored_orphans = []
                benefits = []
                if res['with_orphan_ids']:
                    benefits = request.env['grant.benefit'].sudo().search(
                        [('id', 'in', res['with_orphan_ids'])],order='id desc')
                    for ben in benefits:
                        sponsored_orphans.append({
                            'id': ben.id,
                            'name': ben.name,
                             "benefit_available_need": float(format(ben.benefit_needs_value, '.2f')),
                            # 'contribution_value': ben.contribution_value,
                        })

                data['benefit_id'] = self.get_sponsorship_benefit_info(
                    res['benefit_id'], benefit_type)
                data['with_orphan_ids'] = sponsored_orphans or []
                data['with_orphans_count'] = len(sponsored_orphans)

                orphans_month_amount = sum(request.env['takaful.sponsorship'].sudo().search(
                    [('sponsor_id', '=', sponsor_id.id), ('benefit_id', 'in', res['with_orphan_ids'])]).mapped('contribution_value'))
                data['orphans_contribution_value'] = orphans_month_amount or 0
                data['contribution_value'] = res['contribution_value']
                info.append(data)

        return info

    def get_sponsorship_benefit_info(self, benefit_id, benefit_type, full=True):
        data = {}
        if not benefit_id or not benefit_type:
            return False

        benefit = request.env['grant.benefit'].sudo().search(
            [('id', '=', benefit_id)], limit=1)

        if not benefit:
            return False
       
        # if benefit.benefit_type != benefit_type:
        #     return False

        data['id'] = benefit.id

        if full:
            data['name'] = benefit.name or _NOT_FOUND_SRT
        else:
            data['first_name'] = benefit.first_name or _NOT_FOUND_SRT

        data['age'] = benefit.age or _NOT_FOUND_INT
        data['city_id'] = benefit.city_id.name or _NOT_FOUND_SRT
        data['number'] = benefit.housing_id.house_number or _NOT_FOUND_SRT
        data['benefit_type'] =  benefit.benefit_type or None
        data['has_needs'] = benefit.has_needs
        data['has_arrears'] = benefit.has_arrears

        if benefit_type == "widow":
            data['total_income'] = benefit.total_income or _NOT_FOUND_FLOAT
            if benefit.orphan_ids.ids:
                orphans = []
                for orphan in benefit.orphan_ids:
                    # type(orphan.read([])[0]['benefit_needs_value'])
                    orphans.append({
                        "id": orphan.id,
                        "first_name": orphan.first_name,
                        "benefit_available_need": float(format(orphan.benefit_needs_value, '.2f')),
                    })
                data['orphan_ids'] = orphans or _NOT_FOUND_LIST
            else:
                data['orphan_ids'] = _NOT_FOUND_LIST

            data['orphan_count'] = len(benefit.orphan_ids) or 0

            salary_resouces = []
            for source in benefit.salary_ids:
                if source.salary_type:
                    salary_resouces.append(source.salary_type)
            data['salary_resouces'] = salary_resouces or _NOT_FOUND_LIST

        if benefit_type == "orphan":
            data['gender'] =  benefit.gender or None
            data['orphan_status'] = dict(benefit.fields_get(allfields=['orphan_status'])[
                                         'orphan_status']['selection'])[benefit['orphan_status']] if benefit.orphan_status else _NOT_FOUND_SRT

            data['education_level'] = dict(benefit.fields_get(allfields=['education_level'])[
                                           'education_level']['selection'])[benefit['education_level']] if benefit.education_level else _NOT_FOUND_SRT
            data['class_room'] = benefit.classroom or _NOT_FOUND_SRT
            data['quran_parts'] = benefit.number_parts or _NOT_FOUND_INT

        data['responsible'] = dict(benefit.fields_get(allfields=['responsible'])[
                                   'responsible']['selection'])[benefit['responsible']] if benefit.responsible else _NOT_FOUND_SRT
        data['health_status'] = dict(benefit.fields_get(allfields=['health_status'])[
                                     'health_status']['selection'])[benefit['health_status']] if benefit.health_status else _NOT_FOUND_SRT

        data['housing_status'] = dict(benefit.housing_id.fields_get(allfields=['property_type'])['property_type']['selection'])[
            benefit.housing_id['property_type']] if benefit.housing_id.property_type else _NOT_FOUND_SRT
        data['education_status'] = dict(benefit.fields_get(allfields=['education_status'])[
                                        'education_status']['selection'])[benefit['education_status']] if benefit.education_status else _NOT_FOUND_SRT

        skills = []
        for skill in benefit.craft_skill_ids:
            if skill.name:
                skills.append(skill.name)

        for skill in benefit.training_inclinations_ids:
            if skill.name:
                skills.append(skill.name)

        data['skills'] = skills or _NOT_FOUND_LIST

        try:
            data['benefit_total_need'] = float(
                format(benefit.total_expenses, '.2f'))

            data['benefit_available_need'] = float(
                format(benefit.benefit_needs_value, '.2f'))
            data['benefit_needs_percent'] = float(
                format(benefit.benefit_needs_percent, '.2f'))
            data['benefit_arrears_value'] = float(
                format(benefit.benefit_arrears_value, '.2f'))
        except Exception as e:
            data['benefit_total_need'] = 0

        # Needs of benefit
        domain = [
            '&',
            ('benefit_id', '=', benefit.id),
            ('remaining_amount', '>', 0),
            ('state', '=', 'published'),
        ]

        needs_list = request.env['benefits.needs'].sudo().search(domain,order='id desc')
        needs = []
        for need in needs_list:
            if need.name:
                needs.append(need.name)
        data['needs'] = needs or _NOT_FOUND_LIST

        return data

    @http.route('/api/sponsor/registeration', methods=["POST"], type='http', auth='none', csrf=False)
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

        if not user_type_kw in ['person', 'company', 'charity']:
            error_descrip = _('User type value is invalid or missing')
            error = 'invalid_user_type'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        if user_type_kw == 'person':
            keys = all([first_name, second_name, middle_name, family_name, gender_kw,
                       id_number, mobile_kw, email_kw, city_kw, activation_mode_kw])
        else:
            keys = all([name, id_number, mobile_kw, email_kw,
                       city_kw, activation_mode_kw])

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
        city = request.env['res.country.city'].sudo().search(
            [('id', '=', city_kw)])
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

        res = request.env['res.partner'].sudo().search(
            [('id_number', '=', id_number)])
        if res and len(res) >= 1:
            error_descrip = _('This Id Number is already exist')
            error = 'already_exist'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        res = request.env['res.partner'].sudo().search(
            [('mobile', '=', mobile_kw)])
        if res and len(res) >= 1:
            error_descrip = _('This mobile number is already exist')
            error = 'already_exist'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        res = request.env['res.users'].sudo().search(
            [('login', '=', email_kw)])
        if res and len(res) >= 1:
            error_descrip = _('This email is already exist')
            error = 'already_exist'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        # Create Sponser from here, and complete its record later.
        if user_type_kw == 'person':
            full_name = first_name + " " + second_name + \
                " " + middle_name + " " + family_name

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

        # Get the user
        user = sponsor.user_id
        # Remove any defualt groups
        user.sudo().remove_access_groups()
        user.sudo().write({
            'groups_id': [(4, request.env.ref('base.group_portal', False).id)],
        })
        user.sudo().write({
            'groups_id': [(3, request.env.ref('base.group_user', False).id)],
        })
        # Assign access groups according to account_type
        user.sudo().write({
            'groups_id': [(4, request.env.ref('odex_takaful.takaful_group_user_sponsor', False).id)],
        })

        if activation_mode_kw == 'email':
            # With Email Verification
            result = user.sudo().reset_password_using_email()
            if result['code'] == 200:
                return successful_response(
                    status=OUT_SUCCESS_CODE,
                    dict_data=result['results'] or []
                )
            else:
                code = result['code']
                error_descrip = result['error_descrip']
                error = result['error']
                _logger.error(error_descrip)
                return error_response(code, error, error_descrip)
        else:
            # With SMS Verification
            result = user.sudo().request_otp(mobile_kw)
            if result['code'] == 200:
                return successful_response(
                    status=OUT_SUCCESS_CODE,
                    dict_data=result['results'] or []
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

        sponsorship_value = {
            'sponsorship_value': self.get_default_sponsorship_amount()}
        # send HTTP response
        return successful_response(
            status=OUT_SUCCESS_CODE,
            dict_data=sponsorship_value,
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
            limit = None

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

        result = request.env[model].sudo().search(
            domain, offset=offset, limit=limit,order='id desc')
        if result:
            result = props_fields(result, fields)
            count = len(result)
        else:
            result = None
            count = 0

        next_page = None if count < PAGE_SIZE else (int(page) + 1)
        return successful_response(
            status=OUT_SUCCESS_CODE,
            dict_data={
                'count': count,
                'results': result or [],
                'next_page': next_page,
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

        res = request.env[model].sudo().search(domain, limit=1,order='id desc')
        if res:
            dict_data = props_fields(res, ['id',
                                           'title',
                                           'body',
                                           'sent_on'
                                           ]
                                     )
            return successful_response(status=OUT_SUCCESS_CODE, dict_data=dict_data[0])
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

        res = request.env[model].sudo().search(domain, limit=1,order='id desc')
        if res:
            try:
                res.unlink()
                return successful_response(
                    status=OUT_SUCCESS_CODE,
                    dict_data={}
                )
            except Exception as e:
                error_descrip = _('Cannot delete this notification')
                error = 'failed_operation'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

        else:
            error_descrip = _('No notification is found')
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
                    'id': sponsor_id.id or _NOT_FOUND_INT,
                    'name': sponsor_id.name or _NOT_FOUND_SRT,
                    'id_number': sponsor_id.id_number or _NOT_FOUND_SRT,
                    'company_type': sponsor_id.company_type or _NOT_FOUND_SRT,
                    'email': sponsor_id.email or _NOT_FOUND_SRT,
                    'mobile': sponsor_id.mobile or _NOT_FOUND_SRT,
                    'city_id': sponsor_id.city_id.id or _NOT_FOUND_SRT,
                    'city_name': sponsor_id.city_id.name or _NOT_FOUND_SRT,
                    # Bank info
                    'account_number': sponsor_id.account_number or _NOT_FOUND_SRT,
                    'iban': sponsor_id.iban or _NOT_FOUND_SRT,
                    'bank_id': sponsor_id.bank_id.id or _NOT_FOUND_SRT,
                    'bank_name': sponsor_id.bank_id.name or _NOT_FOUND_SRT,
                    'bank_entity_name': sponsor_id.bank_entity_name or _NOT_FOUND_SRT,
                    'image': sponsor_id.image or _NOT_FOUND_SRT
                }
            else:
                dict_data = {
                    'id': sponsor_id.id or _NOT_FOUND_INT,
                    'name': sponsor_id.name or _NOT_FOUND_SRT,
                    'first_name': sponsor_id.first_name or _NOT_FOUND_SRT,
                    'second_name': sponsor_id.second_name or _NOT_FOUND_SRT,
                    'middle_name': sponsor_id.middle_name or _NOT_FOUND_SRT,
                    'family_name': sponsor_id.family_name or _NOT_FOUND_SRT,
                    'gender': dict(sponsor_id.fields_get(allfields=['gender'])['gender']['selection'])[sponsor_id.gender] if sponsor_id.gender else _NOT_FOUND_SRT,
                    'id_number': sponsor_id.id_number or _NOT_FOUND_SRT,
                    'company_type': sponsor_id.company_type or _NOT_FOUND_SRT,
                    'email': sponsor_id.email or _NOT_FOUND_SRT,
                    'mobile': sponsor_id.mobile or _NOT_FOUND_SRT,
                    'city_id': sponsor_id.city_id.id or _NOT_FOUND_INT,
                    'city_name': sponsor_id.city_id.name or _NOT_FOUND_SRT,
                    # Bank info
                    'account_number': sponsor_id.account_number or _NOT_FOUND_SRT,
                    'iban': sponsor_id.iban or _NOT_FOUND_SRT,
                    'bank_id': sponsor_id.bank_id.id or _NOT_FOUND_INT,
                    'bank_name': sponsor_id.bank_id.name or _NOT_FOUND_SRT,
                    'bank_entity_name': sponsor_id.bank_entity_name or _NOT_FOUND_SRT,
                    'image': sponsor_id.image or _NOT_FOUND_SRT
                }
            return successful_response(
                status=OUT_SUCCESS_CODE,
                dict_data=dict_data
            )
        else:
            error_descrip = _('No sponsor is found')
            error = 'does_not_exist'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

    # Update Record for Sponsor
    @http.route('/api/sponsor/profile/update', methods=['POST'], type='http', auth='none', csrf=False)
    @check_permissions
    def do_update_sponsor_profile(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context
        files = request.httprequest.files.getlist('image')
        updated_fields = [
            'mobile',
            'city_id',
            # Bank info
            'account_number',
            'iban',
            'bank_id',
            'bank_entity_name',
            'image'
        ]
        values = {}
        for field_name, field_value in kw.items():
            if not field_name in updated_fields:
                error_descrip = _('Cannot update this field: %s ') % field_name
                error = 'invalid_data'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

            if field_value == "true" or field_value == "True":
                values[field_name] = True
            elif field_value == "false" or field_value == "False":
                values[field_name] = False
            else:
                values[field_name] = field_value
        if files:
            attachment = files[0].read()
            data = base64.b64encode(attachment)
            values['image'] = data

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
                res = props_fields(sponsor_id, updated_fields)
                return successful_response(
                    OUT_SUCCESS_CODE,
                    res,

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
        fields = ['notify_by_app',
                  'notify_by_sms',
                  'notify_month_day',
                  'notify_pay_by_app',
                  'notify_pay_by_sms']

        if sponsor_id:
            res = props_fields(sponsor_id, fields=fields)
            return successful_response(
                status=OUT_SUCCESS_CODE, dict_data=res
            )
        else:
            error_descrip = _('No sponsor is found')
            error = 'does_not_exist'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

    # Update notify settings for Sponsor
    @http.route('/api/sponsor/notify_setting/update', methods=['POST'], type='http', auth='none', csrf=False)
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

            if field_value == "true" or field_value == "True":
                values[field_name] = True
            elif field_value == "false" or field_value == "False":
                values[field_name] = False
            else:
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
                    props_fields(sponsor_id, updated_fields)
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
        fields = {
            'name_in_certificate',
            'name_in_certificate',
            'type_in_certificate',
            'duration_in_certificate',
        }

        if sponsor_id:
            dict_data = props_fields(sponsor_id, fields=fields)
            return successful_response(
                status=OUT_SUCCESS_CODE,
                dict_data=dict_data
            )
        else:
            error_descrip = _('No sponsor is found')
            error = 'does_not_exist'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

    # Update certificate settings for Sponsor
    @http.route('/api/sponsor/certificate_setting/update', methods=['POST'], type='http', auth='none', csrf=False)
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

            if field_value == "true" or field_value == "True":
                values[field_name] = True
            elif field_value == "false" or field_value == "False":
                values[field_name] = False
            else:
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
                    props_fields(sponsor_id, updated_fields)
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
                    'value': True,
                    'title': _('Has Needs'),
                    'state': False,
                },
                # For Field of: has_arrears
                {
                    'name': 'has_arrears',
                    'value': True,
                    'title': _('Has Delay Payments'),
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
                    'title': _('Has Delay Payments'),
                    'state': False,
                },

            ]

        # Return Benefitfilters
        return successful_response(
            status=OUT_SUCCESS_CODE,
            dict_data=filters
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
            limit = None

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

        domain = [['benefit_type', '=', benefit_type]]
        # Get filters if any
        filters = kw.get('filters', [])
        try:
            filters = json.loads(filters)
            filters = map_filters(filters)
        except Exception as e:
            pass
        if filters:
            domain += filters

        # Get from config
        sudoConf = request.env['ir.config_parameter'].sudo()
        new_kafala = sudoConf.get_param('odex_takaful_base.new_kafala')

        # Set parmeters.
        model = 'grant.benefit'
        if new_kafala == "always":
            full = True
        else:
            full = False

        benefits = request.env[model].sudo().search(
            domain, offset=offset, limit=limit,order='id desc')
        result = []
        
        for ben in benefits:
            res = self.get_sponsorship_benefit_info(
                str(ben.id), benefit_type, full=full)
            if res:
                result.append(res)

        if result:
            count = len(result)

        else:
            result = None
            count = 0

        next_page = None if count < PAGE_SIZE else (int(page) + 1)
        return successful_response(
            status=OUT_SUCCESS_CODE,
            dict_data={
                'count': count,
                'results': result or [],
                'next_page': next_page,
            }
        )

        # Get User Sponsorships

    @http.route('/api/sponsor/sponsorships/<sponsorships_id>', methods=["GET"], type='http', auth='none')
    @check_permissions
    def user_get_sponsorships_byId(self, sponsorships_id, **kw):
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context
        if not sponsorships_id:
            error_descrip = _('Invalid Sponsorships Id')
            error = 'invalid_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        model = "takaful.sponsorship"
        domain = [('id', '=', sponsorships_id)]
        result = request.env[model].sudo().search(domain,order='id desc')
        benefit_type = result.benefit_type
        # Set parmeters.
        if not result:
            error_descrip = _('Invalid Sponsorships Id , NOT FOUND')
            error = 'invalid_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        fields = [
            'id',
            'state',
            'start_date',
            'next_due_date',
            'benefit_type',
            'close_to_be_canceled_date',
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
            'is_widow_orphan',
            'with_orphan_ids',
        ]
        # val = dict(result.fields_get(allfields=['benefit_type'])[
        #            'benefit_type']['selection'], context=context)[result.benefit_type]

        if benefit_type == 'widow':
            fields += [
                'is_widow_orphan',
                'with_orphan_ids',
            ]

        result = props_fields(result, fields)
        # result[0]['benefit_type'] =result.benefit_type
        if result:
            # if benefit_type == 'widow':
            result = self.add_info_widow_sponsorships(result, benefit_type)
            count = len(result)
        else:
            result = None
            count = 0
        return successful_response(
            status=OUT_SUCCESS_CODE,
            dict_data={
                'count': count,
                'results': result,
            }
        )

    # Get User Sponsorships
    @http.route('/api/home', methods=['GET'], type='http', auth='none')
    @check_permissions
    def api_home(self, **kw):
        uid = request.session.uid
        user_data = self.get_user_sponsor_info(uid)
        sponsor_id = user_data["sponsor_id"]
        domain = ('sponsor_id', '=', sponsor_id.id)
        model = "takaful.sponsorship"
        # result2 = request.env[model].sudo().read_group(
        #         domain, ['benefit_type'], ['benefit_type'])
        # make models manipulations, actions, computations etc. And if you need, fill the results dictionary
        your_custom_dict_data = {
                "my_orphan_sponsorships": request.env[model].sudo().search_count([domain,('benefit_type','=','orphan')]) or 0,
                "available_orphans": request.env['grant.benefit'].sudo().search_count([('benefit_type','=','orphan')]) or 0,
                "my_widow_sponsorships": request.env[model].sudo().search_count([domain,('benefit_type','=','widow')]) or 0,
                "available_widows": request.env['grant.benefit'].sudo().search_count([('benefit_type','=','widow')]) or 0,
                "collective_needs": request.env['benefits.needs'].sudo().search_count([]),
                }
        # send HTTP response
        return successful_response(status=200, dict_data=your_custom_dict_data)
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
            limit = None

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
            'close_to_be_canceled_date',
            'expected_cancel_date',
            'end_date',
            'month_count',
            'paid_month_count',
            'contribution_value',
            'sponsorship_class',
            'sponsorship_duration',
            # 'benefit_ids',
            'benefit_id',
            'has_delay',
            'has_needs',
        ]

        if benefit_type == 'widow':
            fields += [
                'is_widow_orphan',
                'with_orphan_ids',
            ]

        # Get filters if any
        filters = kw.get('filters', [])
        try:
            filters = json.loads(filters)
            filters = map_filters(filters)
        except Exception as e:
            pass

        # ['state', '!=', 'draft'],
        domain = [['sponsor_id', '=', sponsor_id.id], [
            'sponsorship_type', '=', 'person'], ['benefit_type', '=', benefit_type]]

        if filters:
            domain += filters
        else:
            if benefit_type == 'orphan':
                filters = [
                    ['gender', 'in', ['male', 'female']],
                    ['state', 'in', ['confirmed', 'wait_pay',
                                     'progress', 'to_cancel', 'canceled', 'closed']],
                ]
                domain += filters
            elif benefit_type == 'widow':
                filters = [
                    ['state', 'in', ['confirmed', 'wait_pay',
                                     'progress', 'to_cancel', 'canceled', 'closed']],
                ]
                domain += filters

        result = request.env[model].sudo().search(
            domain, offset=offset, limit=limit,order='id desc')
        result = props_fields(result, fields)
        if result:
            # if benefit_type == 'widow':
            result = self.add_info_widow_sponsorships(result, benefit_type)
            count = len(result)
        else:
            result = None
            count = 0

        next_page = None if count < PAGE_SIZE else (int(page) + 1)
        return successful_response(
            status=OUT_SUCCESS_CODE,
            dict_data={
                'id': sponsor_id.id,
                'name': sponsor_id.name,
                'count': count,
                'results': result,
                'next_page': next_page,
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
            status=OUT_SUCCESS_CODE,
            dict_data=record
        )

    # Get Cancel Reasons List
    @http.route('/api/sys/reason_list', methods=["GET"], type='http', auth='none')
    @check_permissions
    def get_reason_list(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        # Set parmeters.
        model = 'sponsorship.reason.stop'
        fields = ['id', 'name']
        result = request.env[model].sudo().search([],order='id desc')
        result = props_fields(result, fields)
        return successful_response(
            status=OUT_SUCCESS_CODE,
            dict_data={
                'count': len(result),
                'results': result or [],
            }
        )

    # Create Cancel Record for Sponsorship: Do Cancel for Sponsorship
    @http.route('/api/sponsor/sponsorships/cancel', methods=['POST'], type='http', auth='none', csrf=False)
    @check_permissions
    def do_cancel_sponsorship(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
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

        reason = request.env['sponsorship.reason.stop'].sudo().search(
            [('id', '=', reason_id)], limit=1)
        if not reason:
            error_descrip = _('This Reason does not exist in the system')
            error = 'does_not_exist'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        uid = request.session.uid
        user_data = self.get_user_sponsor_info(uid)
        sponsor_id = user_data["sponsor_id"]

        sponsorship = request.env['takaful.sponsorship'].sudo().search(
            [('id', '=', sponsorship_id), ('sponsor_id', '=', sponsor_id.id)], limit=1)
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

        cancel_reason_id = request.env['sponsorship.cancellation'].sudo().search(
            [('sponsorship_id', '=', sponsorship.id)], limit=1)
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
        context.update({'lang': u'ar_001'})
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
                # For Field of: has_delay
                {
                    'name': 'has_delay',
                    'value': 'true',
                    'title': _('Has Delay Payments'),
                    'state': False,
                },
                # For Field of: state (Sponsorship Status)
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
                # For Field of: has_delay
                {
                    'name': 'has_delay',
                    'value': 'true',
                    'title': _('Has Delay Payments'),
                    'state': False,
                },
                # For Field of: state (Sponsorship Status)
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
            status=OUT_SUCCESS_CODE,
            dict_data=filters
        )

    # Get Need Filters
    @http.route('/api/sys/need_filters', methods=['GET'], type='http', auth='none')
    @check_permissions
    def get_need_filters(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        model = 'benefits.needs'
        groupby = 'benefit_type'
        # result = request.env[model].sudo().read_group([],['need_category'],groupby=groupby)
        filters = [
            # For Field of: benefit_type (Benefit Type)
            {
                'name': 'benefit_type',
                'value': 'orphans',
                'title': _('Orphans'),
                'state': False,
            },
            {
                'name': 'benefit_type',
                'value': 'widows',
                'title': _('Widows'),
                'state': False,
            },
            {
                'name': 'benefit_type',
                'value': 'both',
                'title': _('All'),
                'state': False,
            },
        ]

        for f in filters:
            need = []
            ids = request.env[model].sudo().search(
                [('benefit_type', '=', f['value'])]).mapped('need_category').ids
            result = request.env['needs.categories'].sudo().search_read(
                [('id', 'in', ids)], ['id', 'name'],order='id desc')
            f['need_category_list'] = result
        return successful_response(
            status=OUT_SUCCESS_CODE,
            dict_data=filters
        )

    # Get all need categories list
    @http.route('/api/sys/need_category_list', methods=["GET"], type='http', auth='none')
    def get_need_category_list(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_SY'})
        request.env.context = context

        # Set parmeters.
        model = 'needs.categories'
        fields = ['id', 'name']
        result = request.env[model].sudo().search([],order='id desc')
        result = props_fields(result, fields)
        return successful_response(
            status=OUT_SUCCESS_CODE,
            dict_data={
                'count': len(result),
                'results': result or [],
            }
        )

    # Get Need Types for general needs
    @http.route('/api/sys/need_types/page/<page>', methods=["GET"], type='http', auth='none')
    @check_permissions
    def get_need_types(self, page, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_SY'})
        request.env.context = context
        need_category_list = kw.get('need_category_list', False)

        if page:
            try:
                offset = (int(page) * PAGE_SIZE) - PAGE_SIZE
                limit = PAGE_SIZE
            except Exception as e:
                return error_response_404_url_not_found()
        else:
            offset = 0
            limit = None

        model = 'benefits.needs'
        fields = [
            'id',
            'name',
            'need_status',
            'benefit_count',
            # 'need_category',
            'category_name',
            # 'state_id',
            'city_name',
            'target_amount',
            'paid_amount',
            'remaining_amount',
            'completion_ratio',
        ]
        domain = [
            '&',
            ['remaining_amount', '>', 0],
            ['state', '=', 'published'],
            # ['benefit_need_type','=', 'general'],
        ]
        try:
            need_category_list = json.loads(need_category_list)
            if need_category_list:
                domain.append(['need_category', 'in', need_category_list])
        except Exception as e:
            pass

        # Get filters if any
        benefit_type = kw.get('benefit_type')
        if benefit_type:
            domain.append(['benefit_type', '=', benefit_type])
        try:
            result = request.env[model].sudo().search(
                domain, offset=offset, limit=limit,order='id desc')
            result = props_fields(result, fields)
        except Exception as e:
            result = []

        count = len(result)
        next_page = None if count < PAGE_SIZE else (int(page) + 1)
        return successful_response(
            status=OUT_SUCCESS_CODE,
            dict_data={
                'count': count,
                'results': result or [],
                'next_page': next_page,
            }
        )

    # Get Need type for one benefit: Based on Need Categoey Id
    @http.route('/api/sys/benefit/need_types', methods=["GET"], type='http', auth='none')
    @check_permissions
    def get_benefit_need_types(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_SY'})
        request.env.context = context

        need_category_id = kw.get('need_category_id', False)
        need_status = kw.get('need_status', False)
        benefit_id = kw.get('benefit_id', False)

        if not all([need_category_id, benefit_id]):
            error_descrip = _('Some or all data is missing')
            error = 'missing_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        try:
            need_category_id = int(need_category_id)
        except Exception as e:
            error_descrip = _('Invalid value for %s ') % 'need_category_id'
            error = 'invalid_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        try:
            benefit_id = int(benefit_id)
        except Exception as e:
            error_descrip = _('Invalid value for %s ') % 'benefit_id'
            error = 'invalid_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        model = 'benefits.needs'
        fields = [
            'id',
            'name',
            'category_name',
            'target_amount',
            'paid_amount',
            'remaining_amount',
            'completion_ratio',
            'need_status'
        ]
        domain = [
            '&',
            ('remaining_amount', '>', 0),
            ('state', '=', 'published'),
            ('need_category', '=', need_category_id),
            ('benefit_id', '=', benefit_id),

            ('benefit_need_type', '=', 'special'),
        ]

        if not need_status in ['urgent', 'not_urgent']:
            domain.append(('need_status', 'in', ['urgent', 'not_urgent']),)
        elif need_status in ['urgent', 'not_urgent']:
            domain.append(('need_status', 'in', [need_status]),)
        else:
            error_descrip = _('Invalid value for %s ') % 'need_status'
            error = 'invalid_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        result = request.env[model].sudo().search(domain,order='id desc')
        result = props_fields(result, fields)
        return successful_response(
            status=OUT_SUCCESS_CODE,
            dict_data={
                'count': len(result),
                'results': result or [],
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

        orphan_ids = kw.get('orphan_ids', [])
        benefit_type = kw.get('benefit_type', [])

        fields = ['id', 'first_name',
                  'benefit_needs_value', 'benefit_needs_percent', 'benefit_type']
        domain = []
        if orphan_ids:
            try:
                orphan_ids = literal_eval(orphan_ids)
            except Exception as e:
                error_descrip = _('Invalid orphan ids')
                error = 'invalid_data'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)
            domain.append(('id', 'in', orphan_ids))
        if benefit_type:
            domain.append(('benefit_type', '=', benefit_type))
        result = request.env['grant.benefit'].sudo().search(domain,order='id desc')
        result = props_fields(result, fields)
        return successful_response(
            status=OUT_SUCCESS_CODE,
            dict_data={
                'count': len(result),
                'results': result or [],
            }
        )
        # else:
        #     error_descrip = _('Some or all data is missing')
        #     error = 'missing_data'
        #     _logger.error(error_descrip)
        #     return error_response(400, error, error_descrip)

    # Get Filters for sponsor payments
    @http.route('/api/sys/payment_filters', methods=['GET'], type='http', auth='none')
    @check_permissions
    def get_sponsor_payments_filters(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_SY'})
        request.env.context = context

        filters = [
            {
                'name': 'benefit_type',
                'value': 'orphan',
                'title': _('Orphans'),
                'state': False,
            },
            {
                'name': 'benefit_type',
                'value': 'widow',
                'title': _('Widows'),
                'state': False,
            },
            {
                'name': 'operation_type',
                'value': 'contribution',
                'title': _('Contributions'),
                'state': False,
            },
        ]

        # Return financial filters
        return successful_response(
            status=OUT_SUCCESS_CODE,
            dict_data=filters
        )

    #  Get sponsor financial records
    @http.route('/api/sponsor/payments/page/<page>', methods=["GET"], type='http', auth='none')
    @check_permissions
    def get_sponsor_payments_records(self, page, **kw):
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
            limit = None

        uid = request.session.uid
        user_data = self.get_user_sponsor_info(uid)
        sponsor_id = user_data["sponsor_id"]

        domain = [
            ['sponsor_id', '=', sponsor_id.id],
        ]

        # Get filters if any
        filters = kw.get('filters', [])
        try:
            filters = json.loads(filters)
            filters = map_filters(filters)
        except Exception as e:
            pass

        if filters:
            domain += filters

        # Set parmeters.
        model = "takaful.sponsor.operation"
        fields = [
            'id',
            'name',
            'title',
            'date',
            'month',
            'amount',
        ]
        result2 = []
        data = []
        try:
            result2 = request.env[model].sudo().read_group(
                domain, fields, ['date:month'])
            for res in result2:
                domain2 = []
                domain2 = domain.copy()
                domain2 += res['__domain']
                result = request.env[model].sudo().search(
                    domain2, offset=offset, limit=limit)
                result = props_fields(result, fields)
                data_info = {
                    'date_count': res['date_count'],
                    'amount ': res['amount'],
                    'month': result[0]['month'],
                    'date:month': res['date:month'],
                }
                if result:
                    data_info['current_count'] = len(result) + int(offset)
                    data_info['data'] = result
                    data.append(data_info)
        except Exception as e:
            result = []

        max_count = max([d['date_count']
                        for d in result2 if 'date_count' in d] or [-1])
        count = (max_count // PAGE_SIZE) + 1
        next_page = None if count <= int(page) else (int(page) + 1)
        return successful_response(
            status=OUT_SUCCESS_CODE,
            dict_data={
                'count': count,
                'results': data or [],
                'next_page': next_page,
            }
        )

    #  Get sponsor arrears records
    @http.route('/api/sponsor/arrears/page/<page>', methods=["GET"], type='http', auth='none')
    @check_permissions
    def get_sponsor_arrears_records(self, page, **kw):
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
            limit = None
        # Set parmeters.
        model = "takaful.sponsorship"
        fields = [
            'id',
            'code',
            'next_due_date',
            'due_days',
            'contribution_value',
        ]

        uid = request.session.uid
        user_data = self.get_user_sponsor_info(uid)
        sponsor_id = user_data["sponsor_id"]

        domain = [
             '&',
                ['sponsor_id', '=', sponsor_id.id],
                ['has_delay', '=', True],
        ]

        result2 = []
        data = []
        try:
            result2 = request.env[model].sudo().read_group(
                domain, fields, ['next_due_date:month'])
            for res in result2:
                domain2 = []
                domain2 = domain.copy()
                domain2 += res['__domain']
                result = request.env[model].sudo().search(
                    domain2, offset=offset, limit=limit,order='id desc')
                result = props_fields(result, fields)
                data_group = {
                    'date_count': res['next_due_date_count'],
                    'due_days ': res['due_days'],
                    'contribution_value ': res['contribution_value'],
                    'next_due_date:month': res['next_due_date:month'],
                }
                if result:
                    data_group['current_count'] = len(result) + int(offset)
                    data_group['data'] = result
                    data.append(data_group)
        except Exception as e:
            print("***********************************")
            print(e)
            result = []
        max_count = max([d['next_due_date_count']
                        for d in result2 if 'next_due_date_count' in d] or [-1])
        count = (max_count // PAGE_SIZE) + 1
        next_page = None if count <= int(page) else (int(page) + 1)
        return successful_response(
            status=OUT_SUCCESS_CODE,
            dict_data={
                'count': count,
                'results': data or [],
                'next_page': next_page,
            }
        )

    #  Get sponsorships gifting record
    @http.route('/api/sponsor/gifting/page/<page>', methods=["GET"], type='http', auth='none')
    @check_permissions
    def get_sponsorships_gifting_record(self, page, **kw):
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
            limit = None

        # Set parmeters.
        model = "takaful.sponsorship"
        fields = [
            'id',
            'gifter_name',
            'benefit_type',
            'sponsorship_duration',
            'start_date',
            'month_count',
            'contribution_value',

        ]

        uid = request.session.uid
        user_data = self.get_user_sponsor_info(uid)
        sponsor_id = user_data["sponsor_id"]

        domain = [
            '&',
            ['sponsor_id', '=', sponsor_id.id],
            ['is_gift', '=', 'yes'],
        ]

        try:
            result = request.env[model].sudo().search(
                domain, offset=offset, limit=limit,order='id desc')
            result = props_fields(result, fields)
        except Exception as e:
            result = []

        count = len(result)
        next_page = None if count < PAGE_SIZE else (int(page) + 1)
        return successful_response(
            status=OUT_SUCCESS_CODE,
            dict_data={
                'count': count,
                'results': result or [],
                'next_page': next_page,
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

        if mobile1 != mobile2:
            error_descrip = _('Enter anothor sponsor mobile number')
            error = 'invalid_mobile'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        res = request.env['takaful.sponsor'].sudo().search(
            [('mobile', '=', mobile)], limit=1)
        if res:
            return successful_response(
                status=OUT_SUCCESS_CODE,
                dict_data={
                    'id': res.id,
                    'name': res.name,
                    # 'list' :props_fields(res, res._fields)
                }
            )
        else:
            error_descrip = _('This sponsor does not exist')
            error = 'does_not_exist'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)


    @http.route('/api/sponsor/sponsorships/create2', methods=['POST'], type='http', auth='none', csrf=False)
    @check_permissions
    def do_create_sponsorship2(self, **kw):
         # Get Sponsor Info...
        uid = request.session.uid
        user_data = self.get_user_sponsor_info(uid)
        sudoConf = request.env['ir.config_parameter'].sudo()
        sponsor_id = user_data["sponsor_id"]
        context = request.env.context.copy()
        context.update({'lang': u'ar_SY'})
        request.env.context = context
        
        benefit_id = kw.get('benefit_id', False)
        months_number = kw.get('months_number', False)
        orphan_ids = kw.get('orphan_ids', [])
        sponsorship_duration = kw.get('sponsorship_duration', False)
        month_amount = kw.get('month_amount', False)
        sponsorship_class = kw.get('sponsorship_class', False)
        payment_option = kw.get('payment_option', False)
        orphan_ids = kw.get('orphans', [])
        
        gifter_id = kw.get('gifter_id', False)
        gifter_name = kw.get('gifter_name', '')
        gifter_mobile = kw.get('gifter_mobile', False)
        gifter_message = kw.get('gifter_message', '')
        is_gift = kw.get('is_gift', 'no')
        try :
            domain = [('id', '=', int(benefit_id))]
            benefit = request.env['grant.benefit'].sudo().search(
                    domain, limit=1)
            start_date = get_first_day_of_next_month()
            allowed_days = int(sudoConf.get_param(
                    'odex_takaful_base.allowed_pay_days'))
            end_date = start_date + \
                    relativedelta(months=int(months_number), days=(
                        start_date.day + allowed_days))
            if not all([benefit_id,sponsorship_duration ,payment_option,sponsorship_class]):
                error_descrip = _('Invalid benefit_id,payment_option,sponsorship_duration ,sponsorship_class')
                error = 'invalid_data'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)
            if is_gift == 'yes' :
                if not all([gifter_name,gifter_message ,gifter_mobile]):
                    if gifter_id:
                        try:
                            gifter_id = int(gifter_id)
                        except Exception as e:
                            error_descrip = _('Invalid Id for Gifter or Invalid gifter_name,gifter_message ,gifter_mobile')
                            error = 'invalid_gifter_id or Invalid gifter_name,gifter_message ,gifter_mobile'
                            _logger.error(error_descrip)
                            return error_response(400, error, error_descrip)

                        gifter = request.env['takaful.sponsor'].sudo().search(
                            [('id', '=', gifter_id)], limit=1)
                        if not gifter:
                            error_descrip = _('Gifter does not exist for this Id')
                            error = 'does_not_exist'
                            _logger.error(error_descrip)
                            return error_response(400, error, error_descrip)

                        gifter_name = gifter.name
                        gifter_mobile = gifter.mobile
                        gifter_id = gifter.id
                    else:
                        error_descrip = _('Invalid gifter_name,gifter_message ,gifter_mobile')
                        error = 'invalid_data'
                        _logger.error(error_descrip)
                        return error_response(400, error, error_descrip)
            if orphan_ids:
                try:
                    orphan_ids = literal_eval(orphan_ids)
                except Exception as e:
                    error_descrip = _('Invalid orphan ids')
                    error = 'invalid_data'
                    _logger.error(error_descrip)
                    return error_response(400, error, error_descrip)
            data_sponsor_id = {
                    'name': "New",
                    'sponsorship_type': "person",  # group
                    'sponsor_id': sponsor_id.id,
                    'benefit_id': benefit.id,
                    'benefit_type': benefit.benefit_type,
                    'sponsorship_duration': sponsorship_duration,
                    'sponsorship_class': sponsorship_class,
                    'contribution_value':month_amount or benefit.benefit_needs_value or 0,
                    'payment_option': payment_option,
                    'month_count':months_number,
                    'end_date':end_date,
                    'gifter_id': gifter_id,
                    'gifter_name': gifter_name,
                    'gifter_mobile': gifter_mobile,
                    'gifter_message': gifter_message,
                    'is_gift': is_gift,
                }
            orphan_sponsorship = None
            main_sponsorship = None
            main_sponsorship = request.env['takaful.sponsorship'].sudo().create(data_sponsor_id)
            data_res = {}
            orphan_sponsorship_info = []
            if main_sponsorship :
                # main_sponsorship._compute_month_count()
                data_res['main_sponsorship'] = main_sponsorship.read([])#main_sponsorship.id
                data_res['orphan_sponsorship_info'] = orphan_sponsorship_info
            for orphan_id in orphan_ids :
                benefit_id = request.env['grant.benefit'].sudo().search([('id','=',orphan_id.get('id'))], limit=1)
                if not benefit_id :
                    continue
                sponsor_id_data ={
                    'name': "New",
                    'sponsorship_type': "person",  # group
                    'sponsor_id': sponsor_id.id,
                    'benefit_id': benefit_id.id,
                    'benefit_type': benefit_id.benefit_type,
                    'sponsorship_duration': orphan_id.get('sponsorship_duration',False) or sponsorship_duration,
                    'sponsorship_class': orphan_id.get('sponsorship_class',False) or sponsorship_class , 
                    'contribution_value':float(orphan_id.get('month_amount',0)) or benefit_id.benefit_needs_value or 0,
                    'payment_option': payment_option,
                    'month_count':months_number,
                    'end_date':end_date,
                    'gifter_id': gifter_id,
                    'gifter_name': gifter_name,
                    'gifter_mobile': gifter_mobile,
                    'gifter_message': gifter_message,
                    'is_gift': is_gift,
                }
                # main_sponsorship.with_orphan_ids = [(0,0,[benefit_id.id])]
                
                main_sponsorship.sudo().write(
                    {'with_orphan_ids': [(4, benefit_id.id)]})
                orphan_sponsorship = request.env['takaful.sponsorship'].sudo().create(sponsor_id_data)
                orphan_sponsorship_info.append(orphan_sponsorship.read([]))
            if  orphan_sponsorship and  main_sponsorship:
                main_sponsorship.sudo().write({'is_widow_orphan': True})
                main_sponsorship.sudo().action_confirm_data()
                orphan_sponsorship.sudo().action_confirm_data()    
            return successful_response(
                OUT_SUCCESS_CODE,
                data_res,
            )
        except Exception as e :
            return error_response(500,error=str(e),error_descrip=traceback.print_exc() )
        
    # Create a new Sponsorship
    @http.route('/api/sponsor/sponsorships/create', methods=['POST'], type='http', auth='none', csrf=False)
    @check_permissions
    def do_create_sponsorship(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        orphan_sponsorship = None
        main_sponsorship = None
        context.update({'lang': u'ar_SY'})
        request.env.context = context

        benefit_id = kw.get('benefit_id', False)
        benefit_type = kw.get('benefit_type', False)

        is_group = kw.get('is_group', 'no')
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

        # If group is yes.
        benefit_count = kw.get('benefit_count', False)
        need_limit = kw.get('need_limit', False)
        age_limit = kw.get('age_limit', False)

        if is_group and is_group != 'no':
            if is_group != 'yes':
                error_descrip = _('invalid is_group value')
                error = 'invalid_group_value'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

            keys = all([benefit_type, need_limit, age_limit, benefit_count,
                       payment_option, sponsorship_duration, month_amount])
        else:

            keys = all([is_gift, benefit_id, benefit_type,
                       payment_option, sponsorship_duration, month_amount])

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

        if month_amount <= 0:
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

            if months_number <= 0:
                error_descrip = _('Invalid Months Number')
                error = 'invalid_data'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

            sudoConf = request.env['ir.config_parameter'].sudo()
            allowed_days = int(sudoConf.get_param(
                'odex_takaful_base.allowed_pay_days'))
            start_date = get_first_day_of_next_month()
            end_date = start_date + \
                relativedelta(months=months_number, days=(
                    start_date.day + allowed_days))
        # For Group
        if is_group == 'yes':
            try:
                age_limit = int(age_limit)
                need_limit = int(need_limit)
            except Exception as e:
                error_descrip = _(
                    'Invalid value for ages limit or needs limit')
                error = 'invalid_data'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

            if age_limit <= 0 or need_limit <= 0:
                error_descrip = _(
                    'Invalid value for ages limit or needs limit')
                error = 'invalid_data'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

            try:
                benefit_count = int(benefit_count)
            except Exception as e:
                error_descrip = _('Invalid Benefits count')
                error = 'invalid_data'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

            if benefit_count <= 1:
                error_descrip = _(
                    'Invalid Benefits Count, At least Two Beneficiaries For Sponsorship Group')
                error = 'invalid_data'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

            domain = [('benefit_type', '=', benefit_type),
                      ('benefit_needs_percent', '>', need_limit), ('age', '>', age_limit)]
            benefits = request.env['grant.benefit'].sudo().search(
                domain, limit=benefit_count,order='id desc')
            if not benefits:
                error_descrip = _('No Benefits found')
                error = 'does_not_exist'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

            if len(benefits) == 1:
                error_descrip = _(
                    'Matching Only One Benefit, At least Two Beneficiaries For Sponsorship Group')
                error = 'invalid_data'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

            if len(benefits) != benefit_count:
                error_descrip = _(
                    'Mismatch in count, only found %s Benefits') % len(benefits)
                error = 'invalid_data'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

            # rec_sum = sum(benefits.filtered(lambda x: x).mapped('id'))
            if sponsorship_class == "fully":
                total_sponsorship = sum(benefits.mapped('benefit_needs_value'))
            else:
                total_sponsorship = default_sponsorship * benefit_count

            if month_amount < total_sponsorship:
                error_descrip = _(
                    'Invalid Month Amount, At least %s') % total_sponsorship
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
                'benefit_count': len(benefits),
            })
            group_sponsorship.sudo().action_confirm_data()
            # Return OK
            return successful_response(
                OUT_SUCCESS_CODE,
                {},
            )

        if month_amount < default_sponsorship:
            error_descrip = _(
                'Invalid Month Amount, At least %s') % default_sponsorship
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

        benefit = request.env['grant.benefit'].sudo().search(
            [('id', '=', benefit_id)], limit=1)
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

                gifter = request.env['takaful.sponsor'].sudo().search(
                    [('id', '=', gifter_id)], limit=1)
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
            benefits = request.env['grant.benefit'].sudo().search(
                [('id', 'in', orphan_ids)],order='id desc')
            if not with_orphan in ['yes', 'no']:
                error_descrip = _(
                    'Including Orphans value is invalid or missing')
                error = 'invalid_with_orphan'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

            if with_orphan == 'yes':
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
                    default_sponsorship = max(
                        benefits.mapped('benefit_needs_value'))
                    orphan_value = default_sponsorship
                    
                if orphan_value < default_sponsorship:
                    error_descrip = _(
                        'Invalid orphan value, At least %s') % default_sponsorship
                    error = 'invalid_data'
                    _logger.error(error_descrip)
                    return error_response(400, error, error_descrip)

            elif with_orphan == 'yes' and not orphan_value:
                error_descrip = _('Missing orphan value')
                error = 'missing_data'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)
            benefits = request.env['grant.benefit'].sudo().search(
                [('id', 'in', orphan_ids)],order='id desc')
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
                'sponsorship_type': "person",  # group
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
            main_sponsorship.sudo().action_confirm_data()
        else:
        
            main_sponsorship = request.env['takaful.sponsorship'].sudo().create({
                'name': "New",
                'sponsorship_type': "person",  # group
                'sponsor_id': sponsor_id.id,
                'benefit_id': benefit.id,
                'benefit_type': benefit_type,
                'sponsorship_duration': sponsorship_duration,
                'month_count':months_number,
                'sponsorship_class': sponsorship_class,
                'payment_option': payment_option,
                'contribution_value': month_amount,
                'end_date': end_date,
                'is_gift': is_gift,
            })
            main_sponsorship.sudo().action_confirm_data()

        if with_orphan == 'yes' and is_gift == 'yes' and benefits:
            for ben in benefits:
                orphan_sponsorship = request.env['takaful.sponsorship'].sudo().create({
                    'name': "New",
                    'sponsorship_type': "person",  # group
                    'sponsor_id': sponsor_id.id,
                    'benefit_id': ben.id,
                    'benefit_type': 'orphan',
                    'sponsorship_duration': sponsorship_duration,
                    'sponsorship_class': sponsorship_class,
                    'payment_option': payment_option,
                    'contribution_value': orphan_value,
                    'month_count':months_number,
                    'gifter_id': gifter_id,
                    'gifter_name': gifter_name,
                    'gifter_mobile': gifter_mobile,
                    'gifter_message': gifter_message,
                    'end_date': end_date,
                    'is_gift': is_gift,
                })
                main_sponsorship.sudo().write(
                    {'with_orphan_ids': [(4, ben.id)]})
                orphan_sponsorship.sudo().action_confirm_data()
            main_sponsorship.sudo().write({'is_widow_orphan': True})
            main_sponsorship.sudo().action_confirm_data()

        elif with_orphan == 'yes' and benefits:
            for ben in benefits:
                orphan_sponsorship = request.env['takaful.sponsorship'].sudo().create({
                    'name': "New",
                    'sponsorship_type': "person",  # group
                    'sponsor_id': sponsor_id.id,
                    'benefit_id': ben.id,
                    'benefit_type': 'orphan',
                    'sponsorship_duration': sponsorship_duration,
                    'month_count':months_number,
                    'sponsorship_class': sponsorship_class,
                    'payment_option': payment_option,
                    'contribution_value': orphan_value,
                    'end_date': end_date,
                    'is_gift': is_gift,
                })
                main_sponsorship.sudo().write(
                    {'with_orphan_ids': [(4, ben.id)]})
                orphan_sponsorship.sudo().action_confirm_data()
            main_sponsorship.sudo().write({'is_widow_orphan': True})
            main_sponsorship.sudo().action_confirm_data()
        request_json = {}

        if orphan_sponsorship:
            request_json['orphan_sponsorship'] = orphan_sponsorship.read([])
        if main_sponsorship:
            request_json['main_sponsorship'] = main_sponsorship.read([])
        return successful_response(
            OUT_SUCCESS_CODE,
            request_json,
        )

    # Create a paying_demo
    @http.route('/api/sponsor/paying_demo/save', methods=['POST'], type='http', auth='none', csrf=False)
    @check_permissions
    def do_save_paying_demo(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_SY'})
        request.env.context = context

        sponsorship_id = kw.get('sponsorship_id', False)
        pay_months = kw.get('pay_months', 1)
        pay_title = kw.get('pay_title', _('Sponsorship Payment'))

        benefit_id = kw.get('benefit_id', False)
        need_id = kw.get('need_id', False)
        operation_type = kw.get('operation_type', False)
        amount = kw.get('amount', False)
        message = kw.get('message', '')
        benefit_ids = []

        name = ''

        if not operation_type in ['sponsorship', 'gift', 'contribution']:
            error_descrip = _('Invalid value for %s ') % 'operation_type'
            error = 'invalid_data'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        if operation_type == 'sponsorship':
            keys = all([sponsorship_id, pay_months, pay_title, amount])

        elif operation_type == 'gift':
            keys = all([benefit_id, amount])

        elif operation_type == 'contribution':
            keys = all([need_id, amount])

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

        # For Sponsorship
        if operation_type == 'sponsorship':
            try:
                sponsorship_id = int(sponsorship_id)
            except Exception as e:
                error_descrip = _('Invalid Id for Sponsorship')
                error = 'invalid_data'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

            uid = request.session.uid
            user_data = self.get_user_sponsor_info(uid)
            sponsor_id = user_data["sponsor_id"]

            sponsorship = request.env['takaful.sponsorship'].sudo().search(
                [('id', '=', sponsorship_id), ('sponsor_id', '=', sponsor_id.id)], limit=1)
            if not sponsorship:
                error_descrip = _(
                    'This Sponsorship does not exist in the system')
                error = 'does_not_exist'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

            if sponsorship.state == "canceled":
                error_descrip = _('This Sponsorship is already canceled')
                error = 'already_canceled'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

            # Create Manual Payment record by current user
            # draft_cancel = request.env['sponsorship.cancellation'].sudo().create({
            #     'sponsorship_id': sponsorship_id,
            #     'reason_id': reason_id,
            #     'cancel_type': "user",
            #     'state': "draft",
            #     'cancel_user_id': uid,
            #     'note': _('The Sponsor request to cancel this Sponsorship'),
            # })

            # Get info
            if sponsorship.benefit_ids:
                benefit_ids = sponsorship.benefit_ids.ids
            elif sponsorship.benefit_id:
                benefit_id = sponsorship.benefit_id.id

            # Create New Operation
            operation_id = request.env['takaful.sponsor.operation'].sudo().create({
                'name': u'كفالة ' + dict(sponsorship.fields_get(allfields=['benefit_type'])['benefit_type']['selection'])[sponsorship['benefit_type']],
                'title': pay_title,
                'sponsor_id': sponsor_id.id,
                'origin_id': int(sponsorship.id),
                'operation_type': operation_type,
                'amount': amount,
            })

            if benefit_ids:
                for id_ in benefit_ids:
                    operation_id.sudo().write({'benefit_ids': [(4, id_)]})
            else:
                operation_id.benefit_id = benefit_id

            return successful_response(
                OUT_SUCCESS_CODE,
                {},
            )

        # For other
        if operation_type == 'gift':
            try:
                benefit_id = int(benefit_id)
            except Exception as e:
                error_descrip = _('Invalid value for %s ') % 'benefit_id'
                error = 'invalid_data'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

            benefit = request.env['grant.benefit'].sudo().search(
                [('id', '=', benefit_id)], limit=1)
            if not benefit:
                error_descrip = _('This Benefit does not exist')
                error = 'does_not_exist'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)
            title = benefit.name
        else:
            try:
                need_id = int(need_id)
            except Exception as e:
                error_descrip = _('Invalid value for %s ') % 'need_id'
                error = 'invalid_data'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

            need_type = request.env['benefits.needs'].sudo().search(
                [('id', '=', need_id)], limit=1)
            if not need_type:
                error_descrip = _('This Need does not exist')
                error = 'does_not_exist'
                _logger.error(error_descrip)
                return error_response(400, error, error_descrip)

            # if benefit_id and need_type.benefit_id and need_type.benefit_id != benefit_id:
            #     error_descrip = _('Mismatch Need for Benefit')
            #     error = 'invalid_data'
            #     _logger.error(error_descrip)
            #     return error_response(400, error, error_descrip)

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
                'operation_type': operation_type,
                'amount': amount,
                'note': message
            })
            name = u'سداد هدية مالية'
        else:
            contribution = request.env['takaful.contribution'].sudo().create({
                'name': name,
                'need_id': need_id,
                'sponsor_id': sponsor_id.id,
                'operation_type': operation_type,
                'amount': amount,
                'note': message
            })
            title = name
            name = u'سداد إحتياجات'

            if benefit_ids:
                for id_ in benefit_ids:
                    contribution.sudo().write({'benefit_ids': [(4, id_)]})
            else:
                contribution.benefit_id = benefit_id
                title = need_type.benefit_id.name

        # Create New Operation
        operation_id = request.env['takaful.sponsor.operation'].sudo().create({
            'name': name,
            'title': title,
            'sponsor_id': sponsor_id.id,
            'operation_type': operation_type,
            'amount': amount,
        })
        if benefit_ids:
            for id_ in benefit_ids:
                operation_id.sudo().write({'benefit_ids': [(4, id_)]})
        else:
            operation_id.benefit_id = benefit_id

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

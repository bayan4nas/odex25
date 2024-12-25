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


class ControllerPortalREST(http.Controller):
    # This Sponsor Portal API
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

    def add_info_widow_sponsorships(self, result, benefit_type):
        info = []
        if benefit_type == 'orphan':
            for res in result:
                data = {}
                data = dict(res)
                data['benefit_id'] = self.get_sponsorship_benefit_info(res['benefit_id'], benefit_type)
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
                    benefits = request.env['grant.benefit'].sudo().search([('id', 'in', res['with_orphan_ids'])])
                    for ben in benefits:
                        sponsored_orphans.append({
                            'id': ben.id,
                            'name': ben.name,
                        })

                data['benefit_id'] = self.get_sponsorship_benefit_info(res['benefit_id'], benefit_type)
                data['with_orphan_ids'] = sponsored_orphans or None
                data['with_orphans_count'] = len(sponsored_orphans)

                orphans_month_amount = sum(request.env['takaful.sponsorship'].sudo().search([('sponsor_id', '=', sponsor_id.id), ('benefit_id', 'in', res['with_orphan_ids'])]).mapped('contribution_value'))
                data['orphans_contribution_value'] = orphans_month_amount or 0
                data['contribution_value'] = res['contribution_value'] + orphans_month_amount
                info.append(data)

        return info

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
        data['city_id'] = benefit.city_id.name or None
        data['number'] = benefit.housing_id.house_number or None
        data['benefit_type'] = dict(benefit.fields_get(allfields=['benefit_type'])['benefit_type']['selection'])[benefit['benefit_type']] if benefit.benefit_type else None
        data['has_needs'] = benefit.has_needs
        data['has_arrears'] = benefit.has_arrears

        if benefit_type == "widow":
            data['total_income'] = benefit.total_income
            if benefit.orphan_ids.ids:
                orphans = []
                for orphan in benefit.orphan_ids:
                    orphans.append({
                        "id": orphan.id,
                        "first_name": orphan.first_name,
                        "benefit_available_need": float(format(orphan.benefit_needs_value, '.2f')),
                    })
                data['orphan_ids'] = orphans or None
            else:
                data['orphan_ids'] = None

            data['orphan_count'] = len(benefit.orphan_ids) or 0

            salary_resouces = []
            for source in benefit.salary_ids:
                if source.salary_type:
                    salary_resouces.append(source.salary_type)
            data['salary_resouces'] = salary_resouces or None
            
        if benefit_type == "orphan":
            data['gender'] = dict(benefit.fields_get(allfields=['gender'])['gender']['selection'])[benefit['gender']] if benefit.gender else None
            data['orphan_status'] = dict(benefit.fields_get(allfields=['orphan_status'])['orphan_status']['selection'])[benefit['orphan_status']] if benefit.orphan_status else None

            data['education_level'] = dict(benefit.fields_get(allfields=['education_level'])['education_level']['selection'])[benefit['education_level']] if benefit.education_level else None
            data['class_room'] = benefit.classroom or None
            data['quran_parts'] = benefit.number_parts or 0

        data['responsible'] = dict(benefit.fields_get(allfields=['responsible'])['responsible']['selection'])[benefit['responsible']] if benefit.responsible else None
        data['health_status'] = dict(benefit.fields_get(allfields=['health_status'])['health_status']['selection'])[benefit['health_status']] if benefit.health_status else None

        data['housing_status'] = dict(benefit.housing_id.fields_get(allfields=['property_type'])['property_type']['selection'])[benefit.housing_id['property_type']] if benefit.housing_id.property_type else None
        data['education_status'] = dict(benefit.fields_get(allfields=['education_status'])['education_status']['selection'])[benefit['education_status']] if benefit.education_status else None

        skills = []
        for skill in benefit.craft_skill_ids:
            if skill.name:
                skills.append(skill.name)

        for skill in benefit.training_inclinations_ids:
            if skill.name:
                skills.append(skill.name)

        data['skills'] = skills or None

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
        
        needs_list = request.env['benefits.needs'].sudo().search(domain) 
        needs = []
        for need in needs_list:
            if need.name:
                needs.append(need.name)
        data['needs'] = needs or None

        return data

    @http.route('/portal/sys/get_sponsorship_value', methods=['GET'], auth='user', website=True, csrf=False)
    def sys_sponsorship_value(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context
        
        try:
            return json.dumps({
                    'status': True,
                    'default_sponsorship': {'amount': self.get_default_sponsorship_amount()},
                })
        except Exception as e:
            _logger.error(str(e))
            message = str(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    # For notifications
    @http.route('/portal/sponsor/notifications/page/<page>', methods=["GET"], auth='user', website=True, csrf=False)
    def get_notification_list(self, page, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        try:
            if page:
                try:
                    offset = (int(page) * PAGE_SIZE) - PAGE_SIZE
                    limit = PAGE_SIZE
                except Exception as e:
                    data = {'status': False, 'msg': _('URL Not Found')}
                    return json.dumps(data)      
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

            result = request.env[model].sudo().search(domain, offset=offset, limit=limit)
            if result:
                result = props_fields(result, fields)
                count = len(result)
            else:
                result = None
                count = 0

            next_page = None if count < PAGE_SIZE else (int(page) + 1)
            return json.dumps({
                    'status': True,
                    'count': count,
                    'results': result or [],
                    'next_page': next_page,
                })
        except Exception as e:
            _logger.error(str(e))
            message = str(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    # For notifications: Read one
    @http.route('/portal/sponsor/notify/read/<id>', methods=["GET"], auth='user', website=True, csrf=False)
    def read_notification_id(self, id, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        try:
            try:
                object_id = int(id)
            except Exception as e:
                data = {'status': False, 'msg': _('URL Not Found')}
                return json.dumps(data)

            # Set parmeters.
            model = "takaful.push.notification"
            uid = request.session.uid
            domain = [('id', '=', object_id), ('user_id', '=', uid)]

            res = request.env[model].sudo().search(domain, limit=1)
            if res:
                # Make is_read as True
                res.is_read = True
                dict_data = {
                    'id': res.id,
                    'title': res.title,
                    'body': res.body,
                    'sent_on': res.sent_on,
                    # 'is_read': res.is_read,
                }
                return json.dumps({
                    'status': True,
                    'notification': dict_data,
                })
            else:
                message = _('No notification is found')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)
            
        except Exception as e:
            _logger.error(str(e))
            message = str(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    # For notifications: Delete one
    @http.route('/portal/sponsor/notify/delete/<id>', methods=["GET"], auth='user', website=True, csrf=False)
    def delete_notification_id(self, id, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        try:
            try:
                object_id = int(id)
            except Exception as e:
                data = {'status': False, 'msg': _('URL Not Found')}
                return json.dumps(data)

            # Set parmeters.
            model = "takaful.push.notification"
            uid = request.session.uid
            domain = [('id', '=', object_id), ('user_id', '=', uid)]

            res = request.env[model].sudo().search(domain, limit=1)
            if res:
                try:
                    res.unlink()
                    return json.dumps({
                        'status': True,
                        'msg': _('Notification was deleted'),
                    })
                except Exception as e:
                    message = _('Cannot delete this notification')
                    _logger.error(message)
                    data = {'status': False, 'msg': message}
                    return json.dumps(data)

            else:
                message = _('No notification is found')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)
            
        except Exception as e:
            _logger.error(str(e))
            message = str(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    # For Sponsor Info
    @http.route('/portal/sponsor/profile', methods=["GET"], auth='user', website=True, csrf=False)
    def get_sponsor_info(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        try:
            # Set parmeters.
            uid = request.session.uid
            user_data = self.get_user_sponsor_info(uid)
            sponsor_id = user_data["sponsor_id"]

            if sponsor_id:   
                if sponsor_id.company_type in ["company", "charity"]:
                    dict_data = {
                        'id': sponsor_id.id,
                        'name': sponsor_id.name,
                        'id_number': sponsor_id.id_number,
                        'company_type': sponsor_id.company_type,
                        'email': sponsor_id.email,
                        'mobile': sponsor_id.mobile,
                        'city_id': sponsor_id.city_id.id or None,
                        'city_name': sponsor_id.city_id.name,
                        # Bank info
                        'account_number': sponsor_id.account_number,
                        'iban': sponsor_id.iban,
                        'bank_id': sponsor_id.bank_id.id or None,
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
                        'city_id': sponsor_id.city_id.id or None,
                        'city_name': sponsor_id.city_id.name,
                        # Bank info
                        'account_number': sponsor_id.account_number,
                        'iban': sponsor_id.iban,
                        'bank_id': sponsor_id.bank_id.id or None,
                        'bank_name': sponsor_id.bank_id.name,
                        'bank_entity_name': sponsor_id.bank_entity_name,
                    }
               
                return json.dumps({
                    'status': True,
                    'sponsor': dict_data,
                })
            else:
                message = _('No sponsor is found')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

        except Exception as e:
            _logger.error(str(e))
            message = str(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)
        

    # Update Record for Sponsor
    @http.route('/portal/sponsor/profile/update', methods=['PUT'], auth='user', website=True, csrf=False)
    def do_update_sponsor_profile(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        try:
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
                print(values)
                if not field_name in updated_fields:
                    message = _('Cannot update this field: %s ') % field_name
                    _logger.error(message)
                    data = {'status': False, 'msg': message}
                    return json.dumps(data)
                
                if field_value == "true" or field_value == "True":
                    values[field_name] = True
                elif field_value == "false" or field_value == "False":
                    values[field_name] = False
                else:
                    values[field_name] = field_value
            
            if not values:
                message = _('Some or all data is missing')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            mobile = values.get('mobile', False)
            if mobile and re.match(SAUDI_MOBILE_PATTERN, str(mobile)) == None:
                message = _('Enter a valid Saudi mobile number')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            uid = request.session.uid
            user_data = self.get_user_sponsor_info(uid)
            sponsor_id = user_data["sponsor_id"]

            if sponsor_id:   
                try:
                    # Update Record forthis Sponsor
                    sponsor_id.sudo().write(values)
                    return json.dumps({
                        'status': True,
                        'msg': _('Profile was updated'),
                    })
                except Exception as e:
                    message = _('Faield to update this sponsor')
                    _logger.error(message)
                    data = {'status': False, 'msg': message}
                    return json.dumps(data)
            else:
                message = _('No sponsor is found')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)
            
        except Exception as e:
            _logger.error(str(e))
            message = str(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    # Sponsor notify_setting
    @http.route('/portal/sponsor/notify_setting', methods=["GET"], auth='user', website=True, csrf=False)
    def get_sponsor_notify_setting(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        try:
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
                return json.dumps({
                    'status': True,
                    'notify_setting': dict_data,
                })
            else:
                message = _('No sponsor is found')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)
            
        except Exception as e:
            _logger.error(str(e))
            message = str(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    # Update notify settings for Sponsor
    @http.route('/portal/sponsor/notify_setting/update', methods=['POST'], auth='user', website=True, csrf=False)
    def do_update_sponsor_notify_setting(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        try:
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
                    message = _('Cannot update this field: %s ') % field_name
                    _logger.error(message)
                    data = {'status': False, 'msg': message}
                    return json.dumps(data)

                if field_value == "true" or field_value == "True":
                    values[field_name] = True
                elif field_value == "false" or field_value == "False":
                    values[field_name] = False
                else:
                    values[field_name] = field_value
            
            if not values:
                message = _('Some or all data is missing')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            uid = request.session.uid
            user_data = self.get_user_sponsor_info(uid)
            sponsor_id = user_data["sponsor_id"]

            if sponsor_id:   
                try:
                    # Update Record forthis Sponsor
                    sponsor_id.sudo().write(values)
                    return json.dumps({
                        'status': True,
                        'msg': _('Notifications settings were updated'),
                    })
                except Exception as e:
                    message = _('Faield to update these settings')
                    _logger.error(message)
                    data = {'status': False, 'msg': message}
                    return json.dumps(data)
            else:
                message = _('No sponsor is found')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)
            
        except Exception as e:
            _logger.error(str(e))
            message = str(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    # Sponsor certificate_setting
    @http.route('/portal/sponsor/certificate_setting', methods=["GET"], auth='user', website=True, csrf=False)
    def get_sponsor_certificate_setting(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        try:
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
                return json.dumps({
                    'status': True,
                    'certificate_setting': dict_data,
                })
            else:
                message = _('No sponsor is found')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)
            
        except Exception as e:
            _logger.error(str(e))
            message = str(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    # Update certificate settings for Sponsor
    @http.route('/portal/sponsor/certificate_setting/update', methods=['POST'], auth='user', website=True, csrf=False)
    def do_update_sponsor_certificate_setting(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        try:
            updated_fields = [
                'name_in_certificate',
                'type_in_certificate',
                'duration_in_certificate',
            ]
            values = {}
            for field_name, field_value in kw.items():
                if not field_name in updated_fields:
                    message = _('Cannot update this field: %s ') % field_name
                    _logger.error(message)
                    data = {'status': False, 'msg': message}
                    return json.dumps(data)
                
                if field_value == "true" or field_value == "True":
                    values[field_name] = True
                elif field_value == "false" or field_value == "False":
                    values[field_name] = False
                else:
                    values[field_name] = field_value
            
            if not values:
                message = _('Some or all data is missing')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            uid = request.session.uid
            user_data = self.get_user_sponsor_info(uid)
            sponsor_id = user_data["sponsor_id"]

            if sponsor_id:   
                try:
                    # Update Record forthis Sponsor
                    sponsor_id.sudo().write(values)
                    return json.dumps({
                        'status': True,
                        'msg': _('Certificate settings were updated'),
                    })
                except Exception as e:
                    message = _('Faield to update these settings')
                    _logger.error(message)
                    data = {'status': False, 'msg': message}
                    return json.dumps(data)
            else:
                message = _('No sponsor is found')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)
            
        except Exception as e:
            _logger.error(str(e))
            message = str(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    # Get Benefit Filters
    @http.route('/portal/sys/benefit_filters', methods=['GET'], auth='user', website=True, csrf=False)
    def get_benefit_filters(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        try:
            benefit_type = kw.get('benefit_type', False)
            if not benefit_type:
                message = _('Missing data for Orphan or Widow')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            if not benefit_type in ['orphan', 'widow']:
                message = _('Invalid Orphan or Widow')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

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

            # Return filters
            return json.dumps({
                'status': True,
                'filters': filters,
            })

        except Exception as e:
            _logger.error(str(e))
            message = str(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    @http.route('/portal/sys/benefits/page/<page>', methods=["GET"], auth='user', website=True, csrf=False)
    def sys_get_benefits(self, page, **kw):
        # Update context to add language
        try:
            context = request.env.context.copy()
            context.update({'lang': u'ar_001'})
            request.env.context = context
            if page:
                try:
                    offset = (int(page) * PAGE_SIZE) - PAGE_SIZE
                    limit = PAGE_SIZE
                except Exception as e:
                    data = {'status': False, 'msg': _('URL Not Found')}
                    return json.dumps(data)      
            else:
                offset = 0
                limit=None

            benefit_type = kw.get('benefit_type', False)
    
            if not benefit_type:
                message = _('Missing data for Orphan or Widow')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            if not benefit_type in ['orphan', 'widow']:
                message = _('Invalid Orphan or Widow')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

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
                result = None
                count = 0

            next_page = None if count < PAGE_SIZE else (int(page) + 1)
            return json.dumps({
                    'status': True,
                    'count': count,
                    'results': result or [],
                    'next_page': next_page,
                })
        except Exception as e:
            _logger.error(str(e))
            message = str(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    # Get User Sponsorships
    @http.route('/portal/sponsor/sponsorships/page/<page>', methods=["GET"], auth='user', website=True, csrf=False)
    def user_get_sponsorships(self, page, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        try:
            if page:
                try:
                    offset = (int(page) * PAGE_SIZE) - PAGE_SIZE
                    limit = PAGE_SIZE
                except Exception as e:
                    data = {'status': False, 'msg': _('URL Not Found')}
                    return json.dumps(data)      
            else:
                offset = 0
                limit=None

            benefit_type = kw.get('benefit_type', False)
    
            if not benefit_type:
                message = _('Missing data for Orphan or Widow')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            if not benefit_type in ['orphan', 'widow']:
                message = _('Invalid Orphan or Widow')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

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
            domain = [['sponsor_id', '=', sponsor_id.id], ['sponsorship_type', '=', 'person'], ['benefit_type', '=', benefit_type]]
            
            if filters:
                domain += filters
            else:
                if benefit_type == 'orphan':
                    filters = [
                        ['gender', 'in', ['male', 'female']],
                        ['state', 'in', ['confirmed', 'wait_pay', 'progress', 'to_cancel', 'canceled', 'closed']],
                    ]
                    domain += filters
                elif benefit_type == 'widow':
                    filters = [
                        ['state', 'in', ['confirmed', 'wait_pay', 'progress', 'to_cancel', 'canceled', 'closed']],
                    ]
                    domain += filters

            result = request.env[model].sudo().search(domain, offset=offset, limit=limit)
            result = props_fields(result, fields)
            if result:
                # if benefit_type == 'widow':
                result = self.add_info_widow_sponsorships(result, benefit_type)
                count = len(result)
            else:
                result = None
                count = 0

            next_page = 0 if count < PAGE_SIZE else (int(page) + 1)
            return json.dumps({
                    'status': True,
                    'count': count,
                    'results': result or [],
                    'next_page': next_page,
                })
        except Exception as e:
            _logger.error(str(e))
            message = str(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    # Get Beneficiary Details
    @http.route('/portal/sponsor/benefit/info', methods=["GET"], auth='user', website=True, csrf=False)
    def user_get_benefit(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        try:
            benefit_type = kw.get('benefit_type', False)
            benefit_id = kw.get('benefit_id', False)
            
            if not all([benefit_type, benefit_id]):
                message = _('Some or all data is missing')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            if not benefit_type in ['orphan', 'widow']:
                message = _('Invalid Orphan or Widow')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            try:
                benefit_id = int(benefit_id)
            except Exception as e:
                message = _('Invalid Id for Orphan or Widow')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            record = self.get_sponsorship_benefit_info(benefit_id, benefit_type)
            if not record:
                return json.dumps({
                'status': True,
                'benefit': None,
            })

            return json.dumps({
                'status': True,
                'benefit': record,
            })

        except Exception as e:
            _logger.error(str(e))
            message = str(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    # Get Cancel Reasons List
    @http.route('/portal/sys/reason_list', methods=["GET"], auth='user', website=True, csrf=False)
    def get_reason_list(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        try:
            # Set parmeters.
            model = 'sponsorship.reason.stop'
            fields = ['id', 'name']
            result = request.env[model].sudo().search([])
            result = props_fields(result, fields)
            
            return json.dumps({
                'status': True,
                'count': len(result),
                'results': result or [],
            })

        except Exception as e:
            _logger.error(str(e))
            message = str(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    # Create Cancel Record for Sponsorship: Do Cancel for Sponsorship
    @http.route('/portal/sponsor/sponsorships/cancel', methods=['POST'], auth='user', website=True, csrf=False)
    def do_cancel_sponsorship(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        try:
            sponsorship_id = kw.get('sponsorship_id', False)
            reason_id = kw.get('reason_id', False)
            
            if not all([sponsorship_id, reason_id]):
                message = _('Some or all data is missing')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            try:
                sponsorship_id = int(sponsorship_id)
                reason_id = int(reason_id)
            except Exception as e:
                message = _('Invalid Id for Sponsorship or Reason')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            reason = request.env['sponsorship.reason.stop'].sudo().search([('id','=',reason_id)], limit=1)
            if not reason:
                message = _('This Reason does not exist in the system')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            uid = request.session.uid
            user_data = self.get_user_sponsor_info(uid)
            sponsor_id = user_data["sponsor_id"]

            sponsorship = request.env['takaful.sponsorship'].sudo().search([('id','=',sponsorship_id), ('sponsor_id','=',sponsor_id.id)], limit=1)
            if not sponsorship:
                message = _('This Sponsorship does not exist in the system')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            if sponsorship.state == "canceled":
                message = _('This Sponsorship is already canceled')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            cancel_reason_id = request.env['sponsorship.cancellation'].sudo().search([('sponsorship_id','=', sponsorship.id)], limit=1)
            if cancel_reason_id:
                message = _('This Sponsorship is under review for cancel')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            # Create Manual cancellation record by current user
            draft_cancel = request.env['sponsorship.cancellation'].sudo().create({
                'sponsorship_id': sponsorship_id,
                'reason_id': reason_id,
                'cancel_type': "user",
                'state': "draft",
                'cancel_user_id': uid,
                'note': _('The Sponsor request to cancel this Sponsorship'),
            })
            
            return json.dumps({
                'status': True,
                'msg':  _('Successed, your sponsorship cancellation request is under review'),
            })

        except Exception as e:
            _logger.error(str(e))
            message = str(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    @http.route('/portal/sys/sponsorship_filters', methods=['GET'], auth='user', website=True, csrf=False)
    def get_sponsorship_filters(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        try:
            benefit_type = kw.get('benefit_type', False)
            if not benefit_type:
                message = _('Missing data for Orphan or Widow')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            if not benefit_type in ['orphan', 'widow']:
                message = _('Invalid Orphan or Widow')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

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

            # Return filters
            return json.dumps({
                'status': True,
                'filters': filters,
            })

        except Exception as e:
            _logger.error(str(e))
            message = str(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    # Get Need Filters
    @http.route('/portal/sys/need_filters', methods=['GET'], auth='user', website=True, csrf=False)
    def get_need_filters(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        try:
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

            # Return filters
            return json.dumps({
                'status': True,
                'filters': filters,
            })

        except Exception as e:
            _logger.error(str(e))
            message = str(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    # Get all need categories list
    @http.route('/portal/sys/need_category_list', methods=["GET"], type='http', auth='none')
    def get_city_list(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        try:
            # Set parmeters.
            model = 'needs.categories'
            fields = ['id', 'name']
            result = request.env[model].sudo().search([])
            result = props_fields(result, fields)
            
            return json.dumps({
                'status': True,
                'count': len(result),
                'results': result or [],
            })

        except Exception as e:
            _logger.error(str(e))
            message = str(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    # Get Need Types for general needs
    @http.route('/portal/sys/need_types/page/<page>', methods=["GET"], auth='user', website=True, csrf=False)
    def get_need_types(self, page, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        try:
            if page:
                try:
                    offset = (int(page) * PAGE_SIZE) - PAGE_SIZE
                    limit = PAGE_SIZE
                except Exception as e:
                    data = {'status': False, 'msg': _('URL Not Found')}
                    return json.dumps(data)      
            else:
                offset = 0
                limit=None

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
                ['remaining_amount','>', 0],
                ['state','=', 'published'], 
                ['benefit_need_type','=', 'general'], 
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
            try:
                result = request.env[model].sudo().search(domain, offset=offset, limit=limit)
                result = props_fields(result, fields)
            except Exception as e:
                result = []

            count = len(result)
            next_page = None if count < PAGE_SIZE else (int(page) + 1)
            return json.dumps({
                    'status': True,
                    'count': count,
                    'results': result or [],
                    'next_page': next_page,
                })

        except Exception as e:
            _logger.error(str(e))
            message = str(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    # Get Need type for one benefit: Based on Need Categoey Id
    @http.route('/portal/sys/benefit/need_types', methods=["GET"], auth='user', website=True, csrf=False)
    def get_benefit_need_types(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        try:
            need_category_id = kw.get('need_category_id', False)
            need_status = kw.get('need_status', False)
            benefit_id = kw.get('benefit_id', False)
            
            if not all([need_category_id, need_status, benefit_id]):
                message = _('Some or all data is missing')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            try:
                need_category_id = int(need_category_id)
            except Exception as e:
                message = _('Invalid value for %s ') % 'need_category_id'
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)
            
            try:
                benefit_id = int(benefit_id)
            except Exception as e:
                message = _('Invalid value for %s ') % 'benefit_id'
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            if not need_status in ['urgent', 'not_urgent']:
                message = _('Invalid value for %s ') % 'need_status'
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            model = 'benefits.needs'
            fields = [
                'id', 
                'name', 
                'category_name',
                'target_amount',
                'paid_amount',
                'remaining_amount',
                'completion_ratio',
            ]
            domain = [
                '&',
                ('remaining_amount','>', 0),
                ('state','=', 'published'),
                ('need_category','=', need_category_id),
                ('benefit_id','=', benefit_id),
                ('need_status','=', need_status),
                ('benefit_need_type','=', 'special'),
            ]

            result = request.env[model].sudo().search(domain)
            result = props_fields(result, fields)

            return json.dumps({
                'status': True,
                'count': len(result),
                'results': result or [],
            })

        except Exception as e:
            _logger.error(str(e))
            message = str(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    # Get Select a group of Benefit List
    @http.route('/portal/sys/select_benefit', methods=["GET"], auth='user', website=True, csrf=False)
    def get_selected_benefit(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_SY'})
        request.env.context = context

        try:
            orphan_ids = kw.get('orphan_ids', [])
            fields = ['id', 'first_name', 'benefit_needs_value', 'benefit_needs_percent']
            
            if orphan_ids:
                try:
                    orphan_ids = literal_eval(orphan_ids)
                except Exception as e:
                    message = _('Invalid orphan ids')
                    _logger.error(message)
                    data = {'status': False, 'msg': message}
                    return json.dumps(data)

                domain = [('id','in', orphan_ids), ('benefit_type','=', 'orphan')]
                result = request.env['grant.benefit'].sudo().search(domain)
                result = props_fields(result, fields)
                return json.dumps({
                    'status': True,
                    'count': len(result),
                    'results': result or [],
                })
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

    # Get Filters for sponsor payments
    @http.route('/portal/sys/payment_filters', methods=['GET'], auth='user', website=True, csrf=False)
    def get_sponsor_payments_filters(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_SY'})
        request.env.context = context
        try:
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

            # Return filters
            return json.dumps({
                'status': True,
                'filters': filters,
            })

        except Exception as e:
            _logger.error(str(e))
            message = str(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    #  Get sponsor financial records
    @http.route('/portal/sponsor/payments/page/<page>', methods=["GET"], auth='user', website=True, csrf=False)
    def get_sponsor_payments_records(self, page, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_SY'})
        request.env.context = context

        try:
            if page:
                try:
                    offset = (int(page) * PAGE_SIZE) - PAGE_SIZE
                    limit = PAGE_SIZE
                except Exception as e:
                    data = {'status': False, 'msg': _('URL Not Found')}
                    return json.dumps(data)      
            else:
                offset = 0
                limit=None

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
                # 'id',
                'name',
                'title',
                'date',
                # 'month',
                'amount',
            ]
            
            try:
                result = request.env[model].sudo().search(domain, offset=offset, limit=limit)
                result = props_fields(result, fields)
            except Exception as e:
                result = []

            count = len(result)
            next_page = None if count < PAGE_SIZE else (int(page) + 1)
            return json.dumps({
                    'status': True,
                    'count': count,
                    'results': result or [],
                    'next_page': next_page,
                })

        except Exception as e:
            _logger.error(str(e))
            message = str(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    #  Get sponsor arrears records
    @http.route('/portal/sponsor/arrears/page/<page>', methods=["GET"], auth='user', website=True, csrf=False)
    def get_sponsor_arrears_records(self, page, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_SY'})
        request.env.context = context

        try:
            if page:
                try:
                    offset = (int(page) * PAGE_SIZE) - PAGE_SIZE
                    limit = PAGE_SIZE
                except Exception as e:
                    data = {'status': False, 'msg': _('URL Not Found')}
                    return json.dumps(data)      
            else:
                offset = 0
                limit=None

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
                ['has_delay','=', True], 
            ]

            try:
                result = request.env[model].sudo().search(domain, offset=offset, limit=limit)
                result = props_fields(result, fields)
            except Exception as e:
                result = []

            count = len(result)
            next_page = None if count < PAGE_SIZE else (int(page) + 1)
            return json.dumps({
                    'status': True,
                    'count': count,
                    'results': result or [],
                    'next_page': next_page,
                })

        except Exception as e:
            _logger.error(str(e))
            message = str(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    #  Get sponsorships gifting record
    @http.route('/portal/sponsor/gifting/page/<page>', methods=["GET"], auth='user', website=True, csrf=False)
    def get_sponsorships_gifting_record(self, page, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_SY'})
        request.env.context = context
        try:
            if page:
                try:
                    offset = (int(page) * PAGE_SIZE) - PAGE_SIZE
                    limit = PAGE_SIZE
                except Exception as e:
                    data = {'status': False, 'msg': _('URL Not Found')}
                    return json.dumps(data)      
            else:
                offset = 0
                limit=None

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
                ['is_gift','=', 'yes'], 
            ]

            try:
                result = request.env[model].sudo().search(domain, offset=offset, limit=limit)
                result = props_fields(result, fields)
            except Exception as e:
                result = []

            count = len(result)
            next_page = None if count < PAGE_SIZE else (int(page) + 1)
            return json.dumps({
                    'status': True,
                    'count': count,
                    'results': result or [],
                    'next_page': next_page,
                })

        except Exception as e:
            _logger.error(str(e))
            message = str(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    # Get anothor Sponsor
    @http.route('/portal/sys/sponsor_search', methods=["GET"], auth='user', website=True, csrf=False)
    def get_anothor_sponsor(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_SY'})
        request.env.context = context

        try:

            mobile = kw.get('mobile', False)

            if not mobile:
                message = _('Missing mobile number')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            if re.match(SAUDI_MOBILE_PATTERN, str(mobile)) == None:
                message = _('Enter a valid Saudi mobile number')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            uid = request.session.uid
            user_data = self.get_user_sponsor_info(uid)
            sponsor_id = user_data["sponsor_id"]
            mobile1 = '966' + str(mobile).lstrip('0')
            mobile2 = '966' + str(sponsor_id.mobile).lstrip('0')
            if mobile1 == mobile2:
                message = _('Enter anothor sponsor mobile number')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            res = request.env['takaful.sponsor'].sudo().search([('mobile','=',mobile)], limit=1)
            if res:  
                dict_data = {
                    'id': res.id,
                    'name': res.name,
                }
            
                return json.dumps({
                    'status': True,
                    'sponsor': dict_data,
                })
            else:
                message = _('This sponsor does not exist')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

        except Exception as e:
            _logger.error(str(e))
            message = str(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    # Create a new Sponsorship
    @http.route('/portal/sponsor/sponsorships/create', methods=['POST'], auth='user', website=True, csrf=False)
    def do_create_sponsorship(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_SY'})
        request.env.context = context

        try:
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
                    message = _('Invalid orphan ids')
                    _logger.error(message)
                    data = {'status': False, 'msg': message}
                    return json.dumps(data)

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
                    message = _('invalid is_group value')
                    _logger.error(message)
                    data = {'status': False, 'msg': message}
                    return json.dumps(data)
               
                keys = all([benefit_type, need_limit, age_limit, benefit_count, payment_option, sponsorship_duration, month_amount])
            else:
                keys = all([is_gift, benefit_id, benefit_type, payment_option, sponsorship_duration, month_amount])

            if not keys:
                message = _('Some or all data is missing')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)
            
            if not benefit_type in ['orphan', 'widow']:
                message = _('Invalid Orphan or Widow')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            if not sponsorship_duration in ['temporary', 'permanent']:
                message = _('Invalid Sponsorship Period')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            if not sponsorship_class in ['fully', 'partial']:
                message = _('Invalid Sponsorship Class')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            if not payment_option in ['once', 'month']:
                message = _('Invalid Payment Recurrence')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            try:
                month_amount = float(month_amount)
            except Exception as e:
                message = _('Invalid Month Amount')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            # Get the default amount for sponsorship
            default_sponsorship = self.get_default_sponsorship_amount()

            if month_amount <=0:
                message = _('Invalid Month Amount')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            end_date = None
            if sponsorship_duration == "temporary":
                if months_number:
                    try:
                        months_number = int(months_number)
                    except Exception as e:
                        message = _('Invalid Months Number')
                        _logger.error(message)
                        data = {'status': False, 'msg': message}
                        return json.dumps(data)
                else:
                    message = _('Missing Months Number')
                    _logger.error(message)
                    data = {'status': False, 'msg': message}
                    return json.dumps(data)

                if months_number <=0:
                    message = _('Invalid Months Number')
                    _logger.error(message)
                    data = {'status': False, 'msg': message}
                    return json.dumps(data)

                sudoConf = request.env['ir.config_parameter'].sudo()
                allowed_days = int(sudoConf.get_param('odex_takaful_base.allowed_pay_days'))
                start_date = get_first_day_of_next_month()
                end_date = start_date + relativedelta(months=months_number, days=(start_date.day + allowed_days))

            # For Group
            if is_group == 'yes':
                try:
                    age_limit = int(age_limit)
                    need_limit = int(need_limit)
                except Exception as e:
                    message = _('Invalid value for ages limit or needs limit')
                    _logger.error(message)
                    data = {'status': False, 'msg': message}
                    return json.dumps(data)

                if age_limit <=0 or need_limit <=0:
                    message = _('Invalid value for ages limit or needs limit')
                    _logger.error(message)
                    data = {'status': False, 'msg': message}
                    return json.dumps(data)

                try:
                    benefit_count = int(benefit_count)
                except Exception as e:
                    message = _('Invalid Benefits count')
                    _logger.error(message)
                    data = {'status': False, 'msg': message}
                    return json.dumps(data)

                if benefit_count <= 1:
                    message = _('Invalid Benefits Count, At least Two Beneficiaries For Sponsorship Group')
                    _logger.error(message)
                    data = {'status': False, 'msg': message}
                    return json.dumps(data)

                domain = [('benefit_type','=', benefit_type), ('benefit_needs_percent','>', need_limit), ('age','>', age_limit)]
                benefits = request.env['grant.benefit'].sudo().search(domain, limit=benefit_count)
                if not benefits:
                    message = _('No Benefits found')
                    _logger.error(message)
                    data = {'status': False, 'msg': message}
                    return json.dumps(data)

                if len(benefits) == 1:
                    message = _('Matching Only One Benefit, At least Two Beneficiaries For Sponsorship Group')
                    _logger.error(message)
                    data = {'status': False, 'msg': message}
                    return json.dumps(data)

                if len(benefits) != benefit_count:
                    message = _('Mismatch in count, only found %s Benefits') % len(benefits)
                    _logger.error(message)
                    data = {'status': False, 'msg': message}
                    return json.dumps(data)

                # rec_sum = sum(benefits.filtered(lambda x: x).mapped('id'))
                if sponsorship_class == "fully":
                    total_sponsorship = sum(benefits.mapped('benefit_needs_value'))
                else:
                    total_sponsorship = default_sponsorship * benefit_count
                
                if month_amount < total_sponsorship:
                    message = _('Invalid Month Amount, At least %s') % total_sponsorship 
                    _logger.error(message)
                    data = {'status': False, 'msg': message}
                    return json.dumps(data)

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
                return json.dumps({
                    'status': True,
                    'msg': _('Sponsorship Created Successfully'),
                })

            if month_amount < default_sponsorship:
                message = _('Invalid Month Amount, At least %s') % default_sponsorship 
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            # For Person
            if not is_gift in ['yes', 'no']:
                message = _('Gift value is invalid or missing')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)
                
            try:
                benefit_id = int(benefit_id)
            except Exception as e:
                message = _('Invalid or Missing Id for Benefit')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            benefit = request.env['grant.benefit'].sudo().search([('id','=', benefit_id)], limit=1)
            if not benefit:
                message = _('This Benefit does not exist')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            if is_gift == 'yes':
                if sponsorship_duration == "temporary": 
                    if months_number < 12:
                        message = _('At Least 12 Months for Gift')
                        _logger.error(message)
                        data = {'status': False, 'msg': message}
                        return json.dumps(data)

                if gifter_id:
                    try:
                        gifter_id = int(gifter_id)
                    except Exception as e:
                        message = _('Invalid Id for Gifter')
                        _logger.error(message)
                        data = {'status': False, 'msg': message}
                        return json.dumps(data)

                    gifter = request.env['takaful.sponsor'].sudo().search([('id', '=', gifter_id)], limit=1)
                    
                    if not gifter:
                        message = _('Gifter does not exist for this Id')
                        _logger.error(message)
                        data = {'status': False, 'msg': message}
                        return json.dumps(data)

                    gifter_name = gifter.name
                    gifter_mobile = gifter.mobile
                    gifter_id = gifter.id
                
                if not gifter_name:
                    message = _('Missing Gifter Name')
                    _logger.error(message)
                    data = {'status': False, 'msg': message}
                    return json.dumps(data)

                if not gifter_mobile:
                    message = _('Missing Gifter Mobile Number')
                    error = 'missing_data'
                    _logger.error(message)
                    data = {'status': False, 'msg': message}
                    return json.dumps(data)

                if not gifter_id and (gifter_name and gifter_mobile):
                    gifter_id = False
                    if re.match(SAUDI_MOBILE_PATTERN, str(gifter_mobile)) == None:
                        message = _('Enter a valid Saudi mobile number')
                        _logger.error(message)
                        data = {'status': False, 'msg': message}
                        return json.dumps(data)

            if benefit_type == 'widow':
                if not with_orphan in ['yes', 'no']:
                    message = _('Including Orphans value is invalid or missing')
                    _logger.error(message)
                    data = {'status': False, 'msg': message}
                    return json.dumps(data)

                if with_orphan == 'yes' and orphan_value:
                    try:
                        orphan_value = float(orphan_value)
                    except Exception as e:
                        message = _('Invalid orphan value')
                        _logger.error(message)
                        data = {'status': False, 'msg': message}
                        return json.dumps(data)

                    if orphan_value <= 0:
                        message = _('Invalid orphan value')
                        _logger.error(message)
                        data = {'status': False, 'msg': message}
                        return json.dumps(data)

                    if sponsorship_class == "fully":
                        default_sponsorship = max(benefits.mapped('benefit_needs_value'))

                    if orphan_value < default_sponsorship:
                        message = _('Invalid orphan value, At least %s') % default_sponsorship 
                        _logger.error(message)
                        data = {'status': False, 'msg': message}
                        return json.dumps(data)

                elif with_orphan == 'yes' and not orphan_value:
                    message = _('Missing orphan value')
                    _logger.error(message)
                    data = {'status': False, 'msg': message}
                    return json.dumps(data)

                benefits = request.env['grant.benefit'].sudo().search([('id','in', orphan_ids)])
                if with_orphan == 'yes' and not benefits:
                    message = _('Invalid or missing orphan ids')
                    _logger.error(message)
                    data = {'status': False, 'msg': message}
                    return json.dumps(data)

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
                main_sponsorship.sudo().action_confirm_data()
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
                main_sponsorship.sudo().action_confirm_data()

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
                    orphan_sponsorship.sudo().action_confirm_data()
                    main_sponsorship.sudo().write({'with_orphan_ids': [(4, ben.id)]})
                main_sponsorship.sudo().write({'is_widow_orphan': True})
                main_sponsorship.sudo().action_confirm_data()

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
                    orphan_sponsorship.sudo().action_confirm_data()
                main_sponsorship.sudo().write({'is_widow_orphan': True})
                main_sponsorship.sudo().action_confirm_data()
            
            return json.dumps({
                'status': True,
                'msg': _('Sponsorship Created Successfully'),
            })

        except Exception as e:
            _logger.error(str(e))
            message = str(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)
    
    # Create a paying_demo
    @http.route('/portal/sponsor/paying_demo/save', methods=['POST'], auth='user', website=True, csrf=False)
    def do_save_paying_demo(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_SY'})
        request.env.context = context
        
        try:
            sponsorship_id = kw.get('sponsorship_id', False)
            pay_months = kw.get('pay_months', 1)
            pay_title = kw.get('pay_title', _('Sponsorship Payment'))

            benefit_id = kw.get('benefit_id', False)
            need_id = kw.get('need_id', False)
            operation_type = kw.get('operation_type', False)
            amount = kw.get('amount', False)
            note = kw.get('message', '')
            benefit_ids = []

            name = ''

            if not operation_type in ['sponsorship', 'gift', 'contribution']:
                message = _('Invalid value for %s ') % 'operation_type'
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            if operation_type == 'sponsorship':
                keys = all([sponsorship_id, pay_months, pay_title, amount])

            elif operation_type == 'gift':
                keys = all([benefit_id, amount])

            elif operation_type == 'contribution':
                keys = all([need_id, amount])

            if not keys:
                message = _('Some or all data is missing')
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)

            try:
                amount = float(amount)
            except Exception as e:
                message = _('Invalid value for %s ') % 'amount'
                _logger.error(message)
                data = {'status': False, 'msg': message}
                return json.dumps(data)
            
            # Get Sponsor Info...
            uid = request.session.uid
            user_data = self.get_user_sponsor_info(uid)
            sponsor_id = user_data["sponsor_id"]

            # For Sponsorship
            if operation_type == 'sponsorship':
                try:
                    sponsorship_id = int(sponsorship_id)
                except Exception as e:
                    message = _('Invalid Id for Sponsorship')
                    _logger.error(message)
                    data = {'status': False, 'msg': message}
                    return json.dumps(data)

                sponsorship = request.env['takaful.sponsorship'].sudo().search([('id','=',sponsorship_id), ('sponsor_id','=',sponsor_id.id)], limit=1)
                if not sponsorship:
                    message = _('This Sponsorship does not exist in the system')
                    _logger.error(message)
                    data = {'status': False, 'msg': message}
                    return json.dumps(data)

                if sponsorship.state == "canceled":
                    message = _('This Sponsorship is already canceled')
                    _logger.error(message)
                    data = {'status': False, 'msg': message}
                    return json.dumps(data)

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

                # Return OK
                return json.dumps({
                    'status': True,
                    'msg': _('Paid Successfully')
                })

            # For other
            if operation_type == 'gift':
                try:
                    benefit_id = int(benefit_id)
                except Exception as e:
                    message = _('Invalid value for %s ') % 'benefit_id'
                    _logger.error(message)
                    data = {'status': False, 'msg': message}
                    return json.dumps(data)

                benefit = request.env['grant.benefit'].sudo().search([('id','=', benefit_id)], limit=1)
                if not benefit:
                    message = _('This Benefit does not exist')
                    _logger.error(message)
                    data = {'status': False, 'msg': message}
                    return json.dumps(data)

                title = benefit.name

            elif operation_type == 'contribution':
                try:
                    need_id = int(need_id)
                except Exception as e:
                    message = _('Invalid value for %s ') % 'need_id'
                    _logger.error(message)
                    data = {'status': False, 'msg': message}
                    return json.dumps(data)

                need_type = request.env['benefits.needs'].sudo().search([('id','=', need_id)], limit=1)
                if not need_type:
                    message = _('This Need does not exist')
                    _logger.error(message)
                    data = {'status': False, 'msg': message}
                    return json.dumps(data)
                
                # if benefit_id and need_type.benefit_id and need_type.benefit_id != benefit_id:
                #     message = _('Mismatch Need for Benefit')
                #     error = 'invalid_data'
                #     _logger.error(message)
                #     return error_response(400, error, message)

                # Get info
                if need_type.benefit_ids:
                    benefit_ids = need_type.benefit_ids.ids
                elif need_type.benefit_id:
                    benefit_id = need_type.benefit_id.id
                name = need_type.name

            if operation_type == 'gift':
                name = u'إهداء مالي'
                contribution = request.env['takaful.contribution'].sudo().create({
                    'name': name,
                    'benefit_id': benefit_id,
                    'sponsor_id': sponsor_id.id,
                    'operation_type': operation_type,
                    'amount': amount,
                    'note': note
                })
                name = u'سداد هدية مالية'
            
            elif operation_type == 'contribution':
                contribution = request.env['takaful.contribution'].sudo().create({
                    'name': name,
                    'need_id': need_id,
                    'sponsor_id': sponsor_id.id,
                    'operation_type': operation_type,
                    'amount': amount,
                    'note': note
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
            return json.dumps({
                'status': True,
                'msg': _('Paid Successfully')
            })

        except Exception as e:
            _logger.error(str(e))
            message = str(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

        
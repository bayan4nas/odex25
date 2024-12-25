# -*- coding: utf-8 -*-
from odoo.addons.web.controllers.main import serialize_exception
import re
from odoo.tools.translate import _
from odoo.http import request
import base64
import json
from odoo import http, modules
from odoo.addons.takaful_rest_api.controllers.main import *

_logger = logging.getLogger(__name__)


class BenefitPortal(http.Controller):

    @staticmethod
    def get_server_error(error):
        x = False
        if len(error.args) == 2:
            x, y = error.args
            x = re.sub('\n', '', x)
        else:
            x = error.args
        text = (_("Contact Admin"))
        message = "%s, %s" % (x, text)
        return message

    @staticmethod
    def get_attachment(attachment_id):
        attachment = request.env['ir.attachment'].sudo().search(
            [('id', '=', attachment_id)])
        if attachment:
            result = ([attachment.id, attachment.name])
            return result

    @staticmethod
    def get_validation_error(field_id):
        filed = field_id.replace('_', ' ')
        result = ({'status': False, 'msg': (
            _('Enter The ' + filed)), 'data': {'field': field_id}})
        return result

    @staticmethod
    def get_validation_image(FileStorage):
        FileExtension = FileStorage.filename.split('.')[-1].lower()
        ALLOWED_IMAGE_EXTENSIONS = ['jpg', 'pdf', 'png', 'jpeg']
        if FileExtension not in ALLOWED_IMAGE_EXTENSIONS:
            result = {'status': False, 'message': _(
                "Only allowed files with extension: %s" % (
                    ",".join(ALLOWED_IMAGE_EXTENSIONS)))}
            return result
        else:
            pass

    ####################### Get function #####################
    # Types
    @http.route('/benefit/types/<key>', methods=["GET"], type='http', auth='public')
    def get_benefit_types_data(self, key):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context
        try:
            model = []
            if 'items' in key:
                model.append('benefit.housing.rooms.items')
            if 'insurance' in key:
                model.append('insurance.type')
            if 'insurance_company' in key:
                model.append('insurance.company')
            if 'specialization' in key:
                model.append('specialization.specialization')
            if 'bank' in key:
                model.append('res.bank')
            if 'sport' in key:
                model.append('sport.type')
            if 'labor' in key:
                model.append('domestic.labor')
            if 'housing' in key:
                # cloth.size
                model.append('benefit.housing')
            if 'uom' in key:
                model.append('product.uom')
            if 'cloth_size' in key:
                model.append('cloth.size')
            if 'cloth_type' in key:
                model.append('cloth.type')
            if 'associations' in key:
                # Todo add filter in other.associations
                model.append('other.associations')
            if 'cat_need' in key:
                # Todo add filter in needs.categories
                model.append('needs.categories')
            if model:
                main_obj = {}
                results = []
                # dict_obj = {}
                for k in model:
                    result = request.env[k].sudo().search([])
                    name = k.replace('.', '_')
                    if result:
                        results.append(
                            ({name: [{'id': s.id, 'name': s.name} for s in result]}))
                    else:
                        results.append(({name: False}))
                main_obj['result'] = results
                # results.append(dict_obj)
                return json.dumps(main_obj)
        except Exception as e:
            _logger.error(str(e))
            message = self.get_server_error(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    # Benefit Profile
    @http.route('/benefit/profile', auth='public', website=True, csrf=False, methods=['GET'])
    # TODO : ADD payment history in benefit Screen
    def get_benefit(self):
        try:
            benefit = request.env['grant.benefit'].sudo().search(
                [('user_id', '=', request.session.uid)])
            print(benefit)
            for rec in benefit:
                benefit = rec
            li = ['name', 'id_number', 'id_expiry', 'gender', 'marital_status', 'birth_date', 'family_id', 'bank_id',
                  'iban',
                  'email', 'phone', 'country_id', 'city_id', 'street', 'location', 'id_number_attach', 'iban_attach']
            follower = request.env['grant.benefit'].sudo().search(
                [('responsible_id', '=', benefit.id)])
            lif = ['name', 'gender', 'responsible', 'birth_date',
                   'id_number', 'id_number_attach', 'status']
            benefit_need = request.env['benefits.needs'].sudo().search(
                [('benefit_id', '=', benefit.id)])
            lneed = ['name', 'category_name', 'completion_ratio', 'state']
            if benefit:
                follower_list = []
                for followers in follower.read(lif):
                    follower_list.append(followers)
                benefit_needs = []
                for need in benefit_need.read(lneed):
                    benefit_needs.append(need)
                dicts = {}
                keys = []
                values = []
                for i in benefit.read(li):
                    for k, v in i.items():
                        if k == 'id_number_attach':
                            keys.append(k)
                            values.append(self.get_attachment(v))
                        else:
                            keys.append(k)
                            values.append(v)

                keys.append('follower')
                values.append(follower_list)
                keys.append('needs')
                values.append(benefit_needs)
                for i in keys:
                    dicts[i] = values[keys.index(i)]
                data = {'status': True, 'msg': (
                    _('Benefit Found')), 'data': dicts}
            else:
                data = {'status': False, 'msg': (
                    _('Benefit not Found')), 'data': False}
            return json.dumps(data)

        except Exception as e:
            import traceback
            print(traceback.format_exc())
            _logger.error(str(e))
            message = self.get_server_error(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    # Verify the address and the residential unit and add the beneficiary to it if it exists
    @http.route('/benefit/check_address', auth='public', website=True, csrf=False, methods=['GET'])
    def get_address_id(self, housing_number=False, **kw):
        li = ['city_id', 'block', 'street', 'house_number', 'floor', 'rent_amount', 'housing_type', 'property_type',
              'lat', 'lon', 'rooms_number', 'water_bill_account_number', 'electricity_bill_account_number']
        try:
            if not housing_number:
                data = {'status': False, 'msg': (
                    _('Enter Your Residential unit Number')), 'data': {}}
            else:
                address = request.env['benefit.housing'].sudo().search(
                    [('housing_number', '=', housing_number)])
                # for addres in address:
                if address:
                    data = {'status': True, 'msg': (_('You have address')),
                            'data': address.read(li)}
                else:
                    data = {'status': True, 'msg': (_('No address')),
                            'data': {}}
            return json.dumps(data)
        except Exception as e:
            _logger.error(str(e))
            message = self.get_server_error(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    @http.route('/benefit/all_support', auth='public', website=True, csrf=False, methods=['GET'])
    def get_all_support(self):
        try:
            benefit = request.env['grant.benefit'].sudo().search(
                [('user_id', '=', request.session.uid)])
            li = ['name.name', 'follower_type',
                  'birth_date', 'gender', 'name.responsible']
            if benefit:
                benefits = request.env['benefit.followers'].sudo().search(
                    [('benefit_id', '=', benefit.id)])
                if benefits:
                    data = {'status': True, 'msg': (
                        _('Records Found ')), 'data': benefits.read(li)}
                else:
                    data = {'status': False, 'msg': (
                        _('Records Not Found ')), 'data': {}}
            else:
                data = {'status': False, 'msg': (
                    _('Records Not Found ')), 'data': {}}
            return json.dumps(data)
        except Exception as e:
            _logger.error(str(e))
            message = self.get_server_error(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    ####################### POST function #####################

    # complete Benefit Account
    @http.route('/benefit/complete_benefit', auth='public', website=True, methods=['GET', 'POST'], csrf=False)
    def get_complete_benefit(self, step, **kw):
        
        benefit_id = request.env['grant.benefit'].sudo().search(
            [('user_id', '=', request.session.uid)], limit=1)
        if not benefit_id:
            error =  {'status': False, 'message': _("Not Found benefit ")}
            return json.dumps(error)
        step = int(step)        
        li = [
            # first step values
            'id', 'job_position', 'job_company', 'id_number_attach', 'id_expiry', 'marital_status', 'bank_id',
            'iban', 'iban_attach', 'name_in_bank', 'followers_total', 'followers_out_total', 'instrument_number',
            'instrument_attach',

            # second step values
            'city_id', 'house_number', 'block', 'street', 'floor', 'housing_type', 'property_type',
            'lat', 'lon', 'house_images', 'rooms_number', 'water_bill_account_number', 'water_bill_account_attach',
            'electricity_bill_account_number', 'electricity_bill_account_attach',

            #   step 3 values
            'salary_type', 'salary_amount', 'salary_attach', 'isAssociated', 'associations_id', 'support_amount', 'support_description',

            #   step 4 values
            'education_status', 'is_want_education', 'nearest_literacy_school', 'literacy_school_note', 'learning_expense',
            'education_level', 'classroom', 'educational_institution_information', 'educational_institution_attach',
            'specialization_ids', 'study_document_attached', 'case_study', 'graduation_status', 'graduation_date',
            'interruption_date', 'reasons_for_interruption', 'acadimec_regsteration_attached', 'Transcript_attached',
            'average', 'is_quran_memorize', 'quran_memorize_name', 'number_parts',

            #   step 5 values
            'cloth_type', 'cloth_size', 'is_diseases', 'diseases_type', 'treatment_used', 'treatment_amount',
            'is_treatment_amount_country', 'treatment_amount_country_Monthly', 'treatment_amount_country_description',
            'treatment_amount_country_attach', 'is_disability', 'disability_type', 'disability_accessories',
            'disability_attach', 'disability_amount', 'weight', 'height',

            # step 6 values
            'is_insurance', 'insurance_type', 'insurance_company', 'insurance_amount', 'insurance_attach',

            #   step 7 values
            'is_sport', 'sport_type', 'sport_time', 'sport_club', 'subscription', 'sportswear', 'is_widows', 'is_divorcee']
        benefit = ''
        values = {}
        benefit = {}
        followers = {}
        expenses = {}
        salary = {}
        associations = {}
        sport = {}
        try:
            if step == 1:
                fields = [
                    'id', 'job_position', 'job_company', 'id_number_attach', 'id_expiry', 'marital_status', 'bank_id',
                    'iban', 'iban_attach', 'name_in_bank', 'followers_total', 'followers_out_total', 'instrument_number',
                    'instrument_attach']
                for field in fields:
                    if not kw.get(field, False):
                        error = self.get_validation_error(field)
                        return json.dumps(error)
                values['function'] = kw.get('job_position')
            if step == 2:
                # 2 Housing
                if not kw.get('house_number', False):
                    error = self.get_validation_error('house_number')
                    return json.dumps(error)
                #    A-Check if housing is available
                address = request.env['benefit.housing'].sudo().search(
                    [('housing_number', '=', kw.get('house_number'))])
                #    B- if not housing Create an address and the housing unit
                
                if not address:
                    values_address = {}
                    address = request.env['benefit.housing']
                    fields = [
                        'city_id', 'house_number', 'block', 'street',
                        'floor', 'housing_type', 'property_type',
                        'lat','lon', 'house_images', 'rooms_number',
                        'water_bill_account_number',
                        'water_bill_account_attach',
                        'electricity_bill_account_number',
                        'electricity_bill_account_attach',
                        ]

                    attachments = [
                        'water_bill_account_attach',
                        'electricity_bill_account_attach'
                    ]
                    for field in fields:
                        if not kw.get(field, False):
                            error = self.get_validation_error(field)
                            return json.dumps(error)
                    for attach in attachments:
                        if kw.get(attach, False):
                            error = self.get_validation_image(
                                kw.get(attach, False))
                            if error:
                                return json.dumps(error)
                    house_images = ['image', 'image_1',
                                    'image_2', 'image_3', 'image_4']
                    index = 0
                    for image in list(http.request.httprequest.files.getlist('house_images')):
                        
                        error = self.get_validation_image(image)
                        if error:
                            return json.dumps(error)
                        x= house_images[index]
                        values_address[x] = ""
                        values_address[x] = base64.b64encode(image.read())
                        index = index + 1
                    if index < 1 :
                        error =  {'status': False, 'message': _("Please Upload More Than One Image")}
                        return json.dumps(error)
                    for field_name, field_value in kw.items():
                        if field_name not in attachments or field_name not in ['house_images']:
                            values_address[field_name] = field_value
                    for fname, fvalue in http.request.httprequest.files.items():
                        if fvalue:
                            file = fvalue.read()
                            if len(file) > 0:
                                values_address[fname] = base64.b64encode(file)
                    
                    values_address['housing_number'] = values_address.pop('house_number')
                    address = address.sudo().create(values_address)
                    # address.sudo().write({'domestic_labor_ids': [(6, 0, [1, 2])]})  # Todo
                    address.sudo()._compute_get_name()
                #    c- Add the beneficiary to the housing unit by link the ID
                values['housing_id'] = address.id            
            if step == 3:
                fields = ['salary_type', 'salary_amount', 'salary_attach',
                          'isAssociated', 'associations_id',
                          'support_amount', 'support_description']
                for field in fields:
                    if not kw.get(field, False):
                        error = self.get_validation_error(field)
                        return json.dumps(error)
                # salary
                salary['benefit_id'] = benefit_id.id
                salary['salary_type'] = kw.get('salary_type')
                salary['salary_amount'] = kw.get('salary_amount')
                
                for fname , file in http.request.httprequest.files.items():
                    salary['salary_attach'] = base64.b64encode(file.read())
                request.env['salary.line'].sudo().create(salary)
                # associations
                isAssociated = kw.get('isAssociated', False)
                if isAssociated:
                    associations['benefit_id'] = benefit_id.id
                    associations['associations_ids'] = kw.get('associations_id')
                    associations['support_amount'] = kw.get('support_amount')
                    associations['associations_description'] = kw.get('support_description')
                    request.env['associations.line'].sudo().create(associations)
                values['is_other_associations'] = isAssociated
            if step == 4:
                # Educational
                fields = ['education_status']
                for field in fields:
                    if not kw.get(field, False):
                        error = self.get_validation_error(field)
                        return json.dumps(error)
                if kw.get('education_status', False) == 'illiterate':
                    if not kw.get('is_want_education', False):
                        return json.dumps({'status': False, 'msg': (_('is_want_education')), 'data': {}})
                # Educational Level if education_status == educated
                if kw.get('education_status', False) == 'educated':
                    if not kw.get('education_level', False):
                        return json.dumps({'status': False, 'msg': (_('education_level')), 'data': {}})
                    if not kw.get('classroom', False):
                        return json.dumps({'status': False, 'msg': (_('classroom')), 'data': {}})
                    if not kw.get('specialization_ids', False):
                        return json.dumps({'status': False, 'msg': (_('specialization')), 'data': {}})
                    if not kw.get('educational_institution_information', False):
                        return json.dumps(
                            {'status': False, 'msg': (_('educational_institution_information')), 'data': {}})
                    if not kw.get('case_study', False):
                        return json.dumps({'status': False, 'msg': (_('case_study')), 'data': {}})
                    if not kw.get('graduation_status', False):
                        return json.dumps({'status': False, 'msg': (_('graduation_status')), 'data': {}})
                    if kw.get('graduation_status', False) == 'graduated':
                        if not kw.get('graduation_date', False):
                            return json.dumps({'status': False, 'msg': (_('graduation_date')), 'data': {}})
                    if kw.get('graduation_status', False) == 'intermittent':
                        if not kw.get('reasons_for_interruption', False):
                            return json.dumps({'status': False, 'msg': (_('reasons_for_interruption')), 'data': {}})
                        if not kw.get('interruption_date', False):
                            return json.dumps({'status': False, 'msg': (_('interruption_date')), 'data': {}})
                        if not kw.get('study_document_attached', False):
                            return json.dumps({'status': False, 'msg': (_('study_document_attached')), 'data': {}})
                        if not kw.get('acadimec_regsteration_attached', False):
                            return json.dumps(
                                {'status': False, 'msg': (_('acadimec_regsteration_attached')), 'data': {}})
                        if not kw.get('Transcript_attached', False):
                            return json.dumps({'status': False, 'msg': (_('Transcript_attached')), 'data': {}})
            if step == 5:
                # health information#
                if kw.get('is_diseases', False) == 'true':
                    if not kw.get('diseases_type', False):
                        return json.dumps({'status': False, 'msg': (_('diseases_type')), 'data': {}})
                    if not kw.get('treatment_used', False):
                        return json.dumps({'status': False, 'msg': (_('treatment_used')), 'data': {}})
                    if not kw.get('treatment_amount', False):
                        return json.dumps({'status': False, 'msg': (_('treatment_amount')), 'data': {}})
                    if kw.get('treatment_amount_country', False):
                        if not kw.get('treatment_amount_country_Monthly', False):
                            return json.dumps(
                                {'status': False, 'msg': (_('treatment_amount_country_Monthly')), 'data': {}})
                        if not kw.get('treatment_amount_country_description', False):
                            return json.dumps(
                                {'status': False, 'msg': (_('treatment_amount_country_description')), 'data': {}})
                        if not kw.get('treatment_amount_country_attach', False):
                            return json.dumps(
                                {'status': False, 'msg': (_('treatment_amount_country_attach')), 'data': {}})
                # disability
                if kw.get('is_disability', False):
                    if not kw.get('disability_type', False):
                        return json.dumps({'status': False, 'msg': (_('diseases_type')), 'data': {}})
                    if not kw.get('disability_accessories'
                                  '', False):
                        return json.dumps({'status': False, 'msg': (_('treatment_used')), 'data': {}})
                    if not kw.get('treatment_amount', False):
                        return json.dumps({'status': False, 'msg': (_('treatment_amount')), 'data': {}})
                    if kw.get('treatment_amount_country', False):
                        if not kw.get('treatment_amount_country_Monthly', False):
                            return json.dumps(
                                {'status': False, 'msg': (_('treatment_amount_country_Monthly')), 'data': {}})
                        if not kw.get('treatment_amount_country_description', False):
                            return json.dumps(
                                {'status': False, 'msg': (_('treatment_amount_country_description')), 'data': {}})
                        if not kw.get('treatment_amount_country_attach', False):
                            return json.dumps(
                                {'status': False, 'msg': (_('treatment_amount_country_attach')), 'data': {}})
            if step == 6:
                if kw.get('is_insurance', False) == 'true':
                    if not kw.get('insurance_type', False):
                        return json.dumps({'status': False, 'msg': (_('insurance_type')), 'data': {}})
                    if not kw.get('insurance_company', False):
                        return json.dumps({'status': False, 'msg': (_('insurance_company')), 'data': {}})
                    if not kw.get('insurance_amount', False):
                        return json.dumps({'status': False, 'msg': (_('insurance_amount')), 'data': {}})
                    if not kw.get('insurance_attach', False):
                        return json.dumps({'status': False, 'msg': (_('insurance_attach')), 'data': {}})
            if step == 7:
                sport['benefit_id'] = benefit_id.id 
                sport['sport_type'] = kw.get('sport_type')
                sport['sport_time'] = kw.get('sport_time')
                sport['sport_club'] = kw.get('sport_club')
                sport['subscription'] = kw.get('sport_club')
                sport['sportswear'] = kw.get('sport_club')
                # sport['Subtype'] = kw.get('Subtype')
                # sport['sport_amount'] = kw.get('sport_amount')
                # sport['sport_attendance'] = kw.get('sport_attendance')
                # sport['sport_clothing'] = kw.get('sport_clothing')
                # sport['sport_equipment'] = kw.get('sport_equipment')
                request.env['sport.line'].sudo().create(sport)

            for field_name, field_value in kw.items():
                if field_name not in ['study_document_attached','support_description', 'salary_attach', 'salary_amount', 'salary_type', 'support_amount', 'associations_id', 'isAssociated','house_images', 'acadimec_regsteration_attached', 'Transcript_attached']:
                    values[field_name] = field_value
            for fname, fvalue in http.request.httprequest.files.items():
                if fname not in ['house_images','salary_attach']:
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
                        # if fname == 'id_number_attach' :
                        values[fname] = [(4,attachment_id.id)]
                    # else:
                    #     values[fname] = datas

            if step == 7:
                values['state'] = 'waiting_approve'
            if step <= 7 :
                values['step'] = step + 1
                print("benefit_id8888888888",benefit_id , type(benefit_id))
                # import pprint
                print(values)
                benefit = benefit_id.sudo().write(values)
            data = {'status': True, 'msg': (
                _('data')), 'data': benefit_id.sudo().read([])}
            return json.dumps(data)
        except Exception as e:
            import traceback
            print(traceback.format_exc())
            _logger.error(str(e))
            message = self.get_server_error(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    @http.route('/benefit/create_support', auth='public', website=True, csrf=False, methods=['POST'])
    def get_create_support(self, **kw):
        values = {}
        message = ""
        try:
            check_id = request.env['grant.benefit'].sudo().search(
                [('id_number', '=', kw.get('id_number'))])
            parent = request.env['grant.benefit'].sudo().search(
                [('user_id', '=', request.session.uid)])
            if not check_id:
                required_filed = ['name', 'relation',
                                  'gender', 'birth_date', 'id_number_attach']
                for filed in required_filed:
                    if not kw.get(filed, False):
                        error = self.get_validation_error(filed)
                        return json.dumps(error)
                if not kw.get('id_number', False) or kw.get('id_number', False) == 0:
                    return json.dumps({'status': False, 'msg': (_('Enter Id Number')), 'data': {}})
                for field_name, field_value in kw.items():
                    if field_name != "id_number_attach":
                        values[field_name] = field_value
                # 
                for fname, fvalue in http.request.httprequest.files.items():
                    if fvalue:
                        file = fvalue.read()
                        if len(file) > 0:
                            values[fname] = base64.b64encode(file)
                if kw.get('benefit_type') == 'orphan':
                    values['benefit_type'] = 'orphan'
                if kw.get('benefit_type') == 'widow':
                    values['benefit_type'] = 'widow'
                if kw.get('benefit_type') == 'other':
                    values['benefit_type'] = 'benefit'
                values['responsible'] = kw.get('relation')
                # 
                values['responsible_id'] = parent.id
                # is_live_with_family
                if kw.get('is_live_with_family'):
                    values['housing_id'] = parent.housing_id.id
                for fname, fvalue in http.request.httprequest.files.items():
                    values[fname] = base64.b64encode(fvalue.read())
                benefit = request.env['grant.benefit'].sudo().create(values)
                if benefit:
                    data = {'status': True, 'msg': (
                        _('Record created ')), 'data': {}}
                else:
                    data = {'status': False, 'msg': (
                        _('Record Not created ')), 'data': {}}
                return json.dumps(data)
            else:
                return json.dumps({'status': False, 'msg': (_('Id Number Duplicated ')), 'data': {}})
        except Exception as e:
            _logger.error(str(e))
            message = self.get_server_error(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    @http.route('/benefit/profile/update', auth='public', website=True, csrf=False, methods=['PUT'])
    def write_benefit_profile(self, **kw):
        try:
            benefit = request.env['grant.benefit'].sudo().search(
                [('user_id', '=', request.session.uid)])
            values = {}
            li = ['name', 'id_number', 'id_expiry', 'gender', 'marital_status', 'birth_date', 'family_id', 'bank_id',
                  'iban',
                  'email', 'phone', 'country_id', 'city_id', 'street', 'location', 'id_number_attach', 'iban_attach']
            if benefit:
                # if benefit.state in ['edit_info']: Todo
                for field_name, field_value in kw.items():
                    if field_name != "id_number_attach":
                        values[field_name] = field_value
                for fname, fvalue in http.request.httprequest.files.items():
                    if fvalue:
                        file = fvalue.read()
                        if len(file) > 0:
                            values[fname] = base64.b64encode(file)
                benefit.write(values)
                data = {'status': True, 'msg': (
                    _('Benefit Found')), 'data': benefit.read(li)}
            else:
                data = {'status': False, 'msg': (
                    _('Benefit not Found')), 'data': False}
            return json.dumps(data)

        except Exception as e:
            _logger.error(str(e))
            message = self.get_server_error(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    @http.route('/benefit/support/update', auth='public', website=True, csrf=False, methods=['PUT'])
    def write_benefit_support(self, id, **kw):
        # id of  record
        message = ""
        try:
            benefit = request.env['grant.benefit'].sudo().browse(int(id))
            values = {}
            li = ['f_name', 'g_name', 'parent', 'family', 'id_number', 'birth_date', 'age',
                  'gender', 'id', 'institution_id', 'partner_id', 'relation', 'state']
            if benefit:
                if benefit.state in ['edit_info', 'draft']:
                    for field_name, field_value in kw.items():
                        if field_name != "id_number_attach":
                            values[field_name] = field_value
                    for fname, fvalue in http.request.httprequest.files.items():
                        if fvalue:
                            file = fvalue.read()
                            if len(file) > 0:
                                values[fname] = base64.b64encode(file)
                    benefit.write(values)
                    if benefit.state == 'edit_info':
                        benefit.action_finish_edit()
                    data = {'status': True, 'msg': (_('Benefit Account Updated successfully')),
                            'data': benefit.read(li)}
                else:
                    data = {'status': False, 'msg': (
                        _('You Can Not Update Benefit Account ')), 'data': {}}
            else:
                data = {'status': False, 'msg': (
                    _('Benefit Account Not Found ')), 'data': {}}
            return json.dumps(data)
        except Exception as e:
            _logger.error(str(e))
            message = self.get_server_error(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    @http.route('/benefit/request_need', auth='public', website=True, csrf=False, methods=['POST'])
    def get_request_need(self, **kw):
        values = {}
        try:
            benefit_ids = request.env['grant.benefit'].sudo().search(
                [('user_id', '=', request.session.uid)])
            benefit_id = False
            for id in benefit_ids:
                benefit_id = id
            required_filed = ['need_category', 'description',
                              'f_amount', 'need_status', 'need_type_ids', 'need_attach']
            for filed in required_filed:
                if not kw.get(filed, False):
                    error = self.get_validation_error(filed)
                    return json.dumps(error)
            for field_name, field_value in kw.items():
                if field_name != "need_attach":
                    values[field_name] = field_value
            # TO DO
            for fname, fvalue in http.request.httprequest.files.items():
                values[fname] = base64.b64encode(fvalue.read())
            values['name'] = ("حوجة اليتيم " + benefit_id.name if benefit_id else '')  # TODO
            values['benefit_id'] = benefit_id.id if benefit_id else False
            values['need_type_ids'] = [(6, 0, [1])]  # TODO
            values['city_id'] = benefit_id.city_id.id if benefit_id else False
            values['benefit_need_type'] = 'special'
            values['date'] = datetime.date.today()
            benefit_needs = request.env['benefits.needs'].sudo().create(values)
            
            
            if benefit_needs:
                data = {'status': True, 'msg': (
                    _('Record created ')), 'data': {}}
            else:
                data = {'status': False, 'msg': (
                    _('Record Not created ')), 'data': {}}
            return json.dumps(data)
        except Exception as e:
            _logger.error(str(e))
            message = self.get_server_error(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    @http.route('/portal/attachment', type='http', auth="public")
    @serialize_exception
    def download_documents(self, id, field, filename=None, **kw):
        try:
            model = 'grant.benefit'
            res = request.env[model].sudo().browse(int(id))
            if not filename:
                filename = '%s_%s' % (model.replace('.', '_'), id)
                x = str(field)
                file = res.read([str(x)])
                if file[0][x]:
                    fields = file[0][x]
                    filecontent = base64.b64decode(fields or '')
                    status, headers, content = request.env['ir.http'].binary_content(
                        model=model,
                        id=int(id),
                        field="%s" % (field),
                        default_mimetype='application/octet-stream',
                        env=request.env
                    )
                    mimetype = dict(headers).get('Content-Type')

                    return request.make_response(filecontent,
                                                 [('Content-Type', mimetype),
                                                  ('Content-Disposition', "attachment")])
                else:
                    return json.dumps({'status': False, 'msg': (_("No Attachment"))})
        except Exception as e:
            _logger.error(str(e))
            message = self.get_server_error(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    @http.route('/benefit/get_need_by_cat/<id>', auth='public', website=True, csrf=False, methods=['GET'])
    def get_need_by_cat(self, id, **kw):
        try:
            result = []
            needs_categories = request.env['needs.categories'].sudo().search([
                ('id', '=', int(id))])
            for val in needs_categories.product_ids:
                result.append(
                    {
                        "id": val.id,
                        "name": val.name
                    }
                )

            if result:
                data = {'status': True, 'msg': (
                    _('Record Found ')), 'data': result}
            else:
                data = {'status': False, 'msg': (
                    _('Record Not Found ')), 'data': {}}
            return json.dumps(data)
        except Exception as e:
            _logger.error(str(e))
            message = self.get_server_error(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    @http.route('/benefit/get_benefit_expenses/', auth='public', website=True, csrf=False, methods=['GET'])
    def get_benefit_expenses(self, **kw):
        try:
            result = []
            benefit_id = request.env['grant.benefit'].sudo().search(
                [('user_id', '=', request.session.uid)], limit=1)
            benefit_expenses = request.env['benefit.expenses'].sudo().search(
                [('benefit_id', '=', int(benefit_id))])
            for val in benefit_expenses:
                result.append(
                    {
                        "name": val.name,
                        "expenses_type": self.get_selection_label('expenses_type',val.expenses_type),
                        "expenses_fees_type": self.get_selection_label('expenses_fees_type',val.expenses_fees_type),
                        "medicine_type": self.get_selection_label('medicine_type',val.medicine_type),
                        "diseases_type": self.get_selection_label('diseases_type',val.diseases_type),
                        "trans_type": self.get_selection_label('trans_type',val.trans_type),
                        "debt_reason": val.debt_reason,
                        "attach": val.attach,
                        "debt_type": self.get_selection_label('debt_type',val.debt_type),
                        "pandemics_explain": val.pandemics_explain,
                        "amount": val.amount,
                        "state": self.get_selection_label('state',val.state),
                    }
                )

            if result:
                data = {'status': True, 'msg': (
                    _('Record Found ')), 'data': result}
            else:
                data = {'status': False, 'msg': (
                    _('Record Not Found ')), 'data': {}}
            return json.dumps(data)
        except Exception as e:
            _logger.error(str(e))
            message = self.get_server_error(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)
    


    @http.route('/benefit/add_benefit_expenses/', auth='public', website=True, csrf=False, methods=['POST'])
    def add_benefit_expenses(self, **kw):
        try:
            image_date = None
            for image in list(http.request.httprequest.files.getlist('attach')):
                image_date = base64.b64encode(image.read())
            result = []
            benefit_id = request.env['grant.benefit'].sudo().search(
                [('user_id', '=', request.session.uid)], limit=1)
            benefit_expenses = request.env['benefit.expenses']
            date_created = {
                    "name": kw.get('name',False),
                    "benefit_id":benefit_id.id,
                    "expenses_type": kw.get('expenses_type',False),
                    "expenses_fees_type": kw.get('expenses_fees_type',False),
                    "medicine_type": kw.get('medicine_type',False),
                    "diseases_type": kw.get('diseases_type',False),
                    "trans_type": kw.get('trans_type',False),
                    "debt_reason": kw.get('debt_reason',False),
                    "attach":image_date,
                    "debt_type": kw.get('debt_type',False),
                    "pandemics_explain": kw.get('pandemics_explain',False),
                    "amount": kw.get('amount',False),
                }
            val = benefit_expenses.create(date_created) 
            return self.get_benefit_expenses()
        except Exception as e:
            _logger.error(str(e))
            message = self.get_server_error(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    def get_selection_label(self, field_name, field_value):
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context
        if not field_name or not field_value:
            return ''
        return _(dict(request.env['benefit.expenses'].fields_get(allfields=[field_name])[field_name]['selection'])[field_value])

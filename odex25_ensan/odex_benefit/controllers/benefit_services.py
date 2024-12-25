# -*- coding: utf-8 -*-
import re
from odoo.tools.translate import _
from odoo.http import request
import base64
import json
import logging
from odoo import http, modules

_logger = logging.getLogger(__name__)


class services(http.Controller):
    def get_server_error(self, e):
        x = False
        if len(e.args) == 2:
            x, y = e.args
            x = re.sub('\n', '', x)
        else:
            x = e.args
        text = (_("Contact Admin"))
        message = "%s, %s" % (x, text)
        return message

    def get_validation_error(self, filed_id):
        filed = filed_id.replace('_', ' ')
        result = ({'status': False, 'msg': (
            _('Enter The ' + filed)), 'data': {'filed': filed_id}})
        return result

    # restaurant
    @http.route(['/services/restaurant/add_profile'], type="http", auth="public", website=True, method=['POST'],
                csrf=False)
    def add_restaurant_profile(self, **kw):
        values = {}
        li = ['name', 'surplus_type', 'zone', 'neighborhood',
              'city_id', 'address', 'lat', 'lon']
        for filed in li:
            if not kw.get(filed, False):
                error = self.get_validation_error(filed)
                return json.dumps(error)
        if request.session.uid:
            partner = request.env['res.partner'].sudo().search(
                [('user_id', '=', request.session.uid)])
            values['partner_id'] = partner.id
            for field_name, field_value in kw.items():
                values[field_name] = field_value
            values['surplus_type'] = [1, 2]  # TODO
            surplus = request.env['benefit.food.surplus'].sudo().create(values)
            surplus.surplus_type = values['surplus_type']
            if surplus:
                data = {'status': True, 'msg': (
                    _('Record created ')), 'data': {}}
            else:
                data = {'status': False, 'msg': (
                    _('Record Not created ')), 'data': {}}
        else:
            data = {'status': False, 'msg': (_('need user')), 'data': {}}

        return json.dumps(data)

    # restaurant
    @http.route(['/services/restaurant/add_food'], type="http", auth="public", website=True, method=['POST'],
                csrf=False)
    def add_restaurant_food(self, id, **kw):
        values = {}
        li = ['surplus_type', 'surplus_count', 'date_start',
              'date_end', 'quantity', 'description']
        for filed in li:
            if not kw.get(filed, False):
                error = self.get_validation_error(filed)
                return json.dumps(error)
        for field_name, field_value in kw.items():
            values[field_name] = field_value
        values['food_surplus_id'] = id
        surplus = request.env['food.surplus.line'].sudo().create(values)
        if surplus:
            data = {'status': True, 'msg': (_('Record created ')), 'data': {}}
        else:
            data = {'status': False, 'msg': (
                _('Record Not created ')), 'data': {}}

        return json.dumps(data)

    @http.route(['/services/restaurant/request_food'], type="http", auth="public", website=True, method=['POST'],
                csrf=False)
    def request_restaurant_food(self, id):
        user_id = request.env['grant.benefit'].sudo().search(
            [('user_id', '=', request.session.uid)])
        food = request.env['food.surplus.line'].sudo().search([
            ('id', '=', id)])
        if user_id:
            foods = food.sudo().benefit_ids = [(4, user_id.id)]
            print(foods)
        if foods:
            data = {'status': True, 'msg': (_('Request created ')), 'data': {}}
        else:
            data = {'status': False, 'msg': (_('Request Not created created ')), 'data': {}}

        # # Todo: add is_available check
        # TODO return barcode after request
        # if food.is_available:
        #     data = {'status': True, 'msg': (_('Record created ')), 'data': {}}
        # else:
        #     data = {'status': False, 'msg': (_('Record Not created ')), 'data': {}}
        #
        return json.dumps(data)

    ################ get function ##################
    # ZkataAlfter
    @http.route(['/services/zkat_alfter'], type="http", auth="public", website=True, method=['GET'],
                csrf=False)
    def get_all_zkat(self):
        try:
            data = request.env['receive.benefit.zkat'].sudo().search(
                [('state', '=', 'receiving')])
            data = {'status': True, 'msg': (_('zkat Found')),
                    'data': [(s.id, s.name, s.description, s.uint_price, str(s.date_from), str(s.date_to)) for s in data]}
            return json.dumps(data)
        except Exception as e:
            _logger.error(str(e))
            message = self.get_server_error(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    @http.route(['/services/receive_zkat'], type="http", auth="public", website=True, method=['POST'], csrf=False)
    def add_zakat(self, id, **kw):
        values = {}
        if not kw.get('donor_name', False):
            return json.dumps({'status': False, 'msg': (_('donor_name')), 'data': {}})
        if not kw.get('donation_type', False):
            return json.dumps({'status': False, 'msg': (_('donation_type')), 'data': {}})
        if kw.get('donation_type', False) == 'cash' or kw.get('donation_type', False) == 'both':
            if not kw.get('amount', False):
                return json.dumps({'status': False, 'msg': (_('amount')), 'data': {}})
        if kw.get('donation_type', False) == 'material' or kw.get('donation_type', False) == 'both':
            if not kw.get('quantity', False):
                return json.dumps({'status': False, 'msg': (_('quantity')), 'data': {}})
        values['receive_zkat_id'] = id
        for field_name, field_value in kw.items():
            if field_name == 'donor_name' or field_name == 'phone_number' or field_name == 'donation_type' or field_name == 'amount' or field_name == 'quantity':
                values[field_name] = field_value
            else:
                continue
        # todo online payment
        collection = request.env['payment.collection.line'].sudo().create(
            values)
        if collection:
            data = {'status': True, 'msg': (_('Record created ')), 'data': {}}
        else:
            data = {'status': False, 'msg': (
                _('Record Not created ')), 'data': {}}
        return json.dumps(data)

    @http.route(['/services/food_basket'], type="http", auth="public", website=True, method=['GET'],
                csrf=False)
    def get_all_basket(self):
        try:
            data = request.env['receive.food.basket'].sudo().search(
                [('state', '=', 'receiving')])
            results = []
            if data:
                results.append(({'basket': [{'id': s.id, 'name': s.name, 'description': s.description,
                                             'date_start': str(s.date_start), 'date_end': str(s.date_end)} for s in data]}))
            data = {'status': True, 'data': results}
            return json.dumps(data)
        except Exception as e:
            _logger.error(str(e))
            message = self.get_server_error(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    @http.route(['/services/add_food_basket'], type="http", auth="public", website=True, method=['POST'],
                csrf=False)
    def add_food_basket(self, id, **kw):
        values = {}
        if not kw.get('name', False):
            return json.dumps({'status': False, 'msg': (_('name')), 'data': {}})
        if not kw.get('phone_number', False):
            return json.dumps({'status': False, 'msg': (_('phone_number')), 'data': {}})
        if not kw.get('donation_type', False):
            return json.dumps({'status': False, 'msg': (_('donation_type')), 'data': {}})
        # if not kw.get('qty', False):
        #     return json.dumps({'status': False, 'msg': (_('qty')), 'data': {}})

        values['food_basket_id'] = id
        values['donation_method'] = 'outside'
        for field_name, field_value in kw.items():
            if field_name == 'name' or field_name == 'phone_number' or field_name == 'donation_type' or field_name == 'amount' or field_name == 'qty' or field_name == 'donation_method':
                values[field_name] = field_value
            else:
                continue
        collection = request.env['food.basket.line'].sudo().create(values)
        if collection:
            data = {'status': True, 'msg': (_('Record created ')), 'data': {}}
        else:
            data = {'status': False, 'msg': (
                _('Record Not created ')), 'data': {}}
        return json.dumps(data)

    # Food Surplus
    @http.route(['/services/reservation_food'], type="http", auth="public", website=True, method=['POST'],
                csrf=False)
    def reservation_food(self, id, benefit_id, **kw):
        collection = request.env['food.surplus.line'].sudo().browse(int(id))
        benefit = request.env['grant.benefit'].sudo().browse(int(benefit_id))
        if collection:
            if len(collection.benefit_ids) >= collection.surplus_count:
                data = {'status': False, 'msg': (
                    _('Record Not created ')), 'data': {}}
            else:
                data = {'status': True, 'msg': (
                    _('Record created ')), 'data': {}}
                for co in collection:
                    co.sudo().write({'benefit_ids': [(4, benefit.id)]})
        else:
            data = {'status': False, 'msg': (
                _('Record Not found ')), 'data': {}}
        return json.dumps(data)

    @http.route(['/services/clubs'], type="http", auth="public", website=True, method=['GET'],
                csrf=False)
    def get_all_club(self):
        try:
            # todo : add is_available domain
            clubs = request.env['benefit.club'].sudo().search(
                [('is_available', '=', True)])
            results = []
            if clubs:
                results.append(({'clubs': [{'id': s.id, 'name': s.name, 'description': s.description,
                                            'subscription_amount': s.subscription_amount,
                                            'programs_type': s.programs_type} for s in clubs]}))
            data = {'status': True, 'data': results}
            return json.dumps(data)
        except Exception as e:
            _logger.error(str(e))
            message = self.get_server_error(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    @http.route(['/services/club_subscription'], type="http", auth="none", website=True, method=['POST'],
                csrf=False)
    def add_subscription_request(self, id, **kw):
        values = {}
        li = ['name', 'phone_number', 'birth_date', 'city', 'lat', 'lon']
        for filed in li:
            if not kw.get(filed, False):
                error = self.get_validation_error(filed)
                return json.dumps(error)
        for field_name, field_value in kw.items():
            values[field_name] = field_value
            # todo
            # todo online payment
        partner_id = request.env.user.partner_id
        external_by_partner_id = request.env['external.benefits'].sudo().search(
            [('partner_id', '=', partner_id.id)], limit=1)
        external_by_phone = request.env['external.benefits'].sudo().search(
            [('phone', '=', values['phone_number'])], limit=1)
        external_id = external_by_partner_id or external_by_phone
        if not external_id:
            external_id = request.env['external.benefits'].sudo().create({
                "name": values['name'],
                "phone": values['phone_number'],
                "birth_date": values['birth_date'],
                "city_id": values['city'],
            })
        if not external_id and partner_id:
            external_id = request.env['external.benefits'].sudo().create({
                "name": partner_id.name,
                "phone": partner_id.phone,
                "birth_date": partner_id.birth_date,
                "city_id": partner_id.city_id,
                "partner_id": partner_id.id
            })
        subscription = None
        if external_id:
            subscription = request.env['external.request'].sudo().create({
                "club_id": int(id),
                "external_id": external_id.id,
                "lat": values['lat'],
                "lon": values['lon'],
            })
        if subscription:
            data = {'status': True, 'msg': (_('Record created ')), 'data': {}}
        else:
            data = {'status': False, 'msg': (
                _('Record Not created ')), 'data': {}}

        return json.dumps(data)

    @http.route(['/services/food'], type="http", auth="public", website=True, method=['GET'],
                csrf=False)
    def get_available_food_surplus(self):
        try:
            foods = request.env['food.surplus.line'].sudo().search(
                [])  # ([('is_available', '=', True)])
            results = []
            if foods:
                results.append(({'foods': [{'id': s.id, 'name': s.food_surplus_id.name,
                'name_food': s.surplus_type.name,
                                            'description': s.description,
                                            'surplus_count': s.surplus_count, 'quantity': s.quantity, 'address':
                                                s.food_surplus_id.address, 'date_start': str(s.date_start), 'date_end': str(s.date_end)} for s in foods]}))
            data = {'status': True, 'data': results}
            return json.dumps(data)
        except Exception as e:
            _logger.error(str(e))
            message = self.get_server_error(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    @http.route(['/services/loans'], type="http", auth="public", website=True, method=['GET'],
                csrf=False)
    def get_all_loans(self):
        try:
            loans = request.env['benefit.loans'].sudo().search(
                [('state', '=', 'announced')])
            results = []
            if loans:
                results.append(({'loans': [{'id': s.id, 'name': s.family_id.name, 'description': s.description,
                                            'benefits_total': s.benefits_total,
                                            'project_name': s.name, 'loan_amount': s.loan_amount, } for s in loans]}))
            data = {'status': True, 'data': results}
            return json.dumps(data)
        except Exception as e:
            _logger.error(str(e))
            message = self.get_server_error(e)
            data = {'status': False, 'msg': message}
            return json.dumps(data)

    #create_loan in backend
    @http.route(['/services/create_loan'], type="http", auth="public", website=True, method=['POST'],
                csrf=False)
    def create_loan(self, **kw):
        values = {}
        # if not kw.get('phone_number', False):
        #     return json.dumps({'status': False, 'msg': (_('phone_number')), 'data': {}})
        # if not kw.get('loan_amount', False):
        #     return json.dumps({'status': False, 'msg': (_('loan_amount')), 'data': {}})
        # if not kw.get('installment_value', False):
        #     return json.dumps({'status': False, 'msg': (_('installment_value')), 'data': {}})
        # if not kw.get('installment_number', False):
        #     return json.dumps({'status': False, 'msg': (_('installment_number')), 'data': {}})
        for field_name, field_value in kw.items():
            values[field_name] = field_value
        loan = request.env['receive.benefit.loans'].sudo().create(values)

        if loan:
            data = {'status': True, 'msg': (_('Record created ')), 'data': {}}
        else:
            data = {'status': False, 'msg': (
                _('Record Not created ')), 'data': {}}
        return json.dumps(data)

    # restaurant
    @http.route(['/services/appliancesFurniture/receive'], type="http", auth="public", website=True, method=['POST'],
                csrf=False)
    def add_appliances(self, **kw):
        values = {}
        li = ['name', 'donor_name', 'phone_number', 'address', 'lat', 'lon', 'date_receipt', 'uom_id', 'product_qty',
              'product_status', 'description']
        for filed in li:
            if not kw.get(filed, False):
                error = self.get_validation_error(filed)
                return json.dumps(error)
        for field_name, field_value in kw.items():
            if field_name not in ['image_1', 'image_2', 'image_3', 'image_4']:
                values[field_name] = field_value
        for fname, fvalue in http.request.httprequest.files.items():
            if fvalue:
                file = fvalue.read()
                if len(file) > 0:
                    values[fname] = base64.b64encode(file)
        values['donation_method'] = 'platform'
        appliances = request.env['receive.appliances.furniture'].sudo().create(
            values)
        if appliances:
            data = {'status': True, 'msg': (_('Record created ')), 'data': {}}
        else:
            data = {'status': False, 'msg': (
                _('Record Not created ')), 'data': {}}

        return json.dumps(data)

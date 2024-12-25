# -*- coding: utf-8 -*-
from odoo import http,_
from odoo.http import request
import json


class Event_sponsor(http.Controller):
    @http.route('/sponser/form', type='http', auth='public', methods=['GET'])
    def get_sponser_form(self):
        sponsoring_types = request.env['event.sponsor.type'].sudo().search([])
        li = ['sequence','name']
        if sponsoring_types:
            data = {'status': True, 'msg': (_('Sponsoring Types Found')), 'data':sponsoring_types.read(li)}
        else:
            data = {'status': False, 'msg': (_('Sponsoring Types Not Found')), 'data': {}}
        return json.dumps(data)

    @http.route('/sponsor/submit', type='http', auth='public', csrf=False,methods=['POST'])
    def sponsor_submit(self,id,**kw):
        values = {}
        for field_name, field_value in kw.items():
            values[field_name] = field_value
            if field_name == 'event_id':
                field_value = request.env['event.event'].browse(int(id)).id
                values[field_name] = field_value
        sponsor = request.env['event.sponsor'].sudo().create(values)
        li = ['event_id','partner_id', 'url', 'sponsor_type_id']
        if sponsor:
            data = {'status': True, 'msg': (_('sponsor Registered')), 'data': sponsor.read(li)}
        else:
            data = {'status': False, 'msg': (_('sponsor Not Registered')), 'data': {}}
        return json.dumps(data)



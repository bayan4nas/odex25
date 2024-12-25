# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
from odoo import  _
from werkzeug.exceptions import NotFound
from odoo.addons.rating.controllers.main import Rating

from odoo import http
from odoo.http import request


class InheritRating(Rating):

    @http.route('/rating/<string:token>/<int:rate>', type='http', auth="public")
    def open_rating(self, token, rate, **kwargs):
        result = super(InheritRating,self).open_rating(token,rate, **kwargs)
        # TO DO: add context to control returned result 
        assert rate in (1, 5, 10), "Incorrect rating"
        rating = request.env['rating.rating'].sudo().search([('access_token', '=', token)])
        if not rating:
            return request.not_found()
        rate_names={
            5: ("not satisfied","غير راضي"),
            1: ("highly dissatisfied","غير راضي اطلاقا"),
            10: ("satisfied","راضي")
        }
        rating.write({'rating': rate, 'consumed': True})
        lang = rating.partner_id.lang or 'en_US'
        return request.env['ir.ui.view'].with_context(lang='en_US').render_template('rating.rating_external_page_submit', {
            'rating': rating, 'token': token,
            'rate_name': rate_names[rate], 'rate': rate
        })

    @http.route(['/rating/<string:token>/<int:rate>/submit_feedback'], type="http", auth="public", methods=['post'])
    def submit_rating(self, token, rate, **kwargs):
        rating = request.env['rating.rating'].sudo().search([('access_token', '=', token)])
        if not rating:
            return request.not_found()
        record_sudo = request.env[rating.res_model].sudo().browse(rating.res_id)
        if rating.res_model == 'helpdesk.ticket':
            if record_sudo.rated:
                return request.env['ir.ui.view'].render_template('helpdesk_translated_mailtemplate.rating_external_page_view_rated')
        record_sudo.rating_apply(rate, token=token, feedback=kwargs.get('feedback'))
        record_sudo.rated = True
        lang = rating.partner_id.lang or 'en_US'
        return request.env['ir.ui.view'].with_context(lang=lang).render_template('rating.rating_external_page_view', {
            'web_base_url': request.env['ir.config_parameter'].sudo().get_param('web.base.url'),
            'rating': rating,
        })

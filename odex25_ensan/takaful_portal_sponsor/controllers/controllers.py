# -*- coding: utf-8 -*-
from odoo import http
import json
import requests
# from odoo.addons.takaful_rest_api.controllers.sponsor_web_controller import ControllerPortalREST

class TakafulSponsorPortal(http.Controller):
    
    # kafel routes 
    @http.route('/guarantees', type='http', auth='public', website=True)
    def my_guarantees(self, page=1, **kw):
        return http.request.render("takaful_portal_sponsor.my_guarantees")

    @http.route('/sadad', type='http', auth='public', website=True)
    def sadad(self, **kw):
        return http.request.render("takaful_portal_sponsor.sadad")

    @http.route('/need_kafala', type='http', auth='public', website=True)
    def need_kafala(self, **kw):
        return http.request.render("takaful_portal_sponsor.need_kafala")

    @http.route('/orphan_needs', type='http', auth='public', website=True)
    def orphan_needs(self, **kw):
        return http.request.render("takaful_portal_sponsor.orphan_needs")

    @http.route('/kafala_gift', type='http', auth='public', website=True)
    def kafala_gift(self, **kw):
        return http.request.render("takaful_portal_sponsor.kafala_gift")

    @http.route('/general_needs', type='http', auth='public', website=True)
    def general_needs(self, **kw):
        return http.request.render("takaful_portal_sponsor.general_needs")

    @http.route('/cancel_kafala', type='http', auth='public', website=True)
    def cancel_kafala(self, **kw):
        return http.request.render("takaful_portal_sponsor.cancel_kafala")

    @http.route('/makfoul_details', type='http', auth='public', website=True)
    def my_page(self, **kwargs):
        my_id = kwargs.get('benefit_type', 'default_value')
        user_type = kwargs.get('benefit_id', 'default_value')
        return http.request.render('takaful_portal_sponsor.makfoul_details', {
            'my_id': my_id,
            'user_type': user_type,
        })
        
    @http.route('/need_kafala_details', type='http', auth='public', website=True)
    def need_kafala_details(self, **kwargs):
        my_id = kwargs.get('benefit_type', 'default_value')
        user_type = kwargs.get('benefit_id', 'default_value')
        return http.request.render('takaful_portal_sponsor.need_kafala_details', {
            'my_id': my_id,
            'user_type': user_type,
        })

    @http.route('/paied_record', type='http', auth='public', website=True)
    def paied_record(self, **kw):
        return http.request.render("takaful_portal_sponsor.paied_record")

    @http.route('/delayed_record', type='http', auth='public', website=True)
    def delayed_record(self, **kw):
        return http.request.render("takaful_portal_sponsor.delayed_record")

    @http.route('/notifications', type='http', auth='public', website=True)
    def get_notifications(self, **kwargs):
        is_read = kwargs.get('is_read', 'default_value')
        return http.request.render('takaful_portal_sponsor.all_notifications', {
            'is_read': is_read
        })
        
    @http.route('/notifications_details', type='http', auth='public', website=True)
    def notifications_details(self, **kwargs):
        notify_id = kwargs.get('id', 'default_value')
        return http.request.render('takaful_portal_sponsor.notifications_details', {
            'id': notify_id
        })

    @http.route('/certificates_settings', type='http', auth='public', website=True)
    def certificates_settings(self, **kw):
        return http.request.render("takaful_portal_sponsor.certificates_settings")
    
    @http.route('/notifications_settings', type='http', auth='public', website=True)
    def notifications_settings(self, **kw):
        return http.request.render("takaful_portal_sponsor.notifications_settings")
    
    @http.route('/sponsor_profile', type='http', auth='public', website=True)
    def sponsor_profile(self, **kw):
        return http.request.render("takaful_portal_sponsor.sponsor_profile")

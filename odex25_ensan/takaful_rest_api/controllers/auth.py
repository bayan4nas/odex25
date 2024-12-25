# -*- coding: utf-8 -*-
from .main import *
import sys
import time

import logging

try:
    import simplejson as json
except ImportError:
    import json

import werkzeug.wrappers


from odoo import http
from odoo.http import request
from odoo import _

_logger = logging.getLogger(__name__)


# HTTP controller of REST resources:

class ControllerREST(http.Controller):
    
    def define_token_expires_in(self, token_type, kw):
        token_lifetime = kw.get('%s_lifetime' % token_type)
        try:
            token_lifetime = float(token_lifetime)
        except:
            pass
        if isinstance(token_lifetime, (int, float)):
            expires_in = token_lifetime
        else:
            try:
                expires_in = float(request.env['ir.config_parameter'].sudo()
                    .get_param('takaful_rest_api.%s_token_expires_in' % token_type))
            except:
                expires_in = None
        return int(round(expires_in or (sys.maxsize - time.time())))
    
    # Login in System database and get access tokens:
    @http.route('/api/auth/login', methods=['GET', 'POST'], type='http', auth='none',  csrf=False)
    def api_auth_gettokens(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context
        
        username = kw.get('username', False)
        password = kw.get('password', False)
        
        # Empty 'username' or 'password:
        if not username or not password:
            error_descrip = _("Empty value of 'username' or 'password'!")
            error = 'empty_username_or_password'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)
        
        # Login in System database:
        try:
            request.session.authenticate(db_name, username, password)
        except:
            # Invalid database:
            error_descrip = _("Invalid database!")
            error = 'invalid_database'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)
        
        uid = request.session.uid
        
        # System login failed:
        if not uid:
            error_descrip = _("System User authentication failed!")
            error = 'system_user_authentication_failed'
            _logger.error(error_descrip)
            return error_response(401, error, error_descrip)
        
        # Generate tokens
        access_token = generate_token()
        expires_in = self.define_token_expires_in('access', kw)
        refresh_token = generate_token()
        refresh_expires_in = self.define_token_expires_in('refresh', kw)
        # prevent undeletable access token
        if refresh_expires_in < expires_in:
            refresh_expires_in = expires_in
        
        # Save all tokens in store
        _logger.info("Save OAuth2 tokens of user in Token Store...")
        token_store.save_all_tokens(
            request.env,
            access_token = access_token,
            expires_in = expires_in,
            refresh_token = refresh_token,
            refresh_expires_in = refresh_expires_in,
            user_id = uid)
        
        user_context = request.session.get_context() if uid else {}
        company_id = request.env.user.company_id.id if uid else 'null'
        # Logout from System and close current 'login' session:
        request.session.logout()
        
        # Successful response:
        resp = werkzeug.wrappers.Response(
            status = OUT__auth_gettokens__SUCCESS_CODE,
            content_type = 'application/json; charset=utf-8',
            headers = [ ('Cache-Control', 'no-store'),
                        ('Pragma', 'no-cache')  ],
            response = json.dumps({
                # 'uid':                  uid,
                # 'user_context':         user_context,
                # 'company_id':           company_id,
                'access_token':         access_token,
                'expires_in':           expires_in,
                'refresh_token':        refresh_token,
                'refresh_expires_in':   refresh_expires_in, }),
        )
        # Remove cookie session
        resp.set_cookie = lambda *args, **kw: None
        return resp
    
    # Refresh access token:
    @http.route('/api/auth/refresh_token', methods=['POST'], type='http', auth='none',  csrf=False)
    def api_auth_refreshtoken(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context
        
        # Get and check refresh token
        refresh_token = kw.get('refresh_token', False)
        if not refresh_token:
            error_descrip = _("No refresh token was provided in request!")
            error = 'no_refresh_token'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)
        
        # Validate refresh token
        refresh_token_data = token_store.fetch_by_refresh_token(request.env, refresh_token)
        if not refresh_token_data:
            return error_response_401__invalid_token()
        
        old_access_token = refresh_token_data['access_token']
        new_access_token = generate_token()
        expires_in = self.define_token_expires_in('access', kw)
        uid = refresh_token_data['user_id']
        
        # Update access (and refresh) token in store
        token_store.update_access_token(
            request.env,
            old_access_token = old_access_token,
            new_access_token = new_access_token,
            expires_in = expires_in,
            refresh_token = refresh_token,
            user_id = uid)
        
        # Successful response:
        resp = werkzeug.wrappers.Response(
            status = OUT__auth_refreshtoken__SUCCESS_CODE,
            content_type = 'application/json; charset=utf-8',
            headers = [ ('Cache-Control', 'no-store'),
                        ('Pragma', 'no-cache')  ],
            response = json.dumps({
                'access_token': new_access_token,
                'expires_in':   expires_in,
            }),
        )
        # Remove cookie session
        resp.set_cookie = lambda *args, **kw: None
        return resp
    
    # Delete access tokens from token store:
    @http.route('/api/auth/logout', methods=['POST'], type='http', auth='none',  csrf=False)
    def api_auth_deletetokens(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context
        
        # Get and check refresh token
        refresh_token = kw.get('refresh_token', False)
        if not refresh_token:
            error_descrip = _("No refresh token was provided in request!")
            error = 'no_refresh_token'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)
        
        token_store.delete_all_tokens_by_refresh_token(request.env, refresh_token)
        
        # Successful response:
        return successful_response(
            OUT__auth_deletetokens__SUCCESS_CODE,
            {'message': _('Successfully logout'),}
        )

    # Validate access token:
    @http.route('/api/auth/validate_token', methods=['POST'], type='http', auth='none',  csrf=False)
    @check_permissions
    def api_auth_validatetoken(self, **kw):
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        return successful_response( 
            status = OUT_SUCCESS_CODE,
            dict_data = {}
        )

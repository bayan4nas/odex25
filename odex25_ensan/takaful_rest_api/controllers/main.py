# -*- coding: utf-8 -*-
import functools
import hashlib
import logging
import os
from ast import literal_eval

try:
    import simplejson as json
except ImportError:
    import json
import base64

import werkzeug.wrappers

import odoo
from odoo import _
from odoo import http, SUPERUSER_ID, models
from odoo.http import request, OpenERPSession, Response
from odoo.tools.safe_eval import safe_eval
from odoo.modules.registry import Registry
from psycopg2.extensions import ISOLATION_LEVEL_READ_COMMITTED

import re
import datetime
from functools import wraps

SAUDI_MOBILE_PATTERN = "(^(05|5)(5|0|3|6|4|9|1|8|7)([0-9]{7})$)"
_NOT_FOUND_SRT = _("لايوجد")
_NOT_FOUND_INT = 0
_NOT_FOUND_LIST = []
_NOT_FOUND_FLOAT = 0.0
_NOT_FOUND_DATE = None
_logger = logging.getLogger(__name__)


def map_filters(filters):
    domain = []
    filtered_dict = {}
    for item in filters:
        key = item.get('name')
        value = item.get('value')
        status = item.get('state')

        if status == "true":
            status = True
        elif value == "false":
            status = False

        if value == "true" and status is True:
            value = True
            filtered_dict.setdefault(key, value)
        elif value == "false" and status is True:
            value = False
            filtered_dict.setdefault(key, value)
        elif value and status is True:
            filtered_dict.setdefault(key, []).append(value)

    for field_name, field_value in filtered_dict.items():
        if type(field_value) is list:
            domain.append([field_name, 'in', field_value])
        else:
            domain.append([field_name, '=', field_value])

    return domain


def get_value_or_null(obj, key):
    if not obj[key] and obj._fields[key].type in ['one2many', 'many2many']:
        return _NOT_FOUND_LIST
    if not obj[key] and obj._fields[key].type in ['many2one']:
        return _NOT_FOUND_INT
    elif not obj[key] and obj._fields[key].type in ['date', 'datetime']:
        return _NOT_FOUND_DATE
    elif not obj[key] and obj._fields[key].type in ['integer']:
        return _NOT_FOUND_INT
    elif not obj[key] and obj._fields[key].type in ['float']:
        return _NOT_FOUND_FLOAT
    elif not obj[key] and obj._fields[key].type in ['selection']:
        return _NOT_FOUND_SRT
    elif not obj[key] and obj._fields[key].type != 'boolean':
        return _NOT_FOUND_SRT
    elif obj._fields[key].type == 'many2one':
        return obj[key].id
    elif obj._fields[key].type in ['many2one', 'one2many', 'many2many']:
        return obj[key].mapped('id')
    # elif obj._fields[key].type == 'selection':
    #     return dict(obj.fields_get(allfields=[key])[key]['selection'])[obj[key]]

    return obj[key]


def props_fields(recordset, fields):
    if not fields:
        fields = ['id']
    list_data = []
    for obj in recordset:
        rec = dict((key, get_value_or_null(obj, key)) for key in fields if key in list(set(obj._fields)))
        if rec:
            list_data.append(rec)
    return list_data


class make_response():

    def __call__(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            header = 'application/json;charset=utf-8'
            try:
                result = decode_bytes(func(*args, **kwargs))
                code = result.get("code") or 200
                dict_data = result.get("dict_data") or {}
                return Response(json.dumps(dict_data), content_type=header, status=code)
            except Exception as e:
                code = 500
                dict_data = {
                    'error': _("Internal Server Error"),
                    'error_descrip': str(e),
                }
                return Response(json.dumps(dict_data), content_type=header, status=code)

        return wrapper


def eval_request_params(kwargs):
    for k, v in kwargs.items():
        try:
            kwargs[k] = safe_eval(v)
        except Exception:
            continue


def decode_bytes(result):
    if isinstance(result, (list, tuple)):
        decoded_result = []
        for item in result:
            decoded_result.append(decode_bytes(item))
        return decoded_result
    if isinstance(result, dict):
        decoded_result = {}
        for k, v in result.items():
            decoded_result[decode_bytes(k)] = decode_bytes(v)
        return decoded_result
    if isinstance(result, bytes):
        return result.decode('utf-8')
    return result


def get_first_day_of_next_month():
    """ Get the first day of the next month. Preserves the timezone. """
    dt = datetime.datetime.today()  # Starting from current month
    if dt.day == 1:
        # Ya.. first day of the month!
        return dt

    if dt.month == 12:
        return datetime.datetime(year=dt.year + 1,
                                 month=1,
                                 day=1,
                                 tzinfo=dt.tzinfo)
    else:
        return datetime.datetime(year=dt.year,
                                 month=dt.month + 1,
                                 day=1,
                                 tzinfo=dt.tzinfo)


OUT_SUCCESS_CODE = 200

# List of REST resources in current file:
#   (url prefix)            (method)     (action)
# /api/auth/get_tokens        GET     - Login in System and get access tokens
# /api/auth/refresh_token     POST    - Refresh access token
# /api/auth/delete_tokens     POST    - Delete access tokens from token store


# List of IN/OUT data (json data and HTTP-headers) for each REST resource:

# /api/auth/get_tokens  GET  - Login in System and get access tokens
# IN data:
#   JSON:
#       {
#           "username": "XXXX",     # System username
#           "password": "XXXX",     # System user password
#           "access_lifetime": XXX, # (optional) access token lifetime (seconds)
#           "refresh_lifetime": XXX # (optional) refresh token lifetime (seconds)
#       }
# OUT data:
OUT__auth_gettokens__SUCCESS_CODE = 200  # editable
#   Possible ERROR CODES:
#       400 'empty_username_or_password'
#       400 'invalid_database'
#       401 'system_user_authentication_failed'
#   JSON:
#       {
#           "uid":                  XXX,
#           "user_context":         {....},
#           "company_id":           XXX,
#           "access_token":         "XXXXXXXXXXXXXXXXX",
#           "expires_in":           XXX,
#           "refresh_token":        "XXXXXXXXXXXXXXXXX",
#           "refresh_expires_in":   XXX
#       }

# /api/auth/refresh_token  POST  - Refresh access token
# IN data:
#   JSON:
#       {
#           "refresh_token": "XXXXXXXXXXXXXXXXX",
#           "access_lifetime": XXX  # (optional) access token lifetime (seconds)
#       }
# OUT data:
OUT__auth_refreshtoken__SUCCESS_CODE = 200  # editable
#   Possible ERROR CODES:
#       400 'no_refresh_token'
#       401 'invalid_token'
#   JSON:
#       {
#           "access_token": "XXXXXXXXXXXXXXXXX",
#           "expires_in":   XXX
#       }

# /api/auth/delete_tokens  POST  - Delete access tokens from token store
# IN data:
#   JSON:
#       {"refresh_token": "XXXXXXXXXXXXXXXXX"}
# OUT data:
OUT__auth_deletetokens__SUCCESS_CODE = 200  # editable
#   Possible ERROR CODES:
#       400 'no_refresh_token'

PAGE_SIZE = 10


def check_permissions(func):
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        _logger.info("Check permissions...")
        # Update context to add language
        context = request.env.context.copy()
        context.update({'lang': u'ar_001'})
        request.env.context = context

        # Get access token from http header
        access_token = request.httprequest.headers.get('access_token')
        if not access_token:
            error_descrip = _("No access token was provided in request header!")
            error = 'no_access_token'
            _logger.error(error_descrip)
            return error_response(400, error, error_descrip)

        request.session.context = context
        # Validate access token
        access_token_data = token_store.fetch_by_access_token(request.env, access_token)
        if not access_token_data:
            return error_response_401__invalid_token()

        # Set session UID from current access token
        request.session.uid = access_token_data['user_id']
        # Set user's context
        user_context = request.env(request.cr, request.session.uid)['res.users'].context_get().copy()
        user_context['uid'] = request.session.uid
        request.session.context = request.context = user_context
        # Set website request object
        if not hasattr(request, 'website') and request.env['ir.module.module'].sudo().search([
            ('name', '=', 'website'), ('state', 'in', ['installed', 'to upgrade', 'to remove'])], limit=1):
            request_http_host = request.httprequest.environ['HTTP_HOST']
            request.website = request.env['website'].sudo().search([('domain', 'like', request_http_host)],
                                                                   limit=1) or None

        # The code, following the decorator
        return func(self, *args, **kwargs)

    return wrapper


def successful_response(status, dict_data):
    resp = werkzeug.wrappers.Response(
        status=status,
        content_type='application/json; charset=utf-8',
        # headers = None,
        response=json.dumps(dict_data, ensure_ascii=u_escape_characters_for_unicode_in_responses),
    )
    # Remove cookie session
    resp.set_cookie = lambda *args, **kwargs: None
    return resp


def error_response(status, error, error_descrip=None):
    data = {
        'error': error,
        'error_descrip': error_descrip,
    }
    if not error_descrip:
        del data['error_descrip']
    resp = werkzeug.wrappers.Response(
        status=status,
        content_type='application/json; charset=utf-8',
        # headers = None,
        response=json.dumps(data, ensure_ascii=u_escape_characters_for_unicode_in_responses),
    )
    # Remove cookie session
    resp.set_cookie = lambda *args, **kwargs: "None"
    return resp


def error_response_400__invalid_object_id():
    error_descrip = _("Invalid object or page 'id'!")
    error = 'invalid_object_id'
    _logger.error(error_descrip)
    return error_response(400, error, error_descrip)


def error_response_401__invalid_token():
    error_descrip = _("Token is expired or invalid!")
    error = 'invalid_token'
    _logger.error(error_descrip)
    return error_response(401, error, error_descrip)


def error_response_404__not_found_object_in_system():
    error_descrip = _("Not found object(s) in System!")
    error = 'not_found_object_in_system'
    _logger.error(error_descrip)
    return error_response(404, error, error_descrip)


def error_response_404_url_not_found():
    error_descrip = _("Not found URL in System!")
    error = 'not_found_url_in_system'
    _logger.error(error_descrip)
    return error_response(404, error, error_descrip)


def error_response_409__not_read_object_in_system(system_error):
    error_descrip = _("Not read object in System! ERROR: %s") % system_error
    error = 'not_read_object_in_system'
    _logger.error(error_descrip)
    return error_response(409, error, error_descrip)


def error_response_409__not_created_object_in_system(system_error):
    error_descrip = _("Not created object in System! ERROR: %s") % system_error
    error = 'not_created_object_in_system'
    _logger.error(error_descrip)
    return error_response(409, error, error_descrip)


def error_response_409__not_updated_object_in_system(system_error):
    error_descrip = _("Not updated object in System! ERROR: %s") % system_error
    error = 'not_updated_object_in_system'
    _logger.error(error_descrip)
    return error_response(409, error, error_descrip)


def error_response_409__not_deleted_object_in_system(system_error):
    error_descrip = _("Not deleted object in System! ERROR: %s") % system_error
    error = 'not_deleted_object_in_system'
    _logger.error(error_descrip)
    return error_response(409, error, error_descrip)


def error_response_409__not_called_method_in_system(system_error):
    error_descrip = _("Not called method in System! ERROR: %s") % system_error
    error = 'not_called_method_in_system'
    _logger.error(error_descrip)
    return error_response(409, error, error_descrip)


def error_response_501__method_not_exist_in_system():
    error_descrip = _("Method not exist in System!")
    error = 'method_not_exist_in_system'
    _logger.error(error_descrip)
    return error_response(501, error, error_descrip)


def error_response_501__model_not_available():
    error_descrip = _("This model is not available in REST API!")
    error = 'model_not_available'
    _logger.error(error_descrip)
    return error_response(501, error, error_descrip)


def generate_token(length=40):
    random_data = os.urandom(100)
    hash_gen = hashlib.new('sha512')
    hash_gen.update(random_data)
    return hash_gen.hexdigest()[:length]


# Read system parameters and setup token store:
db_name = odoo.tools.config.get('db_name', 'takaful_dev')
if not db_name:
    _logger.error(
        "ERROR: To proper setup OAuth2 and Token Store - it's necessary to set the parameter 'db_name' in System config file!")
else:
    # Read system parameters...
    registry = Registry(db_name)

    print(db_name)
    print(registry)
    with registry.cursor() as cr:
        cr.execute("SELECT value FROM ir_config_parameter \
            WHERE key = 'takaful_rest_api.cors_parameter_value_in_all_routes'")
        res = cr.fetchone()
        rest_cors_value = res and res[0].strip() or 'null'
        cr.execute("SELECT value FROM ir_config_parameter \
            WHERE key = 'takaful_rest_api.u_escape_characters_for_unicode_in_responses'")
        res = cr.fetchone()
        u_escape_characters_for_unicode_in_responses = res and res[0].strip()
        if u_escape_characters_for_unicode_in_responses in ('1', 'True', 'true'):
            u_escape_characters_for_unicode_in_responses = True
        else:
            u_escape_characters_for_unicode_in_responses = False
        # Token store settings:
        cr.execute("SELECT value FROM ir_config_parameter \
            WHERE key = 'takaful_rest_api.use_redis_token_store'")
        res = cr.fetchone()
        use_redis_token_store = res and res[0].strip()
        if use_redis_token_store in ('0', 'False', 'None', 'false'):
            use_redis_token_store = False
        if not use_redis_token_store:
            # Setup Simple token store
            _logger.info("Setup Simple token store...")
            from . import simple_token_store

            token_store = simple_token_store.SimpleTokenStore()
        else:
            # Setup Redis token store
            _logger.info("Setup Redis token store...")
            cr.execute("SELECT value FROM ir_config_parameter \
                WHERE key = 'takaful_rest_api.redis_host'")
            res = cr.fetchone()
            redis_host = res and res[0]
            cr.execute("SELECT value FROM ir_config_parameter \
                WHERE key = 'takaful_rest_api.redis_port'")
            res = cr.fetchone()
            redis_port = res and res[0]
            cr.execute("SELECT value FROM ir_config_parameter \
                WHERE key = 'takaful_rest_api.redis_db'")
            res = cr.fetchone()
            redis_db = res and res[0]
            cr.execute("SELECT value FROM ir_config_parameter \
                WHERE key = 'takaful_rest_api.redis_password'")
            res = cr.fetchone()
            redis_password = res and res[0]
            if redis_password in ('None', 'False'):
                redis_password = None
            if redis_host and redis_port:
                from . import redis_token_store

                token_store = redis_token_store.RedisTokenStore(
                    host=redis_host,
                    port=redis_port,
                    db=redis_db,
                    password=redis_password)
            else:
                _logger.warning(
                    "WARNING: It's necessary to RESTART System server after the installation of 'takaful_rest_api' module!")
        # Connect REST resources
        # from . import cors_assist
        from . import resources

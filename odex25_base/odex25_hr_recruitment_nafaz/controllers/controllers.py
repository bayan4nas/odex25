# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from keycloak import KeycloakOpenID
from odoo import http, _
from odoo.http import request, Response, JsonRequest
import json
from datetime import datetime
from werkzeug.exceptions import NotFound
from odoo.addons.website_hr_recruitment.controllers.main import WebsiteHrRecruitment
from ..client_utils import get_client, handle_service_error
from odoo.exceptions import AccessDenied
import logging
import werkzeug.urls
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class HrEmployeeAPI(http.Controller):

    @http.route('/api/employee', type='http', auth='public', methods=['GET', 'OPTIONS', 'POST'], csrf=False, cors='*')
    def get_all_employees(self, **kw):
        # Retrieve and validate id_token and access_token
        id_token, access_token = kw.get('id_token'), kw.get('access_token')
        if not id_token or not access_token:
            return self._response(400, _('id_token and access_token are required'), success=False)

        # Retrieve OAuth provider configuration
        provider = request.env['auth.oauth.provider'].sudo().search([('enabled', '=', True), ('autologin', '=', True)], limit=1)
        if not provider or not provider.jwks_uri:
            return self._response(400, _('OAuth provider not configured or missing JWKS URI'), success=False)

        try:
            _logger.info(f"Received Id Token: {id_token}, Access Token: {access_token}")
            decoded_token = provider._parse_id_token(id_token, access_token)
            _logger.info(f"Decoded Token: {decoded_token}")

            login = decoded_token.get('username')
            if not login:
                return self._response(400, _('Username not found in token'), success=False)
        except Exception as e:
            _logger.error(f"Token decoding error: {e}")
            return self._response(500, str(e), success=False)

        # Validate the user
        user = request.env['res.users'].sudo().search([('login', '=', login)], limit=1)
        if not user:
            return self._response(400, _('User account with login {} not found').format(login), success=False)

        # Extract filters and build search domain
        filters = {
            'name': kw.get('name'),
            'english_name': kw.get('english_name'),
            'job_id.name': kw.get('job_title'),
            'department_id.name': kw.get('department'),
            'work_email': kw.get('work_email'),
            'work_phone': kw.get('work_phone'),
            'emp_no': kw.get('employee_number'),
            'mobile_phone': kw.get('mobile_phone')
        }

        domain = [('state', '=', 'open'), ('active', '=', True)] + [
            (field, 'ilike', value) if field != 'emp_no' else (field, '=', value)
            for field, value in filters.items() if value
        ]

        _logger.info(f"Search domain: {domain}")

        # Search for employees and prepare response
        employees = request.env['hr.employee'].sudo().search(domain)
        employee_data = [
            {
                'name': emp.name or "",
                'english_name': emp.english_name or "",
                'job_title': emp.job_id.name or "",
                'department': emp.department_id.name or "",
                'work_email': emp.work_email or "",
                'work_phone': emp.work_phone or "",
                'employee_number': emp.emp_no or "",
                'mobile_phone': emp.mobile_phone or "",
                'image_url': f'/web/image?model=res.users&id={emp.user_id.id}&field=image_1920' if emp.user_id else ""
            }
            for emp in employees
        ]
        return self._response(data=employee_data, success=True)

    def _response(self, code=200, message=None, data=None, success=True):
        """Helper method to standardize API responses."""
        response = {
            'code': code,
            'message': message,
            'data': data,
            'success': success
        }
        return request.make_response(json.dumps(response), headers={'Content-Type': 'application/json'})


class WebsiteHrRecruitment(WebsiteHrRecruitment):

    @http.route('''/jobs/detail/<model("hr.job"):job>''', type='http', auth="public", website=True, sitemap=False)
    def jobs_detail(self, job, **kwargs):
        if not job.can_access_from_current_website():
            raise NotFound()
        nafaz_server_url = request.env['ir.config_parameter'].sudo().get_param('nafaz_server_url', '')
        nafaz_client_id = request.env['ir.config_parameter'].sudo().get_param('nafaz_client_id', '')
        nafaz_realm_name = request.env['ir.config_parameter'].sudo().get_param('nafaz_realm_name', '')
        nafaz_client_secret_key = request.env['ir.config_parameter'].sudo().get_param('nafaz_client_secret_key', '')
        keycloak_openid = KeycloakOpenID(server_url=nafaz_server_url, client_id=nafaz_client_id,
                                         realm_name=nafaz_realm_name, client_secret_key=nafaz_client_secret_key)
        redirect_uri = request.httprequest.url_root.replace("http://", "https://")
        _logger.info("***********************************************", redirect_uri)
        # auth_url = keycloak_openid.auth_url(redirect_uri=redirect_uri + "jobs/apply/{}".format(job.id),scope="openid+profile+email")
        auth_url = keycloak_openid.auth_url(redirect_uri=redirect_uri + "jobs/apply/{}".format(job.id))
        response = request.render("website_hr_recruitment.detail", {'job': job, 'main_object': job, 'auth_url': auth_url})
        # Set the X-Frame-Options and Content-Security-Policy headers
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Content-Security-Policy'] = "frame-ancestors 'none';"
        return response

    @http.route('''/jobs/apply/<model("hr.job"):job>''', type='http', auth="public", website=True, sitemap=False)
    def jobs_apply(self, job, **kwargs):
        nafaz_server_url = request.env['ir.config_parameter'].sudo().get_param('nafaz_server_url', '')
        nafaz_client_id = request.env['ir.config_parameter'].sudo().get_param('nafaz_client_id', '')
        nafaz_realm_name = request.env['ir.config_parameter'].sudo().get_param('nafaz_realm_name', '')
        nafaz_client_secret_key = request.env['ir.config_parameter'].sudo().get_param('nafaz_client_secret_key', '')
        keycloak_openid = KeycloakOpenID(server_url=nafaz_server_url, client_id=nafaz_client_id,
                                         realm_name=nafaz_realm_name, client_secret_key=nafaz_client_secret_key)
        userinfo = dict()
        access_token = {}
        error = None

        if kwargs.get('code'):
            try:
                redirect_uri = request.httprequest.url_root.replace("http://", "https://")
                access_token = keycloak_openid.token(
                    grant_type='authorization_code',
                    code=kwargs.get('code'),
                    redirect_uri=redirect_uri + "jobs/apply/{}".format(job.id))
                if not access_token.get('access_token'):
                    error = True
                    _logger.info("***********************access_token***************************")
                    _logger.error('OAuth2: Access Token = ', access_token)
                userinfo = keycloak_openid.userinfo(access_token.get('access_token'))
                _logger.info("***********************userinfo*********************************")
                _logger.info('user info ==>', userinfo)
                if not userinfo:
                    _logger.error('OAuth2: User info = ', userinfo)
                    error = True
                date_string = userinfo['dob']
                date_object = datetime.strptime(date_string, "%a %b %d %H:%M:%S AST %Y")
                userinfo['dob'] = date_object.strftime("%Y-%m-%d")
                date_string = userinfo['cardIssueDateGregorian']
                date_object = datetime.strptime(date_string, "%a %b %d %H:%M:%S AST %Y")
                userinfo['cardIssueDateGregorian'] = date_object.strftime("%Y-%m-%d")
                self._fetch_and_update_address(userinfo)
            except Exception as e:
                _logger.error(
                    'OAuth2: access denied, redirect to main page in case a valid session exists, without setting cookies')
                _logger.error(e)
                error = True
            if error:
                url = "/web/login?oauth_error=2"
                redirect = werkzeug.utils.redirect(url, 303)
                redirect.autocorrect_location_header = False
                return redirect

        if not job.can_access_from_current_website():
            raise NotFound()

        error = {}
        default = {}
        if 'website_hr_recruitment_error' in request.session:
            error = request.session.pop('website_hr_recruitment_error')
            default = request.session.pop('website_hr_recruitment_default')

        response = request.render("website_hr_recruitment.apply", {
            'job': job,
            'userinfo': userinfo,
            'error': error,
            'default': default,
        })

        # Set security headers
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['Content-Security-Policy'] = "frame-ancestors 'none';"

        return response

    def _fetch_and_update_address(self, userinfo):
        nationality = userinfo['nationality']
        userid = userinfo['userid']
        client = get_client()
        if not client:
            raise UserError(_("Failed to initialize SOAP client."))
        identifier_type = 'NationalID' if nationality == 'Saudi Arabia' else 'IqamaNumber'
        try:
            response = client.service.GetIndividualWaselAddress(Identifier=userid, IdentifierType=identifier_type)

            if hasattr(response, 'ServiceError') and response.ServiceError:
                error_code = response.ServiceError.Code
                error_text = response.ServiceError.ErrorText
                handle_service_error(error_code, error_text)

            if hasattr(response, 'getIndividualWaselAddressResponseDetailObject'):
                detail_object = response.getIndividualWaselAddressResponseDetailObject
                if hasattr(detail_object, 'WaselAddress') and detail_object.WaselAddress:
                    address_details = detail_object.WaselAddress[0]
                    userinfo['postOfficeBox'] = address_details.ZipCode
                    userinfo['localityName'] = address_details.CityNameArabic
                    userinfo['buildingNumber'] = address_details.BuildingNumber
                    userinfo['street'] = address_details.StreetNameArabic

        except UserError:
            raise
        except Exception as e:
            _logger.error(f"Error calling GetIndividualWaselAddress: {e}")
            raise UserError(_("Unable to retrieve address: %s") % e)
        finally:
            if client:
                client.transport.session.close()

    # @http.route('''/get_nafaz_info/<model("hr.employee"):employee>''', auth="public", website=True)
    # def employees_info(self, employee, **kwargs):
    #     nafaz_server_url = request.env['ir.config_parameter'].sudo().get_param('nafaz_server_url', '')
    #     nafaz_client_id = request.env['ir.config_parameter'].sudo().get_param('nafaz_client_id', '')
    #     nafaz_realm_name = request.env['ir.config_parameter'].sudo().get_param('nafaz_realm_name', '')
    #     nafaz_client_secret_key = request.env['ir.config_parameter'].sudo().get_param('nafaz_client_secret_key', '')
    #     keycloak_openid = KeycloakOpenID(server_url=nafaz_server_url, client_id=nafaz_client_id, realm_name=nafaz_realm_name, client_secret_key=nafaz_client_secret_key)
    #     userinfo = dict()
    #     access_token = {}
    #     error = None
    #     print(kwargs)
    #     if kwargs.get('code'):
    #         try:
    #             access_token = keycloak_openid.token(
    #                 grant_type='authorization_code',
    #                 code=kwargs.get('code'),
    #                 redirect_uri=request.httprequest.url_root.replace("http://", "https://") + "get_nafaz_info/{}".format(employee.id))
    #             _logger.info("***********************access_token*********************************")
    #             if not access_token.get('access_token'):
    #                 error = True
    #                 _logger.error('OAuth2: Access Token = ', access_token)
    #
    #             userinfo = keycloak_openid.userinfo(access_token.get('access_token'))
    #             _logger.info(userinfo)
    #             if not userinfo:
    #                 _logger.error('OAuth2: User info = ', userinfo)
    #                 error = True
    #             date_string = userinfo['dob']
    #             date_object = datetime.strptime(date_string, "%a %b %d %H:%M:%S AST %Y")
    #             userinfo['dob'] = date_object.strftime("%Y-%m-%d")
    #             date_string = userinfo['cardIssueDateGregorian']
    #             date_object = datetime.strptime(date_string, "%a %b %d %H:%M:%S AST %Y")
    #             userinfo['cardIssueDateGregorian'] = date_object.strftime("%Y-%m-%d")
    #             employee.name = userinfo.get('arabicName', False) or employee.name
    #             employee.english_name = userinfo.get('englishName', False) or employee.english_name
    #             print(userinfo)
    #         except Exception as e:
    #             _logger.error('OAuth2: access denied, redirect to main page in case a valid session exists, without setting cookies')
    #             _logger.error(e)
    #             error = True
    #         if error:
    #             url = "/web/login?oauth_error=2"
    #             redirect = werkzeug.utils.redirect(url, 303)
    #             redirect.autocorrect_location_header = False
    #             return redirect
    #         else:
    #             return request.redirect(kwargs.get('state', False) or '/web')
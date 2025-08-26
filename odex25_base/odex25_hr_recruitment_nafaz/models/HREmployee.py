# -*- coding: utf-8 -*-
from odoo import models, fields, http, api,_
from keycloak import KeycloakOpenID
import logging
import werkzeug.urls
from ..client_utils import get_client, handle_service_error
from requests.exceptions import HTTPError, ConnectionError, Timeout
from odoo.exceptions import UserError
from lxml import etree
import json


instance = None
_logger = logging.getLogger(__name__)


class Employee(models.Model):
    _inherit = 'hr.employee'

    district_area_english = fields.Char('Address Region	')
    street_name_english = fields.Char('Street')
    city_name_english = fields.Char('City Name')
    drug_type = fields.Selection([('company_property', 'Company Property'), ('property', 'Employee Property'),('rent', 'Rent')])
    is_english_language = fields.Boolean(compute='_compute_user_language')

    def _compute_user_language(self):
        for rec in self:
            if self.env.user.lang == 'en_US':
                rec.is_english_language = True
            else:
                rec.is_english_language = False

    def _get_identifier(self):
        """Private method to get the identifier type and identifier value based on the employee's nationality."""
        if self.check_nationality:
            if self.saudi_number.saudi_id:
                return 'NationalID', self.saudi_number.saudi_id
            else:
                raise UserError(_("No Saudi ID found for the employee."))
        else:
            if self.iqama_number.iqama_id:
                return 'IqamaNumber', self.iqama_number.iqama_id
            else:
                raise UserError(_("No Iqama ID found for the employee."))

    def get_individual_address(self):
        """ Method to get the individual address from the external service and update the employee's address fields."""
        self.ensure_one()
        client = get_client()
        if not client:
            raise UserError(_("Failed to initialize SOAP client."))

        identifier_type, identifier = self._get_identifier()

        try:
            response = client.service.GetIndividualWaselAddress(Identifier=identifier, IdentifierType=identifier_type)
            _logger.info(f"Response: {response.ServiceError}")

            if hasattr(response, 'ServiceError') and response.ServiceError:
                error_code = response.ServiceError.Code
                error_text = response.ServiceError.ErrorText
                handle_service_error(error_code, error_text)

            if hasattr(response, 'getIndividualWaselAddressResponseDetailObject'):
                detail_object = response.getIndividualWaselAddressResponseDetailObject
                if hasattr(detail_object, 'WaselAddress') and detail_object.WaselAddress:
                    self.sudo()._update_address_fields(detail_object.WaselAddress[0])
                else:
                    raise UserError(_("No address details found in the response."))
            else:
                raise UserError(_("Unexpected response format from the service."))

        except UserError:
            raise
        except Exception as e:
            _logger.error(f"Error calling GetIndividualWaselAddress: {e}")
            raise UserError(_("Unable to retrieve address: %s") % e)
        finally:
            if client:
                client.transport.session.close()

    def _update_address_fields(self, address_details):
        """
        Private method to update employee address fields based on the address details from the response.
        """
        region = self.env['address.region'].search([('name', '=', address_details.DistrictAreaArabic)], limit=1)
        city = self.env['address.city'].search([('name', '=', address_details.CityNameArabic)], limit=1)
        country = self.env['res.country'].search([('code', '=', 'SA')], limit=1)

        if not region:
            region = self.env['address.region'].create({'name': address_details.DistrictAreaArabic})
        if not city:
            city = self.env['address.city'].create({'name': address_details.CityNameArabic})

        self.address_region = region.id
        self.address_city = city.id
        self.country_address_id = country.id
        self.sudo().write({
            'extra_number': address_details.AdditionalNumber,
            'building_number': address_details.BuildingNumber,
            'apartment_number': address_details.UnitNumber,
            'postal_code': address_details.ZipCode,
            'street': address_details.StreetNameArabic,
            'district_area_english': address_details.DistrictAreaEnglish,
            'street_name_english': address_details.StreetNameEnglish,
            'city_name_english': address_details.CityNameEnglish,
        })

    def get_nafaz_page(self):
        if self.user_id.id == self.env.user.id:
            nafaz_server_url = self.env['ir.config_parameter'].sudo().get_param('nafaz_server_url', '')
            nafaz_client_id = self.env['ir.config_parameter'].sudo().get_param('nafaz_client_id', '')
            nafaz_realm_name = self.env['ir.config_parameter'].sudo().get_param('nafaz_realm_name', '')
            nafaz_client_secret_key = self.env['ir.config_parameter'].sudo().get_param('nafaz_client_secret_key', '')
            keycloak_openid = KeycloakOpenID(server_url=nafaz_server_url, client_id=nafaz_client_id, realm_name=nafaz_realm_name, client_secret_key=nafaz_client_secret_key)
            redirect_uri = http.request.httprequest.url_root.replace("http://", "https://") + "get_nafaz_info/{}".format(self.id)
            callback_url = "/web#id={}&model=hr.employee&view_type=form".format(self.id)
            auth_url = keycloak_openid.auth_url(redirect_uri=redirect_uri, scope="openid+profile+email", state=callback_url)
            return {'name': 'Go to website','res_model': 'ir.actions.act_url','type': 'ir.actions.act_url','target': 'self', 'url': auth_url}
        else:
            raise UserError(_("The is allowed for this employee only %s") % self.name)
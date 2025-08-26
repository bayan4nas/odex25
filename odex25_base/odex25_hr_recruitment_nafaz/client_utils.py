# client_utils.py
import logging
from zeep import Client
from requests.exceptions import HTTPError, ConnectionError, Timeout
from odoo.exceptions import UserError
from odoo import _


_logger = logging.getLogger(__name__)

instance = None


def get_client():
    """
    Initialize and return the SOAP client instance.
    """
    global instance
    try:
        if instance is None:
            from zeep.transports import Transport
            from requests import Session
            wsdl = 'http://napigsb.saip.gov.sa:182/GSBExpress/Communication/Post/SPWaselAddress/2.0/SPWaselAddressService.svc?singleWsdl'
            session = Session()
            transport = Transport(session=session)
            instance = Client(wsdl, transport=transport)
            _logger.info("******** Created New instance ********")
        else:
            _logger.info("******** Using Existing instance ********")

        return instance

    except (HTTPError, ConnectionError, Timeout) as exception:
        _logger.error(f"Exception Name: {type(exception).__name__}")
        _logger.error(f"Exception Desc: {exception}")
        return None


def handle_service_error(error_code, error_text):
    """
    Handle service errors based on error codes.
    """
    if error_code == '001-000001':
        raise UserError(_("No records found"))
    elif error_code == '001-000100':
        raise UserError(_("You are not authorized by the provider"))
    elif error_code.startswith('500-'):
        raise UserError(_("Internal System Error: %s") % error_text)
    else:
        raise UserError(_("Unknown error: %s") % error_text)

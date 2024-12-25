# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo.addons.phone_validation.tools import phone_validation
from odoo import _
from odoo.exceptions import UserError

import logging

_logger = logging.getLogger(__name__)
_phonenumbers_lib_warning = False


try:
    import phonenumbers

    def phone_parse(number, country_code):
        try:
            phone_nbr = phonenumbers.parse(number, region=country_code or None, keep_raw_input=True)
        except phonenumbers.phonenumberutil.NumberParseException as e:
            raise UserError(
                _('Unable to parse %(phone)s: %(error)s', phone=number, error=str(e))
            ) from e

        if not phonenumbers.is_possible_number(phone_nbr):
            reason = phonenumbers.is_possible_number_with_reason(phone_nbr)
            if reason == phonenumbers.ValidationResult.INVALID_COUNTRY_CODE:
                raise UserError(_('Impossible number %s: not a valid country prefix.', number))
            if reason == phonenumbers.ValidationResult.TOO_SHORT:
                raise UserError(_('Impossible number %s: not enough digits.', number))
            # in case of "TOO_LONG", we may try to reformat the number in case it was
            # entered without '+' prefix or using leading '++' not always recognized;
            # in any case final error should keep the original number to ease tracking
            if reason == phonenumbers.ValidationResult.TOO_LONG:
                # people may enter 0033... instead of +33...
                if number.startswith('00'):
                    try:
                        phone_nbr = phone_parse(f'+{number.lstrip("00")}', country_code)
                    except UserError:
                        raise UserError(_('Impossible number %s: too many digits.', number))
                # people may enter 33... instead of +33...
                elif not number.startswith('+'):
                    try:
                        phone_nbr = phone_parse(f'+{number}', country_code)
                    except UserError:
                        raise UserError(_('Impossible number %s: too many digits.', number))
                else:
                    raise UserError(_('Impossible number %s: too many digits.', number))
            else:
                raise UserError(_('Impossible number %s: probably invalid number of digits.', number))
        if not phonenumbers.is_valid_number(phone_nbr):
            raise UserError(_('Invalid number %s: probably incorrect prefix.', number))

        return phone_nbr

    def phone_format(number, country_code, country_phone_code, force_format='INTERNATIONAL', raise_exception=True):
        """ Format the given phone number according to the localisation and international options.
        :param number: number to convert
        :param country_code: the ISO country code in two chars
        :type country_code: str
        :param country_phone_code: country dial in codes, defined by the ITU-T (Ex: 32 for Belgium)
        :type country_phone_code: int
        :param force_format: stringified version of format globals (see
          https://github.com/daviddrysdale/python-phonenumbers/blob/dev/python/phonenumbers/phonenumberutil.py)
            'E164' = 0
            'INTERNATIONAL' = 1
            'NATIONAL' = 2
            'RFC3966' = 3
        :type force_format: str
        :rtype: str
        """
        try:
            phone_nbr = phone_parse(number, country_code)
        except UserError:
            if raise_exception:
                raise
            return number
        if force_format == 'E164':
            phone_fmt = phonenumbers.PhoneNumberFormat.E164
        elif force_format == 'RFC3966':
            phone_fmt = phonenumbers.PhoneNumberFormat.RFC3966
        elif force_format == 'INTERNATIONAL' or phone_nbr.country_code != country_phone_code:
            phone_fmt = phonenumbers.PhoneNumberFormat.INTERNATIONAL
        else:
            phone_fmt = phonenumbers.PhoneNumberFormat.NATIONAL
        return phonenumbers.format_number(phone_nbr, phone_fmt)

    def phone_get_region_data_for_number(number):
        try:
            phone_obj = phone_parse(number, None)
        except (phonenumbers.phonenumberutil.NumberParseException, UserError):
            return {
                'code': '',
                'national_number': '',
                'phone_code': '',
            }
        return {
            'code': phonenumbers.phonenumberutil.region_code_for_number(phone_obj),
            'national_number': str(phone_obj.national_number),
            'phone_code': str(phone_obj.country_code),
        }

except ImportError:

    def phone_parse(number, country_code):
        return False

    def phone_format(number, country_code, country_phone_code, force_format='INTERNATIONAL', raise_exception=True):
        global _phonenumbers_lib_warning
        if not _phonenumbers_lib_warning:
            _logger.info(
                "The `phonenumbers` Python module is not installed, contact numbers will not be "
                "verified. Please install the `phonenumbers` Python module."
            )
            _phonenumbers_lib_warning = True
        return number

    def phone_get_region_code_for_number(number):
        return {
            'code': '',
            'national_number': '',
            'phone_code': '',
        }

def wa_phone_format(record, fname=False, number=False, country=None,
                    force_format="INTERNATIONAL", raise_exception=True):
    """ Format and return number. This number can be found using a field
    (in which case self should be a singleton recordet), or directly given
    if the formatting itself is what matter.

    :param <Model> record: linked record on which number formatting is
      performed, used to find number and/or country;
    :param str fname: if number is not given, fname indicates the field to
      use to find the number;
    :param str number: number to format (in which case fields-based computation
      is skipped);
    :param <res.country> country: country used for formatting number; otherwise
      it is fetched based on record or company;
    :param str force_format: stringified version of format globals; should be
      one of 'E164', 'INTERNATIONAL', 'NATIONAL' or 'RFC3966';

    :return str: formatted number. Return False is no nmber. If formatting
      fails an exception is raised;
    """
    if not number and record and fname:
        # if no number is given, having a singleton recordset is mandatory to
        # always have a number as input
        record.ensure_one()
        number = record[fname]
    if not number:
        return False

    # fetch country info only if record is a singleton recordset allowing to
    # effectively try to find a country
    if not country and record and 'country_id' in record:
        record.ensure_one()
        country = record.country_id
    if not country:
        country = record.env.company.country_id

    # as 'phone_format' returns original number if parsing fails, we have to
    # let it raise and handle the exception manually to deal with non formatted
    try:
        formatted = phone_validation.phone_format(
            number,
            country.code,
            country.phone_code,
            force_format=force_format if force_format != "WHATSAPP" else "E164",
            raise_exception=True,
        )
    except Exception:  # noqa: BLE001
        if raise_exception:
            raise
        formatted = False

    if formatted and force_format == "WHATSAPP":
        try:
            parsed = phone_validation.phone_parse(formatted, country.code)
        except Exception:  # noqa: BLE001
            if raise_exception:
                raise
            return False
        return f'{parsed.country_code}{parsed.national_number}'
    return formatted

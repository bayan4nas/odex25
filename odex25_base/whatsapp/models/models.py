# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import exceptions, models, api, _
from odoo.addons.phone_validation.tools import phone_validation


class BaseModel(models.AbstractModel):
    _inherit = 'base'

    def _find_value_from_field_path(self, field_path):
        """ Get the value of field, returning display_name(s) if the field is a
        model. Can be called on a void recordset, in which case it mainly serves
        as a field path validation. """
        if self:
            self.ensure_one()

        # as we use mapped(False) returns record, better return a void string
        if not field_path:
            return ''

        try:
            field_value = self.mapped(field_path)
        except KeyError as err:
            raise exceptions.UserError(
                _("'%(field)s' does not seem to be a valid field path", field=field_path)
            ) from err
        except Exception as err:  # noqa: BLE001
            raise exceptions.UserError(
                _("We were not able to fetch value of field '%(field)s'", field=field_path)
            ) from err
        if isinstance(field_value, models.Model):
            return ' '.join((value.display_name or '') for value in field_value)
        return ' '.join(str(value if value is not False and value is not None else '') for value in field_value)

    def _whatsapp_get_portal_url(self):
        """ List is defined here else we need to create bridge modules. """
        if self._name in {
            'sale.order',
            'account.move',
            'project.project',
            'project.task',
            'purchase.order',
            'helpdesk.ticket',
        } and hasattr(self, 'get_portal_url'):
            self.ensure_one()
            return self.get_portal_url()
        contactus_page = self.env.ref('website.contactus_page', raise_if_not_found=False)
        return contactus_page.url if contactus_page else False

    def _whatsapp_get_responsible(self, related_message=False, related_record=False, whatsapp_account=False):
        """ Try to find suitable responsible users for a record.
         This is typically used when trying to find who to add to the discuss.channel created when
         a customer replies to a sent 'whatsapp.template'. In short: who should be notified.

         Heuristic is as follows:
         - Try to find a 'user_id/user_ids' field on the record, use that as responsible if available;
         - Always add the author of the original message
           (If you send a template to a customer, you should be able to reply to his questions.)
         - If nothing found, fallback on the first available among the following:
           - The creator of the record
           - The last editor of the record
           - Ultimate fallback is the people configured as 'notify_user_ids' on the whatsapp account

        For each of those, we only take into account active internal users, that are not the
        superuser, to avoid having the responsible set to 'Odoobot' for automated processes.

        This method can be overridden to force specific responsible users. """

        self.ensure_one()
        responsible_users = self.env['res.users']

        def filter_suitable_users(user):
            return user.active and user._is_internal() and not user._is_superuser()

        for field in ['user_id', 'user_ids']:
            if field in self._fields and self[field]:
                responsible_users = self[field].filtered(filter_suitable_users)

        if related_message:
            # add the message author even if we already have a responsible
            responsible_users |= related_message.author_id.user_ids.filtered(filter_suitable_users)

        if responsible_users:
            # do not go further if we found suitable users
            return responsible_users

        if related_message and not related_record:
            related_record = self.env[related_message.model].browse(related_message.res_id)

        if related_record:
            responsible_users = related_record.create_uid.filtered(filter_suitable_users)

            if not responsible_users:
                responsible_users = related_record.write_uid.filtered(filter_suitable_users)

        if not responsible_users:
            if not whatsapp_account:
                whatsapp_account = self.env['whatsapp.account'].search([], limit=1)

            responsible_users = whatsapp_account.notify_user_ids

        return responsible_users

    def _phone_format(self, fname=False, number=False, country=False, force_format='E164', raise_exception=False):
        """ Format and return number. This number can be found using a field
        (in which case self should be a singleton recordet), or directly given
        if the formatting itself is what matter. Field name can be found
        automatically using '_phone_get_number_fields'

        :param str fname: if number is not given, fname indicates the field to
          use to find the number; otherwise use '_phone_get_number_fields';
        :param str number: number to format (in which case fields-based computation
          is skipped);
        :param <res.country> country: country used for formatting number; otherwise
          it is fetched based on record, using '_phone_get_country_field';
        :param str force_format: stringified version of format globals; should be
          one of 'E164', 'INTERNATIONAL', 'NATIONAL' or 'RFC3966';
        :param bool raise_exception: raise if formatting is not possible (notably
          wrong formatting, invalid country information, ...). Otherwise False
          is returned;

        :return str: formatted number. If formatting is not possible False is
          returned.
        """
        if not number:
            # if no number is given, having a singletong recordset is mandatory to
            # always have a number as input
            self.ensure_one()
            fnames = self._phone_get_number_fields() if not fname else [fname]
            number = next((self[fname] for fname in fnames if fname in self and self[fname]), False)
        if not number:
            return False

        # fetch country info only if self is a singleton recordset allowing to
        # effectively try to find a country
        if not country and self:
            self.ensure_one()
            country_fname = self._phone_get_country_field()
            country = self[country_fname] if country_fname and country_fname in self else self.env['res.country']
        if not country:
            country = self.env.company.country_id

        return self._phone_format_number(
            number,
            country=country, force_format=force_format,
            raise_exception=raise_exception,
        )

    @api.model
    def _phone_get_country_field(self):
        if 'country_id' in self:
            return 'country_id'
        return False

    def _phone_format_number(self, number, country, force_format='E164', raise_exception=False):
        """ Format and return number according to the asked format. This is
        mainly a small helper around 'phone_validation.phone_format'."""
        if not number or not country:
            return False

        try:
            number = phone_validation.phone_format(
                number,
                country.code,
                country.phone_code,
                force_format=force_format,
                raise_exception=True,  # do not get original number returned
            )
        except exceptions.UserError:
            if raise_exception:
                raise
            number = False
        return number



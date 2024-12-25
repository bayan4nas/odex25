# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, tools

class MailThread(models.AbstractModel):
    _inherit = 'mail.thread'

    def _get_mail_thread_data(self, request_list):
        res = super()._get_mail_thread_data(request_list)
        res['canSendWhatsapp'] = self.env['whatsapp.template']._can_use_whatsapp(self._name)
        return res

    def _track_set_log_message(self, message):
        """ Link tracking to a message logged as body, in addition to subtype
        description (if set) and tracking values that make the core content of
        tracking message. """
        if not self._track_get_fields():
            return
        body_values = self.env.cr.precommit.data.setdefault(f'mail.tracking.message.{self._name}', {})
        for id_ in self.ids:
            body_values[id_] = message

    @tools.ormcache('self.env.uid', 'self.env.su')
    def _track_get_fields(self):
        """ Return the set of tracked fields names for the current model. """
        model_fields = {
            name
            for name, field in self._fields.items()
            if getattr(field, 'tracking', None) or getattr(field, 'track_visibility', None)
        }

        return model_fields and set(self.fields_get(model_fields, attributes=()))





class PhoneMixin(models.AbstractModel):
    _inherit = 'mail.thread.phone'
    _phone_search_min_length = 3

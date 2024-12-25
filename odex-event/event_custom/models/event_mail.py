# -*- coding: utf-8 -*-

from datetime import datetime
from dateutil.relativedelta import relativedelta

from odoo import api, fields, models, tools
from odoo.tools import exception_to_unicode
from odoo.tools.translate import _

import random
import logging
_logger = logging.getLogger(__name__)

_INTERVALS = {
    'hours': lambda interval: relativedelta(hours=interval),
    'days': lambda interval: relativedelta(days=interval),
    'weeks': lambda interval: relativedelta(days=7*interval),
    'months': lambda interval: relativedelta(months=interval),
    'now': lambda interval: relativedelta(hours=0),
}



class EventMailScheduler(models.Model):
    _inherit = 'event.mail'

    interval_type = fields.Selection(selection_add = [('after_change_tracks', 'After Change in Tracks')],ondelete={'after_change_tracks': 'set default'})
    mail_track_ids = fields.One2many('event.mail.track', 'scheduler_id')

    # @api.one
    @api.depends('mail_sent', 'interval_type', 'event_id.registration_ids','mail_track_ids','mail_track_ids.mail_sent', 'mail_registration_ids')
    def _compute_done(self):
        """
        overwrite to include new interval type After Change in Tracks
        """
        if self.interval_type in ['before_event', 'after_event']:
            self.done = self.mail_sent
        elif self.interval_type in ['after_sub']:
            self.done = len(self.mail_registration_ids) == len(self.event_id.registration_ids) and all(mail.mail_sent for mail in self.mail_registration_ids)
        else:
            self.done = all(mail.mail_sent for mail in self.mail_track_ids)

    # @api.one
    def execute(self):
        """
        inherit to include new interval type After Change in Tracks
        """
        result = super(EventMailScheduler, self).execute()
        now = fields.Datetime.now()
        if self.interval_type == 'after_change_tracks' and self._context.get('track_change',False):
            # update Tracks change lines
            track_change = self._context.get('track_change',False)
            lines = [
                (0, 0, {'track_id': track_change['id'],'change_date_from':track_change['change_date_from'],'change_date_to':track_change['change_date_to']})
            ]
            if lines:
                self.write({'mail_track_ids': lines})
            # execute scheduler on registrations
            self.mail_track_ids.execute()
        return result



class EventMailRegistration(models.Model):
    _name = 'event.mail.track'
    _description = 'Tracks change Mail Scheduler'
    _rec_name = 'scheduler_id'
    _order = 'change_date_to DESC'

    scheduler_id = fields.Many2one('event.mail', 'Mail Scheduler', required=True, ondelete='cascade')
    track_id = fields.Many2one('event.track', 'Tracks', required=True, ondelete='cascade')
    change_date_from = fields.Datetime('Old Time')
    change_date_to = fields.Datetime('New Time')
    mail_sent = fields.Boolean('Mail Sent')

    # @api.one
    def execute(self):
        if not self.mail_sent:
            for registration in self.track_id.event_id.registration_ids:
                self.scheduler_id.template_id.send_mail(registration.id)
            self.write({'mail_sent': True})

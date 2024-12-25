# -*- coding: utf-8 -*-

import datetime
from odoo import api, fields, models


class Event(models.Model):
    _inherit = 'event.event'

    # Initial date and scale of the track gantt view
    track_gantt_initial_date = fields.Date(compute='_compute_track_gantt_information')
    track_gantt_scale = fields.Char(compute='_compute_track_gantt_information')
    remaining_days = fields.Integer(string='Remaining Days', compute='_compute_remaining_time', store=True)
    remaining_hours = fields.Char(string='Remaining Time', compute='_compute_remaining_time', store=True)
    Description_event = fields.Text(string='Description event')
    link = fields.Char(string='Event website link', readonly=False)
    address_id = fields.Many2one(
        'res.partner', string='Venue', default=lambda self: self.env.company.partner_id.id,
        tracking=True, domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")

    @api.depends('date_begin', 'date_end')
    def _compute_remaining_time(self):
        now = fields.Datetime.now()
        for record in self:
            if record.date_end and now < record.date_end:
                delta = record.date_end - now
                total_seconds = delta.total_seconds()
                record.remaining_days = int(total_seconds // (24 * 3600))
                remaining_seconds_after_days = total_seconds % (24 * 3600)
                hours = int(remaining_seconds_after_days // 3600)
                minutes = int((remaining_seconds_after_days % 3600) // 60)
                seconds = int(remaining_seconds_after_days % 60)

                record.remaining_hours = f"{hours:02}:{minutes:02}:{seconds:02}"
            else:
                record.remaining_days = 0
                record.remaining_hours = "00:00:00"

    @api.depends('track_ids.date', 'track_ids.date_end', 'date_begin', 'date_end')
    def _compute_track_gantt_information(self):
        for event in self:
            first_date = min([event.date_begin] + [track.date for track in event.track_ids if track.date])
            last_date = max([event.date_end] + [track.date_end for track in event.track_ids if track.date_end])

            if first_date and last_date:
                duration = last_date - first_date
                if duration / datetime.timedelta(days=30) > 1:
                    event.track_gantt_scale = 'year'
                elif duration / datetime.timedelta(weeks=1) > 1:
                    event.track_gantt_scale = 'month'
                elif duration / datetime.timedelta(days=1) > 1:
                    event.track_gantt_scale = 'week'
                else:
                    event.track_gantt_scale = 'day'

                event.track_gantt_initial_date = first_date
            else:
                event.track_gantt_scale = False
                event.track_gantt_initial_date = False

# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

import datetime
from odoo import api, fields, models, tools, _
from dateutil.relativedelta import relativedelta
import logging

_logger = logging.getLogger(__name__)


class HelpdeskStage(models.Model):
    _inherit = 'odex25_helpdesk.stage'

    is_reopen = fields.Boolean('Re-open Kanban Stage', help="in this stage the ticket will be opened again if the "
                                                            "customer""replied to your close stage email")
    reopen_time = fields.Float(string="Reopen Time", help="the time that make a ticket reopen task")
    is_auto_close = fields.Boolean('Auto Close Kanban Stage',help="in this stage the ticket will be closed again if "
                                                                  "the customer not send email")
    close_time = fields.Float(string="Close Time", help="the time that make a ticket close task")
    is_done = fields.Boolean(string="Close Ticket")


class HelpdeskTicket(models.Model):
    _inherit = 'odex25_helpdesk.ticket'

    def _message_post_after_hook(self, message, msg_vals):
        if self.partner_email and self.partner_id and not self.partner_id.email:
            self.partner_id.email = self.partner_email

        if self.partner_email and not self.partner_id:
            # we consider that posting a message with a specified recipient (not a follower, a specific one)
            # on a document without customer means that it was created through the chatter using
            # suggested recipients. This heuristic allows to avoid ugly hacks in JS.
            new_partner = message.partner_ids.filtered(lambda partner: partner.email == self.partner_email)
            if new_partner:
                self.search([
                    ('partner_id', '=', False),
                    ('partner_email', '=', new_partner.email),
                    ('stage_id.fold', '=', False)]).write({'partner_id': new_partner.id})
        if message.author_id:
            if message.author_id.email == self.partner_email and self.stage_id.is_close:
                previous = self.env['mail.message'].search([
                    ('res_id', '=', self.id),
                    ('subject', '!=', ''),
                    ('model', '=', 'odex25_helpdesk.ticket'),
                    ('author_id', '!=', self.partner_id.id),
                ])
                if len(previous) != 0 and previous[0]:
                    previous = previous[0]
                    for stage in self.team_id.stage_ids:
                        if stage.is_reopen:
                            difference = fields.Datetime.from_string(message.date) - fields.Datetime.from_string(
                                previous.date)
                            difference = str(difference).split(':')
                            hour, minute = divmod(stage.reopen_time, 1)
                            minute *= 60
                            result = '{}:{}'.format(int(hour), int(minute))
                            result = result.split(':')
                            if int(difference[0]) < int(result[0]):
                                self.stage_id = stage.id
                                break
                            elif int(difference[1]) <= int(result[1]):
                                self.stage_id = stage.id

        return super(HelpdeskTicket, self)._message_post_after_hook(message, msg_vals)

    @api.model
    def automatic_close_state(self):
        ticket = self.env['odex25_helpdesk.ticket'].search([])
        is_done = self.env['odex25_helpdesk.stage'].search([('is_done', '=', True)], limit=1)
        for rec in ticket:
            if rec.stage_id.is_auto_close:
                close_time = rec.stage_id.close_time
                hour, minute = divmod(close_time, 1)
                minute *= 60
                to_str = fields.Datetime.to_string(
                    fields.Datetime.from_string(fields.Datetime.now()) - relativedelta(hours=hour, minutes=int(minute)))
                if not rec.stage_id.is_close:
                    msg_res = rec.message_ids.filtered(lambda x: str(x.date) < to_str)
                    if len(rec.message_ids) == len(msg_res):
                        rec.stage_id = is_done.id

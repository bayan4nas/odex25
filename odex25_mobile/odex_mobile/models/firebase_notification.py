import logging

from odoo import api, models, fields, _
from odoo.exceptions import UserError
import uuid

_logger = logging.getLogger(__name__)


class FirebaseNotification(models.Model):
 
    _name = "firebase.notification"
    _description = "Notification to send to Firebase Cloud Messaging"
    _order = "send_date desc, id desc"

    partner_ids = fields.Many2many("res.partner", string="Partners", readonly=False)
    title = fields.Char(required=True)
    body = fields.Char(required=True)
    meta = fields.Char()
    uid = fields.Char(default=str(uuid.uuid4()))
    send_date = fields.Datetime(copy=False)
    is_system = fields.Boolean()
    sent = fields.Boolean(readonly=True, copy=False)
    viewed = fields.Boolean(readonly=True, copy=False)
    iso_date = fields.Char(string='End Date', compute='_get_last_period')

    # #@api.one
    # @api.depends()
    # def _get_last_period(self):
    #     for record in self:
    #         self.iso_date = str(fields.Datetime.from_string(record.create_date).astimezone().replace(microsecond=0).isoformat())

    @api.depends('write_date')
    def _get_last_period(self):
        for record in self:
            if record.write_date:
                iso_datetime = record.write_date.astimezone().replace(microsecond=0).isoformat()
                record.iso_date = str(iso_datetime)
            else:
                record.iso_date = False

    #@api.multi
    def action_view(self):
        for rec in self:
            rec.viewed = True

    @api.constrains("send_date")
    def _check_date(self):
        for notif in self:
            if notif.send_date is False:
                continue

            dt = fields.Datetime.now()
            if notif.send_date < dt:
                raise UserError(_("Send date should be in the future"))

    #@api.multi
    def send(self, **kwargs):
        if kwargs is None:
            kwargs = {}
        for notif in self:
            registration_ids = self.env["firebase.registration"].search(
                [("partner_id", "in", notif.partner_ids.ids)]
            )
            kwargs.update(
                {"notification_id": str(notif.id), }
            )
            notif.sent = registration_ids.send_message(notif.title, notif.body, kwargs)
            if notif.sent:
                notif.send_date = fields.Datetime.now()


    def notification_cron(self):
        dt = fields.Datetime.now()
        self.search([("sent", "=", False), ("send_date", "<", dt)]).send()

        return True



from odoo import models
from odoo.http import request, SessionExpiredException
from odoo.service import security
from odoo.addons.bus.models.bus import dispatch
from ...tools.websocket import wsrequest
import re

# todo from odoo/addons/bus/models/ir_websocket.py


class IrWebsocket(models.AbstractModel):
    _name = 'ir.websocket'
    _description = 'websocket message handling'

    def _get_im_status(self, im_status_ids_by_model):
        im_status = {}
        if 'res.partner' in im_status_ids_by_model:
            im_status['Persona'] = [{**p, 'type': "partner"} for p in self.env['res.partner'].with_context(active_test=False).search_read(
                [('id', 'in', im_status_ids_by_model['res.partner'])],
                ['im_status']
            )]
        # whatsapp custom code -----------------------------------------------
        if "mail.guest" in im_status_ids_by_model:
            # sudo: mail.guest - necessary to read im_status from other guests, information is not considered sensitive
            im_status["Persona"] += [{**g, 'type': "guest"} for g in (
                self.env["mail.guest"]
                .sudo()
                .with_context(active_test=False)
                .search_read([("id", "in", im_status_ids_by_model["mail.guest"])], ["im_status"])
            )]
        # whatsapp custom code -----------------------------------------------
        return im_status

    def _build_bus_channel_list(self, channels):
        """
            Return the list of channels to subscribe to. Override this
            method to add channels in addition to the ones the client
            sent.

            :param channels: The channel list sent by the client.
        """
        # whatsapp custom code -----------------------------------------------
        channels = list(channels)  # do not alter original list
        discuss_channel_ids = list()
        for channel in list(channels):
            if isinstance(channel, str) and channel.startswith("mail.guest_"):
                channels.remove(channel)
                guest = self.env["mail.guest"]._get_guest_from_token(channel.split("_")[1])
                if guest:
                    self = self.with_context(guest=guest)
            if isinstance(channel, str):
                match = re.findall(r'discuss\.channel_(\d+)', channel)
                if match:
                    channels.remove(channel)
                    discuss_channel_ids.append(int(match[0]))
        guest = self.env["mail.guest"]._get_guest_from_context()
        if guest:
            channels.append(guest)
        domain = ["|", ("is_member", "=", True), ("id", "in", discuss_channel_ids)]
        channels.extend(self.env["discuss.channel"].search(domain))
        # whatsapp custom code -----------------------------------------------
        req = request or wsrequest
        channels.append('broadcast')
        if req.session.uid:
            channels.append(self.env.user.partner_id)
        return channels

    def _subscribe(self, data):
        if not all(isinstance(c, str) for c in data['channels']):
            raise ValueError("bus.Bus only string channels are allowed.")
        last_known_notification_id = self.env['bus.bus'].sudo().search([], limit=1, order='id desc').id or 0
        if data['last'] > last_known_notification_id:
            data['last'] = 0
        channels = set(self._build_bus_channel_list(data['channels']))
        dispatch.subscribe(channels, data['last'], self.env.registry.db_name, wsrequest.ws)

    def _update_bus_presence(self, inactivity_period, im_status_ids_by_model):
        if self.env.user and not self.env.user._is_public():
            self.env['bus.presence'].update_presence(
                inactivity_period,
                identity_field='user_id',
                identity_value=self.env.uid
            )
            im_status_notification = self._get_im_status(im_status_ids_by_model)
            if im_status_notification:
                self.env['bus.bus']._sendone(self.env.user.partner_id, 'mail.record/insert', im_status_notification)
        # whatsapp custom code -----------------------------------------------
        if not self.env.user or self.env.user._is_public():
            guest = self.env["mail.guest"]._get_guest_from_context()
            if not guest:
                return
            # sudo: bus.presence - guests currently need sudo to write their own presence
            self.env["bus.presence"].sudo().update_presence(
                inactivity_period,
                identity_field="guest_id",
                identity_value=guest.id,
            )
        # whatsapp custom code -----------------------------------------------


    @classmethod
    def _authenticate(cls):
        if wsrequest.session.uid is not None:
            if not security.check_session(wsrequest.session, wsrequest.env):
                wsrequest.session.logout(keep_db=True)
                raise SessionExpiredException()
        else:
            public_user = wsrequest.env.ref('base.public_user')
            wsrequest.update_env(user=public_user.id)

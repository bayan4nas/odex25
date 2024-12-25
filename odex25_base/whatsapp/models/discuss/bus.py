# -*- coding: utf-8 -*-
import contextlib
import datetime
import json
import logging
import os
import random
import selectors
import threading
import time
from psycopg2 import InterfaceError, sql

import odoo
from odoo import api, fields, models
from odoo.service.server import CommonServer
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools import date_utils

_logger = logging.getLogger(__name__)

# longpolling timeout connection
TIMEOUT = 50

# custom function to call instead of default PostgreSQL's `pg_notify`
ODOO_NOTIFY_FUNCTION = os.getenv('ODOO_NOTIFY_FUNCTION', 'pg_notify')

#----------------------------------------------------------
# Bus
#----------------------------------------------------------
# def json_dump(v):
#     return json.dumps(v, separators=(',', ':'), default=date_utils.json_default)
#
# def hashable(key):
#     if isinstance(key, list):
#         key = tuple(key)
#     return key


def channel_with_db(dbname, channel):
    if isinstance(channel, models.Model):
        return (dbname, channel._name, channel.id)
    if isinstance(channel, str):
        return (dbname, channel)
    return channel
def json_dump(v):
    return json.dumps(v, separators=(',', ':'), default=date_utils.json_default)

class ImBus(models.Model):
    _inherit = 'bus.bus'

    @api.model
    def _sendone(self, channel, notification_type, message):
        self._sendmany([[channel, notification_type, message]])

    @api.model
    def _sendmany(self, notifications):
        channels = set()
        values = []
        for target, notification_type, message in notifications:
            channel = channel_with_db(self.env.cr.dbname, target)
            channels.add(channel)
            values.append({
                'channel': json_dump(channel),
                'message': json_dump({
                    'type': notification_type,
                    'payload': message,
                })
            })
        self.sudo().create(values)
        if channels:
            # We have to wait until the notifications are commited in database.
            # When calling `NOTIFY imbus`, notifications will be fetched in the
            # bus table. If the transaction is not commited yet, there will be
            # nothing to fetch, and the websocket will return no notification.
            @self.env.cr.postcommit.add
            def notify():
                with odoo.sql_db.db_connect('postgres').cursor() as cr:
                    query = sql.SQL("SELECT {}('imbus', %s)").format(sql.Identifier(ODOO_NOTIFY_FUNCTION))
                    cr.execute(query, (json_dump(list(channels)), ))


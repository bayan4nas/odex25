# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request
import logging


class AutoLogoutIdleUSer(http.Controller):

    @http.route('/get_idle_time/timer', auth='public', type='json')
    def get_idle_time(self):
        if request.env.user.sudo().company_id.idle_time:
            return request.env.user.sudo().company_id.idle_time

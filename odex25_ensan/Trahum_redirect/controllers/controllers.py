# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class LoginRedirect(http.Controller):
    @http.route('/', type='http', auth='public', website=True)
    def redirect_to_login(self, **kwargs):
        return request.redirect('/web')


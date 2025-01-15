# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class LoginRedirect(http.Controller):
    @http.route('/', type='http', auth='public', website=True)
    def redirect_to_login(self, **kwargs):
        # إعادة التوجيه مباشرة إلى صفحة تسجيل الدخول
        return request.redirect('/web/login')


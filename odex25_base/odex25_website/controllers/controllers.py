# -*- coding: utf-8 -*-
from odoo import http


class OdexSupport(http.Controller):
    @http.route('/help', type='http', auth='public', website=True)
    def help(self, **kw):
        return http.request.render("odex25_website.help")


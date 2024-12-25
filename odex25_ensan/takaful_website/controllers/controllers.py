# -*- coding: utf-8 -*-
from odoo import http
from odoo.http import request

class TakafulWebsite(http.Controller):
    
    @http.route('/registration', type='http', auth='public', website=True)
    def registration(self, **kw):
        # redirect user incase it was loged in 
        # if request.env.user.id != request.env.ref('base.public_user').id:
        #     return http.request.redirect('/')
        return http.request.render("takaful_website.portal_global_registration")

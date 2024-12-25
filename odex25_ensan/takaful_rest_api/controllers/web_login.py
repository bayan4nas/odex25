from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal

class MyHome(CustomerPortal):

    @http.route('/my', type='http', auth="user", website=True)
    def home(self, **kw):
        partner = http.request.env['res.partner'].sudo().search([('id', '=', request.env.user.partner_id.id)], limit=1)
        if partner.account_type == 'volunteer':
            return request.redirect("/profile")
        elif partner.account_type == 'benefit':
            return request.redirect("/benefit_profile")
        elif partner.account_type == 'sponsor':
            return request.redirect("/sponsor_profile")
        else:
            # return super(AccountPortal, self).index(*args, **kw)
            return super(MyHome, self).home(**kw)
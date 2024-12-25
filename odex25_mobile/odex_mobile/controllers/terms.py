from odoo import http
from odoo.http import request


class TermsController(http.Controller):

    @http.route(["/rest_api/odexss/terms", "/web/odexss/terms", "/rest_api/myodex/terms", "/web/myodex/terms", ],
        type="http",
        auth="none",
        csrf=False,
        cors="*",
        methods=["GET"],
    )
    def terms_of_user(self, **kw):
        return http.request.render("odex_mobile.terms_of_use", {})

    @http.route(["/rest_api/odexss/privacy", "/web/odexss/privacy", "/web/myodex/privacy", "/rest_api/myodex/privacy", ],
        type="http",
        auth="none",
        csrf=False,
        cors="*",
        methods=["GET"],
    )
    def privacy_policy(self, **kw):
        return http.request.render("odex_mobile.privacy_policy", {})

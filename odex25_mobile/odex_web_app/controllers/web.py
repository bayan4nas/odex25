import odoo
from odoo import http
from odoo.http import request


class WebController(http.Controller):
    @http.route('/web/session/authenticate', type='json', auth="none")
    def authenticate(self, login, password, base_location=None):
        db = odoo.tools.config.get('db_name')
        if not db:
            response_data = {
                "error": "Database name should be specified in Conf File",
                "status": 400
            }
            return response_data

        request.session.authenticate(db, login, password)
        return request.env['ir.http'].session_info()

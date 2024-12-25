from odoo import http, _
from odoo.http import request

class LogViewer(http.Controller):

    @http.route('/log_viewer', type='http', auth='public')
    def log_viewer(self, password=None):
        correct_password = request.env['ir.config_parameter'].sudo().get_param('odoo_log_viewer.password')

        if password == correct_password:
            return request.render('odoo_log_viewer.log_viewer_template', {})
        else:
            return request.render('odoo_log_viewer.password_template', {})

    @http.route('/log_viewer/get_logs', type='json', auth='public')
    def get_logs(self, password=None):
        correct_password = request.env['ir.config_parameter'].sudo().get_param('odoo_log_viewer.password')

        if password == correct_password:
            log_entries = request.env['log.handler.manager'].sudo().get_log_entries()
            return {'log_content': '\n'.join(log_entries)}

        else:
            return {'error': 'Invalid password'}


import base64
from odoo import http
from odoo.http import request
import urllib.parse  # For URL encoding


class MyAttachmentController(http.Controller):
    @http.route('/browse/document/<int:id>', type='http', auth="public")
    def browse_document(self, id):
        model = 'ir.attachment'
        attachment = request.env[model].sudo().browse(id)

        if not attachment.exists() or not attachment.datas:
            return request.not_found()

        # Decode the file content
        file_data = base64.b64decode(attachment.datas)
        file_mimetype = attachment.mimetype or 'application/octet-stream'

        # URL-encode the filename for non-ASCII characters
        filename = urllib.parse.quote(attachment.name)

        # Set HTTP headers with the URL-encoded filename
        http_headers = [
            ('Content-Type', file_mimetype),
            ('Content-Length', str(len(file_data))),
            ('Content-Disposition', f'inline; filename*=UTF-8\'\'{filename}')
        ]

        return request.make_response(file_data, headers=http_headers)

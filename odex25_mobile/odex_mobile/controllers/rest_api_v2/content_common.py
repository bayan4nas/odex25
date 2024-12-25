import base64
from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)

class MyController(http.Controller):

    @http.route([
        '/api/content',
        '/api/content/<string:xmlid>',
        '/api/content/<string:xmlid>/<string:filename>',
        '/api/content/<int:id>',
        '/api/content/<int:id>/<string:filename>',
        '/api/content/<int:id>-<string:unique>',
        '/api/content/<int:id>-<string:unique>/<string:filename>',
        '/api/content/<int:id>-<string:unique>/<path:extra>/<string:filename>',
        '/api/content/<string:model>/<int:id>/<string:field>',
        '/api/content/<string:model>/<int:id>/<string:field>/<string:filename>'
    ], type='http', auth="none", csrf=False)
    def content_common(self, xmlid=None, model='ir.attachment', id=None, field='datas',
                       filename=None, filename_field='name', unique=None, mimetype=None,
                       download=None, data=None, token=None, access_token=None, **kw):
        try:
            # _logger.info("Processing request for content: xmlid=%s, model=%s, id=%s, field=%s", xmlid, model, id, field)
            # Access the binary content of the attachment
            if model == 'ir.attachment':
                attachment = request.env['ir.attachment'].sudo().browse(int(id))
                attachment.public = True
            status, headers, content = request.env['ir.http'].sudo().binary_content(
                xmlid=xmlid, model=model, id=id, field=field, unique=unique, filename=filename,
                filename_field=filename_field, download=download, mimetype=mimetype, access_token=access_token)
            if status != 200:
                # _logger.error("Failed to retrieve content: status=%s, headers=%s, content=%s", status, headers, content)
                return request.env['ir.http']._response_by_status(status, headers, content)
            else:
                content_base64 = base64.b64decode(content)
                headers.append(('Content-Length', str(len(content_base64))))
                response = request.make_response(content_base64, headers)
                if token:
                    response.set_cookie('fileToken', token)
                return response
        except Exception as e:
            _logger.error("An error occurred while processing the content request: %s", str(e), exc_info=True)
            return request.env['ir.http']._response_by_status(500, [], str(e))
    @http.route([
        '/api/download_attachment',
        '/api/download_attachment/<int:id>',
        '/api/download_attachment/<int:id>/<string:filename>'
    ], type='http', auth="none", csrf=False)
    def download_attachment(self, id=None, filename=None, **kw):
        try:
            if not id:
                return request.make_response("Attachment ID not provided", status=400)

            attachment = request.env['ir.attachment'].sudo().browse(id)
            print(attachment)
            if not attachment.exists():
                return request.make_response("Attachment not found", status=404)

            if not attachment.public:
                return request.make_response("Access denied to private attachment", status=403)

            content = base64.b64decode(attachment.datas)
            headers = [
                ('Content-Type', attachment.mimetype),
                ('Content-Length', len(content)),
                ('Content-Disposition', f'attachment; filename={filename or attachment.name}')
            ]

            return request.make_response(content, headers)
        except Exception as e:
            _logger.error("An error occurred while processing the download request: %s", str(e), exc_info=True)
            return request.make_response("Internal Server Error", status=500)
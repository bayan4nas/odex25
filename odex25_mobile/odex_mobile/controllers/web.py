import werkzeug
import odoo
import base64
from odoo import http
from odoo.http import request
from ..util import util
from odoo.tools import (
    image_process,
)

import logging

_logger = logging.getLogger(__name__)

FILETYPE_BASE64_MAGICWORD = {
    b"/": "jpg",
    b"R": "gif",
    b"i": "png",
    b"P": "svg+xml",
}


class WebController(http.Controller):
    @http.route(
        [
            "/rest_api/web/avatar/<int:id>",
            "/rest_api/web/avatar/<int:id>/<string:size>",
            "/web/avatar/<int:id>",
            "/web/avatar/<int:id>/<string:size>",
        ],
        auth="public",
        csrf=False,
        cors="*",
    )
    def avatar(self, id=None, size="1920", **kw):
        headers = []
        try:
            user = request.env["res.users"].sudo().browse(id)

            if user:
                field_size = "image"
                resize = True
                if size in ["medium", "small", "1920"]:
                    field_size = "%s_%s" % (field_size, size)
                    resize = False
                content = getattr(user, field_size)
                status, headers, image_base64 = request.env["ir.http"].binary_content(
                    model="res.users",
                    id=int(id),
                    field=field_size,
                )
                width, height = odoo.tools.image_guess_size_from_field_name(field_size)
                image_base64 = image_process(
                    image_base64,
                    size=(int(width), int(height)),
                    crop=False,
                    quality=int(0),
                )

        except Exception as ex:
            image_base64 = base64.b64decode(
                "R0lGODlhAQABAIABAP///wAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=="
            )
            mimetype = "image/gif"
            _logger.error(str(ex))
        finally:
            content = base64.b64decode(image_base64)
            headers = http.set_safe_image_headers(headers, content)
            response = request.make_response(content, headers)
            response.status_code = status
            return response

    def placeholder(self, image="no_image.gif"):
        _logger.info(util.path("lokate", "static", "img", image))
        return open(util.path("lokate", "static", "img", image), "rb").read()

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

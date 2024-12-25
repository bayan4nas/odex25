# _*_ coding: utf-
import logging

from odoo import http
from odoo.tools.translate import _
import json
import base64
from odoo.http import request


_logger = logging.getLogger(__name__)

from odoo.addons.web.controllers.main import serialize_exception,content_disposition

class PartnershipWebsite (http.Controller):
    
    @http.route('/partnership_logos',type='http',auth='public', website=True)
    def PartnerhsipPage (self,**kw):
        partners = http.request.env['partnership.website'].sudo().search([('publish','=',True)],order="id desc")
        list = self.get_partners(partners)
        status = True
        if not list:
            status = False
        return json.dumps({'status': status, 'content': list})
    
    def get_partners(self,partners):
        list = []
        for l in partners:
            record = {}
            record['logo'] = "/web/binary/attachment?id=" + str(l.id) if l.logo else False
            record['name'] = l.name
            record['url'] = l.url
            record['description'] = l.description
            record['publish'] = l.publish
            list.append(record)
        return list
    
    
    @http.route('/web/binary/attachment', type='http', auth="public", website=True)
    # @serialize_exception
    def attachment_document(self, id, filename=None, **kw):
        res = request.env['partnership.website'].sudo().browse(int(id))
        if res.logo:
            filecontent = base64.b64decode(res.logo or '')
            if not filename:
                filename = '%s_%s' % ("partnership.website".replace('.', '_'), id)
                status, headers, content = request.env['ir.http'].binary_content(
                    model='partnership.website',
                    id=int(id),
                    field='logo',
                    default_mimetype='application/octet-stream',
                    env=request.env
                )
                mimetype = dict(headers).get('Content-Type')
                return request.make_response(filecontent,
                                             [('Content-Type', mimetype),
                                              ('Content-Disposition', "attachment")])
        return http.request.render("website.404_page")
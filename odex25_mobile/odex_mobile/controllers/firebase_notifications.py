import json
from odoo import http
from odoo.http import request
from odoo.addons.website.controllers.main import Website
from odoo.tools.translate import _

# Local modules
from ..http_helper import http_helper
from ..data_util import data_util
from ..validator import validator

# from .get_stop import get_stop

import logging
_logger = logging.getLogger(__name__)


class NotificationController(http.Controller):

    @http.route(['/rest_api/v1/notifications/', '/rest_api/v1/notifications/page/<int:page>'], type='http', auth='none', csrf=False, methods=['GET'], website=True)
    def index(self, page=1, **kw):
        """
            fetch notifications  
        """

        # Security check, parse http request, to get body, header, user token
        _, body, __, token = http_helper.parse_request()

        # Check token validate
        result = validator.verify_token(token)
        if not result.get('status', False):
            return http_helper.errcode(code=result['code'], message=result['message'])
        # extract user from token
        user = validator.verify(token)
        if not user:
            return http_helper.response(code=400, message="You are not allowed to perform this operation. please check with one of your team admins", success=False)

        # security check done successfully
        # 
        # partner_ids
        #  search([('partner_ids','in',user.partner_id.id)])
        # 
        domain = [("sent", "=", True), '&', ("is_system", "=", True), ('partner_ids', 'in', user.partner_id.id)]
        ids = user.env['firebase.notification'].search(domain, order="create_date desc")
        notifications = []
        pager = request.website.pager(
            url="/rest_api/v1/notifications",
            total=len(ids),
            page=page,
            url_args={},
            step=20
        )
        records = user.env['firebase.notification'].search(domain).search(
            domain, limit=20, offset=pager['offset'])

        for res in records:
            notifications.append({
                'notification':{"title":res.title,
                "body": res.body, },
                "id":res.id,
                "title":res.title,
                "body": res.body,
                "is_system": res.is_system,
                "sent": res.sent,
                "viewed": res.viewed,
                "meta": res.meta,
                "data": res.iso_date,
                "uuid": res.uid,
            })
        prev = pager['page_previous']['url']
        nxt = pager['page_next']['url']
        end = pager['page_end']['url']
        page = pager['page']['url']
        values = {
            'data': {
                'links': {
                    'prev': prev if nxt != prev and prev != "/rest_api/v1/notifications" else None,
                    'next': nxt if nxt != prev and nxt != "/rest_api/v1/notifications" and page != end else None
                },
                'results': {
                    "notifications":notifications,
                },
                "count": len(ids),
            }
        }
        return http_helper.response(message="Notifications found", data=values)

    @http.route(['/rest_api/v1/notifications/<int:notif>'], type='http', auth='none', csrf=False, methods=['PATCH'], website=True)
    def open_view(self, notif=None, **kw):
        """
            Update stop  
            return Bad content if route not found or state invalid
        """

        # Security check, parse http request, to get body, header, user token
        _, body, __, token = http_helper.parse_request()

        # Check token validate
        result = validator.verify_token(token)
        if not result.get('status', False):
            return http_helper.errcode(code=result['code'], message=result['message'])
        # extract user from token
        user = validator.verify(token)
        if not user:
            return http_helper.response(code=400, message="You are not allowed to perform this operation. please check with one of your team admins", success=False)

        # security check done successfully
        # 

        notifications = []

        res = user.env['firebase.notification'].search([('id', '=', notif)])
        if not res:
            return http_helper.response(code=400,
                                            message=_("You  can not perform this operation. please check with one of your team admins"),
                                            success=False)
        res.action_view()

        notifications.append({
                "id":res.id,
                "title":res.title,
                "body": res.body,
                "is_system": res.is_system,
                "sent": res.sent,
                "viewed": res.viewed,
                "meta": res.meta,
                "data": str(res.create_date),
                "uuid": res.uid,
            })
 
        values = {
            'links': None,
            'results': {
                "notifications":notifications,
            },
            "count": None,
        }
        return http_helper.response(message="Notification found", data=values)

    @http.route(['/rest_api/v1/notifications/<int:notif>'], type='http', auth='none', csrf=False, methods=['DELETE'], website=True)
    def delete_notification(self, notif=None, **kw):
        """
            Update stop  
            return Bad content if route not found or state invalid
        """

        # Security check, parse http request, to get body, header, user token
        _, body, __, token = http_helper.parse_request()

        # Check token validate
        result = validator.verify_token(token)
        if not result.get('status', False):
            return http_helper.errcode(code=result['code'], message=result['message'])
        # extract user from token
        user = validator.verify(token)
        if not user:
            return http_helper.response(code=400, message="You are not allowed to perform this operation. please check with one of your team admins", success=False)

        # security check done successfully
        # 

        notifications = []

        res = user.env['firebase.notification'].search([('id', '=', notif)])
        if not res:
            return http_helper.response(code=400,
                                            message="You  can not perform this operation. please check with one of your team admins",
                                            success=False)
        res.unlink()

        values = {
            'links': None,
            'results': {
                "notifications":[],
            },
            "count": None,
        }
        return http_helper.response(message="Delete successfully", data=values)

    @http.route(['/rest_api/v1/notifications/reset/'], type='http', auth='none', csrf=False, methods=['DELETE'], website=True)
    def reset(self, **kw):
        """
            Update stop  
            return Bad content if route not found or state invalid
        """

        # Security check, parse http request, to get body, header, user token
        _, body, __, token = http_helper.parse_request()

        # Check token validate
        result = validator.verify_token(token)
        if not result.get('status', False):
            return http_helper.errcode(code=result['code'], message=result['message'])
        # extract user from token
        user = validator.verify(token)
        if not user:
            return http_helper.response(code=400, message="You are not allowed to perform this operation. please check with one of your team admins", success=False)

        # security check done successfully
        # 

        domain = [("sent", "=", True), '&', ("is_system", "=", True), ('partner_ids', 'in', user.partner_id.id)]
        ids = user.env['firebase.notification'].search(domain).unlink()
 
        values = {
            'links': None,
            'results': {
                "notifications":[],
            },
            "count": None,
        }
        return http_helper.response(message="Delete successfully", data=values)

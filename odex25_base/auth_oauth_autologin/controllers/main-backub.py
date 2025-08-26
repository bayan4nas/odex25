# Copyright 2021 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import base64
import functools
import json
import logging
from urllib.parse import urlparse

import werkzeug
import werkzeug.urls
import werkzeug.utils
from werkzeug.exceptions import BadRequest

from odoo import api, http, SUPERUSER_ID, _
from odoo.exceptions import AccessDenied
from odoo.http import request
from odoo import registry as registry_get
from odoo.tools.misc import clean_context

from odoo.addons.auth_oauth.controllers.main import OAuthController as OAuthControllerOriginal, OAuthLogin
from odoo.addons.web.controllers.main import login_and_redirect, set_cookie_and_redirect

_logger = logging.getLogger(__name__)

# - 1.3.11 : Session Token in URL


def fragment_to_query_string(func):
    """
    Converts URL fragment parameters (e.g. after # in URL) to query string parameters for OAuth.
    """
    @functools.wraps(func)
    def wrapper(self, *args, **kwargs):
        kwargs.pop('debug', False)
        if not kwargs:
            return """<html><head><script>
                var l = window.location;
                var q = l.hash.substring(1);
                var r = l.pathname + l.search;
                if(q.length !== 0) {
                    var s = l.search ? (l.search === '?' ? '' : '&') : '?';
                    r = l.pathname + l.search + s + q;
                }
                if (r == l.pathname) {
                    r = '/';
                }
                window.location = r;
            </script></head><body></body></html>"""
        return func(self, *args, **kwargs)
    return wrapper


class OAuthController(OAuthControllerOriginal):

    @http.route('/auth_oauth/signin', type='http', auth='none')
    @fragment_to_query_string
    def signin(self, **kwargs):
        state_raw = kwargs.get('state')
        try:
            state = json.loads(base64.urlsafe_b64decode(state_raw).decode())
        except Exception as e:
            _logger.exception("Invalid 'state' JSON: %s", e)
            return BadRequest("Invalid state parameter")

        dbname = state.get('d')
        if not http.db_filter([dbname]):
            return BadRequest("Invalid database.")

        provider = state.get('p')
        context = clean_context(state.get('c', {}))
        registry = registry_get(dbname)

        with registry.cursor() as cr:
            try:
                env = api.Environment(cr, SUPERUSER_ID, context)
                credentials = env['res.users'].sudo().auth_oauth(provider, kwargs)
                cr.commit()

                action = state.get('a')
                menu = state.get('m')
                redirect = werkzeug.urls.url_unquote_plus(state['r']) if state.get('r') else False

                url = redirect or f"/web#action={action}" if action else f"/web#menu_id={menu}" if menu else "/web"
                resp = login_and_redirect(*credentials, redirect_url=url)

                # Check if user has access to /web
                if werkzeug.urls.url_parse(resp.location).path == '/web' and not request.env.user.has_group('base.group_user'):
                    resp.location = '/'
                return resp

            except AttributeError:
                _logger.error("auth_signup not installed on database %s: OAuth sign up cancelled.", dbname)
                url = "/web/login?oauth_error=1"
            except AccessDenied:
                _logger.info("OAuth2: Access denied; redirecting without setting cookies.")
                redirect = werkzeug.utils.redirect("/web/login?oauth_error=3", 303)
                redirect.autocorrect_location_header = False
                return redirect
            except Exception as e:
                _logger.exception("OAuth2 Exception: %s", str(e))
                url = "/web/login?oauth_error=2"

        return set_cookie_and_redirect(url)


class OAuthAutoLogin(OAuthLogin):

    def _autologin_disabled(self):
        return "no_autologin" in http.request.params

    @http.route()
    def web_login(self, *args, **kwargs):
        response = super().web_login(*args, **kwargs)
        if not response.is_qweb or self._autologin_disabled():
            return response

        providers = [p for p in self.list_providers() if p.get("autologin")]
        if len(providers) != 1:
            return response

        provider = providers[0]

        if "auth_form" in provider:
            return request.make_response(provider["auth_form"], headers=[('Content-Type', 'text/html')])

        auth_link = provider.get("auth_link")
        if auth_link:
            return werkzeug.utils.redirect(auth_link, 303)

        return response

# class OAuthAutoLogin(OAuthLogin):
#     def _autologin_disabled(self):
#         print(http.request.params)
#         print("no_autologin" in http.request.params)
#         return "no_autologin" in http.request.params
#
#     def _autologin_link(self):
#         providers = [p for p in self.list_providers() if p.get("autologin")]
#         if len(providers) == 1:
#             return providers[0].get("auth_link")
#
#
#     @http.route()
#     def web_login(self, *args, **kw):
#         response = super().web_login(*args, **kw)
#         if not response.is_qweb:
#             # presumably a redirect already
#             return response
#         if self._autologin_disabled():
#             return response
#         auth_link = self._autologin_link()
#         if not auth_link:
#             return response
#         return werkzeug.utils.redirect(auth_link, 303)
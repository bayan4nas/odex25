import base64
import hashlib
import logging
import secrets
import werkzeug

from odoo.http import request, route
from werkzeug.urls import url_decode, url_encode
from odoo.addons.web.controllers.main import Session
from odoo.addons.auth_oauth.controllers.main import OAuthLogin

_logger = logging.getLogger(__name__)


class OpenIDLogin(OAuthLogin):
    def list_providers(self):
        providers = super(OpenIDLogin, self).list_providers()
        for provider in providers:
            flow = provider.get("flow")
            if flow in ("id_token", "id_token_code"):
                params = url_decode(provider["auth_link"].split("?")[-1])
                params["nonce"] = secrets.token_urlsafe()
                if flow == "id_token":
                    params["response_type"] = "id_token token"
                elif flow == "id_token_code":
                    params["response_type"] = "code"
                code_verifier = provider["code_verifier"]
                code_challenge = base64.urlsafe_b64encode(hashlib.sha256(code_verifier.encode("ascii")).digest()).rstrip(b"=")
                params["code_challenge"] = code_challenge
                params["code_challenge_method"] = "S256"
                if provider.get("scope"):
                    if "openid" not in provider["scope"].split():
                        _logger.error("openid connect scope must contain 'openid'")
                    params["scope"] = provider["scope"]
                provider["auth_link"] = "{}?{}".format(provider["auth_endpoint"], url_encode(params))
        return providers


class SessionOUT(Session):
    @route("/web/session/logout", type="http", auth="none")
    def logout(self, redirect="/web"):
        request.session.logout(keep_db=True)
        oauth = request.env['auth.oauth.provider'].sudo().search([('enabled', '=', True),('autologin', '=', True)], limit=1)
        provider_logout_url = oauth.data_endpoint
        url = str(provider_logout_url) + "?redirect_uri=" + request.httprequest.url_root
        return werkzeug.utils.redirect(url,303)
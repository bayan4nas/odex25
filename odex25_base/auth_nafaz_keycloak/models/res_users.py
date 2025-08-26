import logging
import json

import requests
from ast import literal_eval

from odoo import api, models, _
from odoo.exceptions import AccessDenied
from odoo.addons.auth_signup.models.res_partner import SignupError, now
from odoo.tools.misc import ustr

from odoo.http import request

_logger = logging.getLogger(__name__)


class ResUsers(models.Model):
    _inherit = "res.users"

    def _auth_oauth_get_tokens_implicit_flow(self, oauth_provider, params):
        # https://openid.net/specs/openid-connect-core-1_0.html#ImplicitAuthResponse
        return params.get("access_token"), params.get("id_token")

    def _auth_oauth_get_tokens_auth_code_flow(self, oauth_provider, params):
        # https://openid.net/specs/openid-connect-core-1_0.html#AuthResponse
        code = params.get("code")
        # https://openid.net/specs/openid-connect-core-1_0.html#TokenRequest
        auth = None
        if oauth_provider.client_secret:
            auth = (oauth_provider.client_id, oauth_provider.client_secret)
        response = requests.post(
            oauth_provider.token_endpoint,
            data=dict(
                client_id=oauth_provider.client_id,
                grant_type="authorization_code",
                code=code,
                code_verifier=oauth_provider.code_verifier,  # PKCE
                redirect_uri=request.httprequest.url_root + "auth_oauth/signin",
            ), auth=auth)
        response.raise_for_status()
        response_json = response.json()
        # https://openid.net/specs/openid-connect-core-1_0.html#TokenResponse
        return response_json.get("access_token"), response_json.get("id_token")

    @api.model
    def _auth_oauth_signin(self, provider, validation, params):
        """retrieve and sign in the user corresponding to provider and validated access token
        :param provider: oauth provider id (int)
        :param validation: result of validation of access token (dict)
        :param params: oauth parameters (dict)
        :return: user login (str)
        :raise: AccessDenied if signin failed

        This method can be overridden to add alternative signin methods.
        """
        print(validation)
        print(provider)
        print(params)
        oauth_uid = validation["user_id"]
        login = validation["username"]
        email = validation["email"]
        try:
            oauth_user = self.search(["|", ("login", "=", email), ("login", "=", login)])
            print(oauth_user)
            if not oauth_user:
                raise AccessDenied()
            assert len(oauth_user) == 1
            oauth_user.write({"oauth_access_token": params["access_token"]})
            return oauth_user.login
        except AccessDenied as access_denied_exception:
            if self.env.context.get("no_user_creation"):
                return None
            state = json.loads(params["state"])
            token = state.get("t")
            values = self._generate_signup_values(provider, validation, params)
            try:
                _, login, _ = self.signup(values, token)
                return login
            except (SignupError, UserError):
                raise access_denied_exception

    @api.model
    def auth_oauth(self, provider, params):
        oauth_provider = self.env["auth.oauth.provider"].browse(provider)
        if oauth_provider.flow == "id_token":
            access_token, id_token = self._auth_oauth_get_tokens_implicit_flow(oauth_provider, params)
        elif oauth_provider.flow == "id_token_code":
            access_token, id_token = self._auth_oauth_get_tokens_auth_code_flow(oauth_provider, params)

        else:
            return super(ResUsers, self).auth_oauth(provider, params)
        if not access_token:
            _logger.error("No access_token in response.")
            raise AccessDenied()
        if not id_token:
            _logger.error("No id_token in response.")
            raise AccessDenied()
        validation = oauth_provider._parse_id_token(id_token, access_token)
        # required check
        if not validation.get("user_id"):
            _logger.error("user_id claim not found in id_token (after mapping).")
            raise AccessDenied()
        # retrieve and sign in user
        params["access_token"] = access_token
        login = self._auth_oauth_signin(provider, validation, params)
        if not login:
            raise AccessDenied()
        # return user credentials
        return self.env.cr.dbname, login, access_token

    def _create_user_from_template(self, values):
        template_user_id = literal_eval(
            self.env["ir.config_parameter"].sudo().get_param("base.template_portal_user_id", "False"))
        template_user = self.browse(template_user_id)
        oauth_provider_id = values.get("oauth_provider_id", False)
        if oauth_provider_id:
            oauth_provider_id = self.env["auth.oauth.provider"].browse(int(oauth_provider_id))
            template_user = oauth_provider_id.auth_signup_template_user_id
        if not template_user.exists():
            raise ValueError(_("Signup: invalid template user"))

        if not values.get("login"):
            raise ValueError(_("Signup: no login given for new user"))
        if not values.get("partner_id") and not values.get("name"):
            raise ValueError(_("Signup: no name or partner given for new user"))

        # create a copy of the template user (attached to a specific partner_id if given)
        values["active"] = True
        try:
            with self.env.cr.savepoint():
                return template_user.with_context(no_reset_password=True).copy(values)
        except Exception as e:
            # copy may failed if asked login is not available.
            raise SignupError(ustr(e))

from odoo import models, fields, api
from datetime import datetime, timedelta
from dateutil import parser
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT

import logging
_logger = logging.getLogger(__name__)
str_fmt = '%d/%m/%Y %H:%M:%S'

class JwtAccessToken(models.Model):
    _name = 'jwt_provider.access_token'
    _description = 'Store user access token for one-time-login'

    token = fields.Char('Access Token', required=True)
    user_id = fields.Many2one('res.users', string='User', required=True, ondelete='cascade')
    expires = fields.Datetime('Expires', required=True)

    is_expired = fields.Boolean(compute='_compute_is_expired')

    @api.depends('expires')
    def _compute_is_expired(self):
        ctr = datetime.now().strftime(str_fmt)
        _logger.info(ctr)
        for token in self:
            token.is_expired = datetime.now() >  token.expires

    def access_token_cron(self):
        # self.search([("is_expired", "=", True)]).unlink()
        current_time = datetime.now()
        expired_tokens = self.search([('expires', '<', current_time)])
        expired_tokens.unlink()
        return True
    
    def set_env(self,env):
        self.env = env

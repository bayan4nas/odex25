# -*- coding: utf-8 -*-
import werkzeug
from odoo import http,tools
from odoo.http import request, Response
from odoo.addons.auth_signup.models.res_users import SignupError
from odoo.exceptions import UserError
import base64
from ..validator import validator
from ..http_helper import http_helper
import json
import logging
_logger = logging.getLogger(__name__)



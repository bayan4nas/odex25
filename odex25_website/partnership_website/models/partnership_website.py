
from odoo import models,fields,api,_
from datetime import datetime
from odoo.exceptions import ValidationError
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT,DEFAULT_SERVER_DATE_FORMAT
import re
import logging

_logger = logging.getLogger(__name__)


class PartnershipWeb (models.Model):
    _name = 'partnership.website'
    _description = 'Partnerships Website'
    
    name = fields.Char(string="Company Name",required=True)
    url = fields.Char(string="Company Website",required=True)
    description = fields.Text(string="About Compnay",sanitize=True,required=True)
    logo = fields.Binary(string='Company Logo',required=True)
    publish = fields.Boolean(string='Publish on Website')
    
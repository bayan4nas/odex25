import datetime
from dateutil import relativedelta
from odoo import api, fields, models, _, exceptions


class JobField(models.Model):
    _name = 'employee.job.domain'
    _description = 'Job Domain'

    name = fields.Char(string="Job Domain Name", required=True)
    description = fields.Text(string="Description")

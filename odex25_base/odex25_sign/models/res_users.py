# -*- coding: utf-8 -*-

from odoo import fields, models


class ResUsers(models.Model):
    _inherit = 'res.users'

    sign_signature = fields.Binary(string="Digital Signature", )
    sign_initials = fields.Binary(string="Digitial Initials",)

# -*- coding: utf-8 -*-
##############################################################################
#
#   Expert (LCT, Life Connection Technology)
#    Copyright (C) 2021-2022 LCT
#
##############################################################################

import re
from odoo import models, fields, api,_
from odoo.exceptions import ValidationError

class Cities(models.Model):
    _name = 're.city'
    _description = 'City'
    _inherit = ['mail.thread','mail.activity.mixin']
    _order = "id desc"

    active = fields.Boolean(default=True)
    name = fields.Char(string="Name")
    district_ids = fields.One2many('district','city_id',string="District")
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.user.company_id)

    _sql_constraints = [
        ('name', 'unique(name)', _('Name must be unique.')),
    ]

    @api.constrains('name')
    def fields_check(self):
        """
        Check if name field contain an invalid value
        :raise exception
        """
        num_pattern = re.compile(r'\d', re.I | re.M)
        white_space = re.compile(r'^\s')
        if not re.match(
                "^[\u0600-\u065F\u066A-\u06EF\u06FA-\u06FFa-zA-Z]+[\u0600-\u065F\u066A-\u06EF\u06FA-\u06FFa-zA-Z-_]*$",
                self.name.replace(" ", "")):
            raise ValidationError(_('Name field must be literal'))
        if num_pattern.search(self.name):
            raise ValidationError(_("Name field cannot accept numbers or special character"))
        if white_space.search(self.name):
            raise ValidationError(_("Name field is required (cannot accept white space)"))


class District(models.Model):
    _name = 'district'
    _description = 'District'
    _inherit = ['mail.thread','mail.activity.mixin']
    _order = "id desc"

    active = fields.Boolean(default=True)
    name = fields.Char(string="Name")
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.user.company_id)
    city_id = fields.Many2one('re.city', string="City")

    _sql_constraints = [
        ('name', 'unique(name,city_id)', _('Name must be unique.')),
    ]

    @api.constrains('name')
    def fields_check(self):
        """
        Check if name field contain an invalid value
        :raise exception
        """
        num_pattern = re.compile(r'\d', re.I | re.M)
        white_space = re.compile(r'^\s')
        if not re.match(
                "^[\u0600-\u065F\u066A-\u06EF\u06FA-\u06FFa-zA-Z]+[\u0600-\u065F\u066A-\u06EF\u06FA-\u06FFa-zA-Z-_]*$",
                self.name.replace(" ", "")):
            raise ValidationError(_('Name field must be literal'))
        if num_pattern.search(self.name):
            raise ValidationError(_("Name field cannot accept numbers or special character"))
        if white_space.search(self.name):
            raise ValidationError(_("Name field is required (cannot accept white space)"))

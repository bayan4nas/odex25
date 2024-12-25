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


class sketchs(models.Model):
    _name = "sketchs.sketchs"
    _description = "Sketchs"

    name = fields.Char(string='name', required=True)
    notes = fields.Text(string='Notes')
    company_id = fields.Many2one('res.company', 'Company', required=True, select=1,
                                 help="Company related to this journal", default=lambda self: self.env.user.company_id)



class PropertyContent(models.Model):
    _name = "property.contents"
    _description = "Contents Property"
    _rec_name = 'content_name'

    content_name = fields.Char(string='Content name', required=True)


class PropertyType(models.Model):
    _name = 'internal.property.type'
    _description = 'Property Type'
    _inherit = ['mail.thread','mail.activity.mixin']
    _order = "id desc"

    active = fields.Boolean(default=True)
    name = fields.Char(string="Name")
    market_type = fields.Selection([('residential', 'Residential'),
                                    ('commercial', 'Commercial'),
                                    ('industrial', 'Industrial'),
                                    ('other', 'Other')], string="Market Type", default="commercial")
    is_land = fields.Boolean(string="Land")
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.user.company_id)
    is_waqf = fields.Boolean('Is Waqf')

    _sql_constraints = [
        ('type', 'unique(name)', _('Property type must be unique.')),
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



class PropertyFace(models.Model):
    _name = 'property.faces'
    _description = 'Property Face'
    _inherit = ['mail.thread','mail.activity.mixin']
    _order = "id desc"

    active = fields.Boolean(default=True)
    name = fields.Char(string="Name")

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


class UnitType(models.Model):
    _name = 'unit.type'
    _description = 'Unit Type'
    _inherit = ['mail.thread','mail.activity.mixin']
    _order = "id desc"

    active = fields.Boolean(default=True)
    name = fields.Char(string="Name")
    mezzanine = fields.Boolean(string="Mezzanine")
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


class PropertyState(models.Model):
    _name = 're.property.state'
    _description = 'Property State'
    _inherit = ['mail.thread','mail.activity.mixin']
    _order = "id desc"

    active = fields.Boolean(default=True)
    name = fields.Char(string="Name")

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





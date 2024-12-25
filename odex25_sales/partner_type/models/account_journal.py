# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    partner_type = fields.Selection(selection=[('cash', 'Cash'), ('postpaid', 'Post Paid')], string='Partner Type')


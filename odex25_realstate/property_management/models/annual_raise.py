# -*- coding: utf-8 -*-

import base64
import json
import re
from xml import etree

from odoo import models, fields, api, exceptions, tools, _
from datetime import datetime
from dateutil.relativedelta import relativedelta


class AnnualRaise(models.Model):
    _name = 'annual.raise'
    _description = 'Rent Annual Raise'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id desc"
    _rec_name = "contract_id"

    active = fields.Boolean(default=True)
    name = fields.Char(string="Name")
    contract_id = fields.Many2one('rental.contract', string='Contract')
    raise_type = fields.Selection([('percentage', 'Percentage'), ('fixed', 'Fixed amount')],
                                  string="Raise Type")
    raise_on = fields.Selection([('meter', 'Meter'),
                                 ('rent_amount', 'Rent amount')],
                                string="Raise on", default="rent_amount")
    raise_val = fields.Float(string="Raise Value")
    raise_amount = fields.Float(string='Raise Percentage', compute='get_raise_amount', store=True)
    year = fields.Integer(string='Number of Years')
    rent_amount = fields.Float(string='Rent Amount', compute='get_rent_amount')
    rent_amount_after_raise = fields.Float(string='Rent Amount After Raise plus Services Cost',
                                           compute='get_rent_amount_after_raise', store=True)
    rent_amount_after_raise_temp = fields.Float(string='Rent Amount After Raise Without Services Cost',
                                                compute='get_rent_amount_after_raise', store=True)
    meter_price = fields.Float(string="Meter price", related='contract_id.meter_price')
    meter_price_after_raise = fields.Float(string="Meter price after raise", compute='get_raise_amount', store=True)
    due_date_raise = fields.Date(string='Due Date', compute='get_due_date')

    @api.depends('raise_val', 'raise_type', 'raise_on', 'rent_amount')
    def get_raise_amount(self):
        """
        Get the raise amount based on raise type if percentage
        go with first if E.X: 2 <--> raise value * rent amount <--> 1000 / 100 = 2
        final rent after raise will be 1002
        if fixed amount the raise amount will be E.X: raise value  <--> 2
        final rent after raise will be 1002
        :return: raise_amount
        """
        # contract_object = self.env['rental.contract'].search([('id', '=', self._context.get('contract_id'))])
        for rec in self:
            if rec.raise_type == 'percentage':
                if rec.raise_on == 'rent_amount':
                    raise_amount = (
                                       rec.contract_id.rent_amount if rec.contract_id.change_price else rec.contract_id.cal_rent_amount) * (
                                           rec.raise_val / 100)
                    rec.raise_amount = raise_amount
                else:
                    raise_amount = ((
                                        rec.contract_id.new_price if rec.contract_id.change_price else rec.contract_id.meter_price) * (
                                            rec.raise_val / 100)) * rec.contract_id.space
                    rec.raise_amount = raise_amount
                    meter_price_after_raise = ((
                                                   rec.contract_id.new_price if rec.contract_id.change_price else rec.contract_id.meter_price) * (
                                                       rec.raise_val / 100)) + rec.meter_price
                    rec.meter_price_after_raise = meter_price_after_raise
            elif rec.raise_type == 'fixed':
                if rec.raise_on == 'rent_amount':
                    raise_amount = rec.raise_val
                    rec.raise_amount = raise_amount
                else:
                    raise_amount = rec.raise_val * rec.contract_id.space
                    rec.raise_amount = raise_amount
                    meter_price_after_raise = rec.raise_val + rec.meter_price
                    rec.meter_price_after_raise = meter_price_after_raise

    @api.depends('contract_id')
    def get_rent_amount(self):
        for this in self:
            if this.contract_id.change_price:
                this.rent_amount = this.contract_id.rent_amount
            elif not this.contract_id.change_price:
                this.rent_amount = this.contract_id.cal_rent_amount

    @api.depends('rent_amount', 'raise_amount')
    def get_rent_amount_after_raise(self):
        for rec in self:
            rec.rent_amount_after_raise = rec.rent_amount + rec.raise_amount + rec.contract_id.service_cost
            rec.rent_amount_after_raise_temp = rec.rent_amount + rec.raise_amount

    #
    # @api.onchange('raise_type')
    # def onchange_raise_type(self):
    #     for record in self:
    #         record.raise_amount = 0.0
    #         record.raise_val = 0.0

    @api.depends('year','contract_id')
    def get_due_date(self):
        for rec in self:
            date = self.contract_id.date_from
            rec.due_date_raise = date
            date_from = datetime.strptime(datetime.strftime(date, '%Y-%m-%d'), '%Y-%m-%d').date()
            due_date = date_from + relativedelta(years=rec.year)
            due_date_raise = due_date.strftime('%Y-%m-%d')
            rec.due_date_raise = due_date_raise
            print(rec.due_date_raise, 'rec.due_date_raise')

    def check_concatenate_date_to(self, year, month, day):
        concatenated_date = ''
        if day < 10:
            day = '0' + str(day)
        if month < 10:
            month = '0' + str(month)
        elif month > 12:
            no_year = month % 12
            month -= (no_year * 12)
            year += no_year
        concatenated_date = str(year) + '-' + str(month) + '-' + str(day)
        return concatenated_date

# -*- coding: utf-8 -*-
##############################################################################
#
#   Expert (LCT, Life Connection Technology)
#    Copyright (C) 2020-2021 LCT
#
##############################################################################
from odoo.exceptions import ValidationError
from odoo import models, fields, api, _


class BenefitWiz(models.TransientModel):
    _name = 'benefit.wiz'
    _description = "Benefit Wizard Report"

    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    benefit_ids = fields.Many2many('grant.benefit',string="Benefits")
    report_type = fields.Selection(selection=[('benefit','Benefits Payment'),
                                              ('benefit_month','Benefits Month Payments'),
                                              ])

    @api.constrains('date_from','date_to')
    def check_date(self):
        for rec in self:
            if rec.date_from and rec.date_to:
                if rec.date_from>rec.date_to:
                    raise ValidationError(_("Date To Should Be Greater Than Date From"))

    def print_report(self):
        data ={'date_from':self.date_from,'date_to':self.date_to,
               'report_type':self.report_type,
               'benefit_ids':self.benefit_ids.ids if self.benefit_ids else False,
         }
        if self.report_type == 'benefit':
            return self.env.ref('odex_takaful.benefit_payment_report_pdf_act').report_action(self, data=data)
        elif self.report_type == 'benefit_month':
            return self.env.ref('odex_takaful.benefit_month_payment_report_pdf_act').report_action(self, data=data)
        elif self.report_type == 'benefit_month_share':
            return self.env.ref('odex_takaful.benefit_month_payment_share_report_pdf_act').report_action(self, data=data)
      
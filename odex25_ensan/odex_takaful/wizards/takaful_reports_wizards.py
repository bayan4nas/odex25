# -*- coding: utf-8 -*-
from odoo import api, models, fields, _


class MakfuleenReprtWizard(models.TransientModel):
    _name = 'takaful.wizard.report.makfuleen'
    _description = "Makfuleen Report For Selected Sponsor(s)"
    
    sponsor_id = fields.Many2one(
        'takaful.sponsor',
        string='Sponsor Name'
    )

    # @api.multi
    def create_makfuleen_wizard_report(self):
        """ Method to print Makfuleen report """
        context = dict(self.env.context or {})
        context['sponsor_id'] = self.sponsor_id.id
        context['name'] = self.sponsor_id.name
        return self.env.ref('odex_takaful.makfuleen_report_pdf_act').report_action(self, data=context)


class KafalatPaymentReprtWizard(models.TransientModel):
    _name = 'takaful.wizard.report.kafalat.payment'
    _description = "Kafalat Payment Report"
    
    sponsor_id = fields.Many2one(
        'takaful.sponsor',
        string='Sponsor Name'
    )

    # @api.multi
    def create_kafalat_payment_wizard_report(self):
        """ Method to print Kafalat Payment report """
        context = dict(self.env.context or {})
        context['sponsor_id'] = self.sponsor_id.id
        context['name'] = self.sponsor_id.name

        return self.env.ref('odex_takaful.kafalat_payment_report_pdf_act').report_action(self, data=context)


class KafalatCancelReprtWizard(models.TransientModel):
    _name = 'takaful.wizard.report.kafalat.cancel'
    _description = "Kafalat Cancel Report"
    
    from_date = fields.Date(string="From Date")
    to_date = fields.Date(string="To Date")

    # @api.multi
    def create_kafalat_cancel_wizard_report(self):
        """ Method to print Kafalat Cancel report """
        context = dict(self.env.context or {})
        context['start_date'] = self.from_date
        context['end_date'] = self.to_date

        return self.env.ref('odex_takaful.kafalat_cancel_report_pdf_act').report_action(self, data=context)

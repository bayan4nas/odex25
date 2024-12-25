# -*- coding: utf-8 -*-

from odoo import api, models, fields, _

class ReportMakfuleen(models.AbstractModel):
    _name = 'report.odex_takaful.makfuleen_report_pdf'

    @api.model
    def get_report_values(self, docids, data=None):
        selected_id = data.get('sponsor_id', False)
        domain = [('sponsor_id', '=', selected_id)]
        records = self.env['takaful.sponsorship'].sudo().search(domain)
        
        return {
            'docs': records,
            'name': data.get('name', ""),
        }


class ReportKafalatPayment(models.AbstractModel):
    _name = 'report.odex_takaful.kafalat_payment_report_pdf'


    @api.model
    def get_report_values(self, docids, data=None):

        sponsor_id = data.get('sponsor_id', False)
        overdue_sponsorships = self.env['takaful.sponsorship'].sudo().search([('sponsor_id','=', sponsor_id), ('has_delay','=', False), ('state','in', ['wait_pay','progress' , 'to_cancel'])])

        overdue_amount = sum(overdue_sponsorships.mapped('overdue_amount')) or 0

        return {
            'docs': overdue_sponsorships or [],
            'name': data.get('name', ""),
            'overdue_amount': overdue_amount,
            'overdue_count': len(overdue_sponsorships),
        }


class ReportKafalatCancel(models.AbstractModel):
    _name = 'report.odex_takaful.kafalat_cancel_report_pdf'


    @api.model
    def get_report_values(self, docids, data=None):
        start_date = data.get('start_date', False)
        end_date = data.get('end_date', False)


        if start_date and end_date:
            canceled_kafalat = self.env['sponsorship.cancellation'].sudo().search([
                ('confirm_date', '>=', start_date),
                ('confirm_date', '<=', end_date),
                ('state', '=', 'cancel'),
            ])
        
        else:
            canceled_kafalat = []
  
        return {
            'docs': canceled_kafalat,
            'cancel_count': len(canceled_kafalat),
            'start_date': start_date,
            'end_date': end_date,
        }


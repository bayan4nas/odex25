# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError

from datetime import datetime, timedelta, date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
from dateutil.parser import parse

class BenefitREP(models.AbstractModel):
    _name = 'report.odex_takaful.benefit_payment_report_pdf'

    def get_result(self, data=None):
        form = data
        domain = []
        if form['benefit_ids']:
            domain += [('benefit_id', 'in', form['benefit_ids'])]
        if form['date_from'] and form['date_to']:
            domain = [('month_id.date', '>=', form['date_from']), ('month_id.date', '<=', form['date_to'])]
        payment = self.env['month.payment.line'].sudo().search(domain)
        return payment

    @api.model
    def get_report_values(self, docids, data=None):
        record = self.get_result(data)
        date_to, date_from = '', ''
        if data['date_from'] and data['date_to']:
            date_from = data['date_from']
            date_to = data['date_to']
        if not record:
            raise ValidationError(_("Sorry, there are no results for this selection !"))
        return {
            'date_from': date_from,
            'date_to': date_to,
            'docs': record,
        }


class BenefitMonth(models.AbstractModel):
    _name = 'report.odex_takaful.benefit_month_payment_report_pdf'

    def get_result(self, data=None):
        form = data
        domain = []
        if form['benefit_ids']:
            domain += [('benefit_id', 'in', form['benefit_ids'])]
        if form['date_from'] and form['date_to']:
            domain += [('month_id.date', '>=', form['date_from']), ('month_id.date', '<=', form['date_to'])]

        payment = self.env['month.payment.line'].sudo().search(domain)
        month_payment = payment.mapped('month_id')
        li = []
        for y in month_payment:
            date = parse(str(y.date))
            li.append({'name': y.name , 'code': y.code, 'month_payment': date.strftime("%m-%Y"), 'payment': payment.filtered(lambda r: r.month_id == y)})
        return li

    @api.model
    def get_report_values(self, docids, data=None):
        record = self.get_result(data)
        # if record.get('data'):
        #     gender = record.get('gender').title()
        #     record.update({'gender': _(gender)})
        date_to, date_from = '', ''
        if data['date_from'] and data['date_to']:
            date_from = data['date_from']
            date_to = data['date_to']
        if not record:
            raise ValidationError(_("Sorry, there are no results for this selection !"))
        return {
            'date_from': date_from,
            'date_to': date_to,
            'docs': record,
        }


class MonthReportXlsx(models.AbstractModel):
    _name = "report.odex_takaful.benefit_month_payment_report_xlsx"
    _inherit = 'report.report_xlsx.abstract'

    @api.model
    def generate_xlsx_report(self, workbook, data, objs):
        docs = objs
        sheet = workbook.add_worksheet(_('Bank Sheet'))
        if self.env.user.lang != 'en_US':
            sheet.right_to_left()
        format0 = workbook.add_format(
            {'bottom': True, 'bg_color': '#b8bcbf', 'right': True, 'left': True, 'top': True, 'align': 'center', })
        format1 = workbook.add_format({'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'center', })
        format2 = workbook.add_format(
            {'font_size': 14, 'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'center',
             'bold': True, 'bg_color': '#0f80d6', 'font_color': 'white'})
        for doc in docs:

            format2.set_align('center')
            sheet.merge_range('A9:L9',
                              (_("Month Payment Sheet")) + " - " + doc.name + " / " + doc.code, format2)
            sheet.set_column('B:D', 15)
            sheet.set_column('E:F', 10)
            row = 10
            clm = 0
            labels = [(_("#")), (_("Benefit Name")), (_("Benefit Type")), (_("Benefit ID Number")), (_("Birth Date")),
                (_("Sponsorship Number")), (_("The Sponsor")),
                (_("Amount")), (_("Iban")), (_("Bank Name")), (_("Responsible Name")), (_("Responsible ID Number"))]
            
            for res in labels:
                sheet.write(row, clm, res, format0)
                clm += 1
            row = 11
            seq = 0
            for rec in doc.line_ids:
                seq += 1
                clm = 0
                sheet.write(row, clm, seq, format1)
                sheet.write(row, clm + 1, rec.benefit_id.name, format1)
                sheet.write(row, clm + 2, rec.benefit_id.benefit_type, format1)
                sheet.write(row, clm + 3, rec.benefit_id.id_number, format1)
                sheet.write(row, clm + 4, rec.benefit_id.birth_date, format1)
                sheet.write(row, clm + 5, rec.s_code, format1)
                sheet.write(row, clm + 6, rec.sponsor_id.name, format1)
                sheet.write(row, clm + 7, rec.amount, format1)
                sheet.write(row, clm + 8, rec.benefit_id.iban, format1)
                sheet.write(row, clm + 9, rec.benefit_id.bank_id.name, format1)
                sheet.write(row, clm + 10, rec.responsible_id.name, format1)
                sheet.write(row, clm + 11, rec.responsible_id.id_number, format1)

                row += 1
            row += 3


class BankSheetReportXlsx(models.AbstractModel):
    _name = "report.odex_takaful.benefit_month_payment_bank_sheet"
    _inherit = 'report.report_xlsx.abstract'

    @api.model
    def generate_xlsx_report(self, workbook, data, objs):
        docs = objs
        sheet = workbook.add_worksheet('Bank Sheet')
        if self.env.user.lang != 'en_US':
            sheet.right_to_left()
        format0 = workbook.add_format(
            {'bottom': True, 'bg_color': '#b8bcbf', 'right': True, 'left': True, 'top': True, 'align': 'center', })
        format1 = workbook.add_format({'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'center', })
        format2 = workbook.add_format(
            {'font_size': 14, 'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'center',
             'bold': True, 'bg_color': '#0f80d6', 'font_color': 'white'})
        for doc in docs:

            format2.set_align('center')
            sheet.merge_range('A9:F9',
                              (_("Bank Sheet")) + " - " + doc.name + " / " + doc.code, format2)
            sheet.set_column('B:D', 15)
            sheet.set_column('E:F', 10)
            row = 9
            clm = 0
            labels = [(_("#")), (_("Bank Name")), (_("Account Number")), (_("Amount")), 
            (_("Benefit Name")), (_("Benefit ID Number")), (_("Responsible Name")), (_("Responsible ID Number"))]

            for res in labels:
                sheet.write(row, clm, res, format0)
                clm += 1
            row = 10
            seq = 0
            for rec in doc.line_ids:
                seq += 1
                clm = 0
                sheet.write(row, clm, seq, format1)
                sheet.write(row, clm + 1, rec.benefit_id.bank_id.name, format1)
                sheet.write(row, clm + 2, rec.benefit_id.iban, format1)
                sheet.write(row, clm + 3, rec.amount, format1)
                sheet.write(row, clm + 4, rec.benefit_id.name, format1)
                sheet.write(row, clm + 5, rec.benefit_id.id_number, format1)
                sheet.write(row, clm + 6, rec.responsible_id.name, format1)
                sheet.write(row, clm + 7, rec.responsible_id.id_number, format1)

                row += 1
            row += 3

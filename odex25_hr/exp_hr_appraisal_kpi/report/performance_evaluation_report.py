# -*- coding: utf-8 -*-
from odoo import api, models, _
from datetime import datetime


class EmployeeAppraisalReport(models.AbstractModel):
    _name = 'report.exp_hr_appraisal_kpi.performance_evaluation_report'
    _description = "Performance Evaluation Summary"

    LABELS = [
        'رقم الموظف', 'الموظف', 'القسم', 'المسمى الوظيفي',
        'مرحلة التقييم', 'تاريخ التقييم', 'سنة التقييم',
        'تقييم الأهداف', 'تقييم الجدارات', 'درجة التقييم', 'نتيجة التقييم']

    def get_result(self, data=None):
        """Fetch employee appraisal records based on filters."""
        form = data['form']
        domain = [('state', '=', 'open')]
        value = [('state', '=', 'closed')]

        if form.get('employee_ids'):
            domain = [('id', 'in', form['employee_ids'])]
        elif form.get('department_ids'):
            domain.append(('department_id', 'in', form['department_ids']))

        employees = self.env['hr.employee'].sudo().search(domain).ids
        value += [('employee_id', 'in', employees)]

        if form.get('date_from') and form.get('date_to'):
            value += [('appraisal_date', '>=', form['date_from']), ('appraisal_date', '<=', form['date_to'])]

        if form.get('appraisal_stage_id'):
            value.append(('appraisal_stage_id', '=', form['appraisal_stage_id'][0]))

        return self.env['hr.employee.appraisal'].sudo().search(value).sorted(
            key=lambda r: (r.employee_id.department_id.id, r.appraisal_stage_id.id)
        )

    @api.model
    def _get_report_values(self, docids, data=None):
        """Prepare values for PDF report."""
        records = self.get_result(data)
        date_from = data['form'].get('date_from', ' / ')
        date_to = data['form'].get('date_to', ' / ')

        return {
            'date_from': date_from,
            'date_to': date_to,
            'docs': records,
            'labels': self.LABELS  # Passing labels to the PDF template
        }


class EmployeeAppraisalReportXlsx(models.AbstractModel):
    _name = "report.exp_hr_appraisal_kpi.performance_evaluation_report_xlsx"
    _description = "XLSX Performance Evaluation Summary"
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, objs):
        docs = self.env['report.exp_hr_appraisal_kpi.performance_evaluation_report'].get_result(data)
        sheet = workbook.add_worksheet(_('Employee Appraisal Report'))
        self = self.with_context(lang=self.env.user.lang)

        if self.env.user.lang != 'en_US':
            sheet.right_to_left()
        # Define formats
        header_format = workbook.add_format(
            {'bold': True, 'font_color': 'white', 'bg_color': '#006666', 'align': 'center', 'valign': 'vcenter',
             'border': 1})
        # header_format = workbook.add_format({'bold': True, 'align': 'center', 'bg_color': '#263f79', 'font_color': 'white'})
        data_format = workbook.add_format({'align': 'center'})
        # title_format = workbook.add_format({'bold': True, 'font_size': 14, 'align': 'center'})

        # # Report Title
        # title = _("Performance Evaluation Summary") + " {} - {}".format(data['form']['date_from'],data['form']['date_to'])
        # sheet.merge_range('A1:L1', title, header_format)

        column_widths = [8, 24, 26, 43, 15, 15, 11, 11, 11, 11, 15, ]
        for i, width in enumerate(column_widths):
            sheet.set_column(i, i, width)

        # Write header using the shared labels
        labels = self.env['report.exp_hr_appraisal_kpi.performance_evaluation_report'].LABELS
        for col, label in enumerate(labels):
            sheet.write(0, col, label, header_format)

        # Write data
        row = 1
        seq = 0
        for rec in docs:
            seq += 1
            # sheet.write(row, 0, seq, data_format)
            sheet.write(row, 0, rec.employee_id.emp_no or '', data_format)
            sheet.write(row, 1, rec.employee_id.name or '', data_format)
            sheet.write(row, 2, rec.employee_id.department_id.name or '', data_format)
            sheet.write(row, 3, rec.employee_id.job_id.name or '', data_format)
            sheet.write(row, 4, rec.appraisal_stage_id.name or '', data_format)
            sheet.write(row, 5, rec.appraisal_date.strftime('%Y-%m-%d') if rec.appraisal_date else '', data_format)
            sheet.write(row, 6, rec.year_id.name or '', data_format)
            sheet.write(row, 7, round(rec.goals_mark, 2) or 0, data_format)
            sheet.write(row, 8, round(rec.skill_mark, 2) or 0, data_format)
            sheet.write(row, 9, round(rec.total_score, 2) or 0, data_format)
            sheet.write(row, 10, rec.appraisal_result.name or 'لم حساب درجة التقييم', data_format)
            row += 1

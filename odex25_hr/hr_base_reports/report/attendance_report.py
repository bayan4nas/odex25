# -*- coding: utf-8 -*-

from datetime import datetime,timedelta
from odoo import api, models, _
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import xlsxwriter


class EmployeeAttendanceReport(models.AbstractModel):
    _name = 'report.hr_base_reports.employee_attendance_report'
    _description = 'Employee Attendance Report'

    def get_result(self, data=None):
        form = data['form']
        employees = False
        domain = []
        if form['employee_ids']:
            employees = self.env['hr.employee'].sudo().browse(form['employee_ids'])
        else:
            if form['department_ids'] and not form['employee_ids']:
                domain = [('department_id', 'in', form['department_ids']), ('state', '=', 'open')]
            domain += [('state', '=', 'open')]
            employees = self.env['hr.employee'].sudo().search(domain)
        end_date = datetime.strptime(str(form['date_to']), DEFAULT_SERVER_DATE_FORMAT)
        start_date = datetime.strptime(str(form['date_from']), DEFAULT_SERVER_DATE_FORMAT)
        value = [('date', '>=', start_date), ('date', '<=', end_date)]
        records = self.env['hr.attendance.transaction'].sudo().search(value)
        record = records.filtered(lambda r: r.employee_id in employees).sorted(
            lambda r: r.date) if employees else records.sorted(lambda r: r.date)
        return record, records

    # lateness_reasons = reason_pool.search([('latest_date', '>=', self.date_from),
    #                                        ('latest_date', '<=', self.date_to),
    #                                        ('employee_id', '=', employee.id),
    #                                        ('state', '=', 'hr_manager')])

    def convert_to_time_format(self,hours):
        total_seconds = int(hours * 3600)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60

        return f"{hours:02}:{minutes:02}:{seconds:02}"

    def get_value_detailse(self,data=None):
        form = data['form']
        employees = False
        domain = []

        if form['employee_ids']:
            employees = self.env['hr.employee'].sudo().browse(form['employee_ids'])
        else:
            if form['department_ids'] and not form['employee_ids']:
                domain = [('department_id', 'in', form['department_ids']), ('state', '=', 'open')]
            domain += [('state', '=', 'open')]
            employees = self.env['hr.employee'].sudo().search(domain)

        end_date = datetime.strptime(str(form['date_to']), DEFAULT_SERVER_DATE_FORMAT)
        start_date = datetime.strptime(str(form['date_from']), DEFAULT_SERVER_DATE_FORMAT)
        end_date_str = end_date.strftime('%Y-%m-%d')
        start_date_str = start_date.strftime('%Y-%m-%d')
        total_days = (end_date - start_date).days + 1
        value = [('date', '>=', start_date), ('date', '<=', end_date)]
        records = self.env['hr.attendance.transaction'].sudo().search(value)
        missions_special = self.env['hr.official.mission.type'].sudo().search([
            ('special_hours', '=', True),
            ('duration_type', '=', 'days'),
            ('related_with_financial', '=', False)
        ])
        assignments = self.env['hr.official.mission.type'].sudo().search([
            ('special_hours', '=', True),
            ('duration_type', '=', 'days'),
            ('related_with_financial', '=', True)
        ])
        Tasks= self.env['hr.official.mission.type'].sudo().search([
            ('special_hours', '=', False),
            ('duration_type', '=', 'days'),
            ('related_with_financial', '=', False)
        ])
        all_leave_types= self.env['hr.holidays.status'].sudo().search([])
        all_public_holiday= self.env['hr.holiday.officials'].sudo().search([])


        filtered_records = records.filtered(lambda r: r.employee_id in employees)
        result = []
        for employee in employees:
            employee_records = filtered_records.filtered(lambda r: r.employee_id == employee)

            absent_count = sum(1 for rec in employee_records if rec.is_absent)
            total_office_hours = sum(rec.office_hours for rec in employee_records)

            missions_special_data = {}
            for mission in missions_special:
                count = sum(
                    1 for rec in employee_records
                    if rec.official_id and rec.official_id.mission_type.id == mission.id
                )
                if count > 0:
                    missions_special_data[mission.id] = {
                        'name': mission.name,
                        'count': count
                    }

            assignments_count = sum(
                1 for rec in employee_records
                if rec.official_id and rec.official_id.mission_type in assignments
            )
            tasks_count = sum(
                1 for rec in employee_records
                if rec.official_id and rec.official_id.mission_type in Tasks
            )
            holidays_data = {}
            for rec in employee_records:
                if rec.normal_leave and rec.leave_id:
                    leave_id = rec.leave_id.holiday_status_id.id
                    leave_name = rec.leave_id.holiday_status_id.name
                    if leave_id not in holidays_data:
                        holidays_data[leave_id] = {
                            'name': leave_name,
                            'count': 1
                        }
                    else:
                        holidays_data[leave_id]['count'] += 1

            public_holidays_data = {}
            for rec in employee_records:
                if rec.public_holiday and rec.public_holiday_id:
                    holiday_id = rec.public_holiday_id.id
                    if holiday_id not in public_holidays_data:
                        public_holidays_data[holiday_id] = {
                            'name': rec.public_holiday_id.official_event_id.name,
                            'count': 1
                        }
                    else:
                        public_holidays_data[holiday_id]['count'] += 1

            public_holiday_days = sum(
                1 for rec in employee_records
                if rec.public_holiday
            )
            actual_working_days = total_days - public_holiday_days
            employee_dates = set(rec.date for rec in employee_records)

            public_holiday_dates = set(
                rec.date for rec in employee_records
                if rec.public_holiday
            )

            absent_dates = set(
                rec.date for rec in employee_records
                if rec.is_absent
            )

            actual_present_days = employee_dates - public_holiday_dates - absent_dates
            actual_days_sum = len(actual_present_days)

            lateness_count = sum(1 for rec in employee_records if rec.approve_lateness)
            early_exit_count = sum(
                1 for rec in employee_records
                if rec.approve_exit_out and not rec.approve_lateness
            )
            required_work_hours = sum(
                rec.plan_hours for rec in employee_records
                if not rec.normal_leave
                and not rec.public_holiday
                and not rec.approve_personal_permission
                and not (
                        rec.is_official
                        and rec.official_id
                        and rec.official_id.mission_type in Tasks
                )
            )
            formatted_required_work_hours = self.convert_to_time_format(required_work_hours)
            formattes_total_office_hours=self.convert_to_time_format(total_office_hours)
            in_office_count = sum(
                1 for rec in employee_records
                if rec.sign_in or rec.sign_out
            )

            entrance_discipline_percentage = round(
                (1 - ((lateness_count + early_exit_count) / actual_working_days)) * 100, 2
            ) if actual_working_days else 0

            hours_commitment_percentage = round(
                (total_office_hours / required_work_hours) * 100, 2
            ) if required_work_hours else 0

            discipline_percentage = round((actual_days_sum / actual_working_days) * 100,
                                          2) if actual_working_days else 0

            employee_data = {
                # 'id': employee.id,
                'employee_name': employee.name,
                'absent': absent_count,
                'total_office_hours': formattes_total_office_hours,
                'missions_special': missions_special_data,
                'holidays': holidays_data,
                'public_holidays': public_holidays_data,
                'actual_working_days': actual_working_days,
                'actual_days_sum':actual_days_sum,
                'lateness_count':lateness_count,
                'early_exit_count':early_exit_count,
                'required_work_hours':formatted_required_work_hours,
                'in_office_count': in_office_count,
                'department':employee.department_id.name,
                'discipline_percentage':f"{discipline_percentage}%",
                'entrance_discipline_percentage':f"{entrance_discipline_percentage}%",
                'hours_commitment_percentage':f"{hours_commitment_percentage}%"

            }
            if assignments_count > 0:
                employee_data['assignments'] = assignments_count

            if tasks_count > 0:
                employee_data['tasks'] = tasks_count

            result.append(employee_data)
        print(result)
        return result,start_date_str,end_date_str
    @api.model
    def _get_report_values(self, docids, data=None):
        record = self.get_result(data)
        date_to, date_from = ' / ', ' / '
        if data['form']['date_from'] and data['form']['date_to']:
            date_from = data['form']['date_from']
            date_to = data['form']['date_to']
        return {
            'date_from': date_from,
            'date_to': date_to,
            'docs': record,
        }

    def get_value_detailse_by_department(self, data=None):
        form = data['form']
        domain = []
        department_summary = []

        if form['department_ids']:
            domain = [('department_id', 'in', form['department_ids']), ('state', '=', 'open')]

        employees = self.env['hr.employee'].sudo().search(domain)

        end_date = datetime.strptime(str(form['date_to']), DEFAULT_SERVER_DATE_FORMAT)
        start_date = datetime.strptime(str(form['date_from']), DEFAULT_SERVER_DATE_FORMAT)

        total_days = (end_date - start_date).days + 1

        value = [('date', '>=', start_date), ('date', '<=', end_date)]
        records = self.env['hr.attendance.transaction'].sudo().search(value)
        missions_special = self.env['hr.official.mission.type'].sudo().search([
            ('special_hours', '=', True),
            ('duration_type', '=', 'days'),
            ('related_with_financial', '=', False)
        ])
        assignments = self.env['hr.official.mission.type'].sudo().search([
            ('duration_type', '=', 'days'),
            ('related_with_financial', '=', True)
        ])
        Tasks = self.env['hr.official.mission.type'].sudo().search([
            ('special_hours', '=', False),
            ('duration_type', '=', 'days'),
            ('related_with_financial', '=', False)
        ])

        filtered_records = records.filtered(lambda r: r.employee_id in employees)

        for department in self.env['hr.department'].browse(form['department_ids']):
            department_employees = employees.filtered(lambda e: e.department_id == department)
            department_records = filtered_records.filtered(lambda r: r.employee_id in department_employees)

            absent_count = sum(1 for rec in department_records if rec.is_absent)
            total_office_hours = sum(rec.office_hours for rec in department_records)
            office_hours_above_count = sum(1 for rec in department_records if rec.office_hours > 0)

            missions_special_data = {}
            for mission in missions_special:
                count = sum(
                    1 for rec in department_records
                    if rec.official_id and rec.official_id.mission_type.id == mission.id
                )
                if count > 0:
                    missions_special_data[mission.id] = {
                        'name': mission.name,
                        'count': count
                    }

            assignments_count = sum(
                1 for rec in department_records
                if rec.official_id and rec.official_id.mission_type in assignments
            )

            tasks_count = sum(
                1 for rec in department_records
                if rec.official_id and rec.official_id.mission_type in Tasks
            )

            holidays_data = {}
            for rec in department_records:
                if rec.normal_leave and rec.leave_id:
                    leave_id = rec.leave_id.holiday_status_id.id
                    leave_name = rec.leave_id.holiday_status_id.name
                    if leave_id not in holidays_data:
                        holidays_data[leave_id] = {
                            'name': leave_name,
                            'count': 1
                        }
                    else:
                        holidays_data[leave_id]['count'] += 1

            public_holidays_data = {}
            for rec in department_records:
                if rec.public_holiday and rec.public_holiday_id:
                    holiday_id = rec.public_holiday_id.id
                    if holiday_id not in public_holidays_data:
                        public_holidays_data[holiday_id] = {
                            'name': rec.public_holiday_id.official_event_id.name,
                            'count': 1
                        }
                    else:
                        public_holidays_data[holiday_id]['count'] += 1

            public_holiday_days = sum(
                1 for rec in department_records
                if  rec.public_holiday
            )
            work_days = sum(
                1 for rec in department_records
                if not rec.public_holiday
            )

            actual_working_days = total_days - public_holiday_days
            employee_dates = set(rec.date for rec in department_records)

            public_holiday_dates = set(
                rec.date for rec in department_records
                if rec.public_holiday
            )

            absent_dates = set(
                rec.date for rec in department_records
                if rec.is_absent
            )

            actual_present_days = employee_dates - public_holiday_dates - absent_dates
            required_work_hours = sum(
                rec.plan_hours for rec in department_records
                if not rec.normal_leave
                and not rec.public_holiday
                and not rec.approve_personal_permission
                and not (
                        rec.is_official
                        and rec.official_id
                        and rec.official_id.mission_type in Tasks
                )
            )
            if office_hours_above_count > 0:
                avg_office_hours_per_day = total_office_hours / office_hours_above_count
                avg_office_hours_per_day_formatted = self.convert_to_time_format(avg_office_hours_per_day)
            else:
                avg_office_hours_per_day_formatted = "00:00:00"
            sign_in_times = [rec.sign_in for rec in department_records if rec.sign_in]

            if sign_in_times:
                total_sign_in_seconds = sum(
                    (timedelta(hours=sign_in).total_seconds() if isinstance(sign_in, (float, int)) else
                     (datetime.combine(datetime.today(), sign_in.time()) - datetime(1900, 1, 1)).total_seconds())
                    for sign_in in sign_in_times
                )
                avg_sign_in_seconds = total_sign_in_seconds / len(sign_in_times)

                avg_sign_in_seconds_rounded = round(avg_sign_in_seconds / 60) * 60
                avg_sign_in_time = str(timedelta(seconds=avg_sign_in_seconds_rounded))

            else:
                avg_sign_in_time = "00:00:00"

            sign_out_times = [rec.sign_out for rec in department_records if rec.sign_out]

            if sign_out_times:
                total_sign_out_seconds = sum(
                    (timedelta(hours=sign_out).total_seconds() if isinstance(sign_out, (float, int)) else
                     (datetime.combine(datetime.today(), sign_out.time()) - datetime(1900, 1, 1)).total_seconds())
                    for sign_out in sign_out_times
                )
                avg_sign_out_seconds = total_sign_out_seconds / len(sign_out_times)

                avg_sign_out_seconds_rounded = round(avg_sign_out_seconds / 60) * 60
                avg_sign_out_time = str(timedelta(seconds=avg_sign_out_seconds_rounded))

            else:
                avg_sign_out_time = "00:00:00"

            permission_count = sum(1 for rec in department_records if rec.approve_personal_permission)
            total_permission_hour = sum(rec.total_permission_hours for rec in department_records if rec.total_permission_hours)
            if permission_count > 0:
                avg_leave_hours_per_day = total_permission_hour / permission_count
                avg_permission_hours_per_day_formatted = self.convert_to_time_format(avg_leave_hours_per_day)
            else:
                avg_permission_hours_per_day_formatted = "00:00:00"

            formatted_required_work_hours = self.convert_to_time_format(required_work_hours)
            formattes_total_office_hours = self.convert_to_time_format(total_office_hours)

            difference = required_work_hours - total_office_hours
            formattes_difference=self.convert_to_time_format(difference)

            department_summary.append({
                'department_name': department.name,
                'actual_working_days': work_days,
                'employee_count': len(department_employees),
                'total_office_hours': formattes_total_office_hours,
                'required_work_hours': formatted_required_work_hours,
                'difference': formattes_difference,
                'avg_sign_in_time': avg_sign_in_time,
                'avg_sign_out_time': avg_sign_out_time,
                'avg_office_hours_per_day_formatted': avg_office_hours_per_day_formatted,
                'holidays': holidays_data,
                'public_holidays': public_holidays_data,
                'missions_special': missions_special_data,
                'avg_permission_hours_per_day_formatted':avg_permission_hours_per_day_formatted,
                'absent': absent_count,

            })
            if assignments_count > 0:
                department_summary[-1]['assignments'] = assignments_count

            if tasks_count > 0:
                department_summary[-1]['tasks'] = tasks_count

        return department_summary, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d')


class EmployeeAttendanceReportXlsx(models.AbstractModel):
    _name = "report.hr_base_reports.employee_attendance_report_xlsx"
    _description = 'XLSX Employee Attendance Report'
    _inherit = 'report.report_xlsx.abstract'

    @api.model
    def generate_xlsx_report(self, workbook, data, objs):

        def format_hours(value):
            hours, minutes = divmod(float(value) * 60, 60)
            return '{:02.0f}:{:02.0f}'.format(hours, minutes)

        docs = self.env['report.hr_base_reports.employee_attendance_report'].get_result(data)
        sheet = workbook.add_worksheet('Employee Attendance Transaction')
        if self.env.user.lang != 'en_US':
            sheet.right_to_left()

        format_header = workbook.add_format(
            {'bottom': True, 'bg_color': '#b8bcbf', 'right': True, 'left': True, 'top': True, 'align': 'center'})
        format_cell = workbook.add_format(
            {'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'center'})
        format_title = workbook.add_format(
            {'font_size': 14, 'bottom': True, 'right': True, 'left': True, 'top': True,
             'align': 'center', 'bold': True, 'bg_color': '#0f80d6', 'font_color': 'white'})
        format_title.set_align('center')

        sheet.merge_range('A9:R9', (_("Employee Attendance Transaction")) + " " +
                          data['form']['date_from'] + '  -  ' + data['form']['date_to'], format_title)

        sheet.set_column('B:D', 15)
        sheet.set_column('E:R', 12)

        headers = [
            (_('#')), (_('Date')), (_('Employee ID')), (_('Employee Name')),
            (_('Department')), (_('Job Title')), (_('Swap In Time')), (_('Swap Out Time')),
            (_('Lateness Hours')), (_('Working Hours')), (_('Note')), (_('Shift')),
            (_('Extra Hour')), (_('Leave Name')), (_('Excuse Start Time')),
            (_('Excuse End Time')), (_('Total Employee Late Hours')), (_('Total Late Department')),
            (_('Total Cost')),
        ]

        row = 9
        for col_num, header in enumerate(headers):
            sheet.write(row, col_num, header, format_header)

        row = 10
        seq = 0
        for rec in docs[0]:
            note = ''
            if rec.is_absent:
                note = 'غياب'
            elif rec.public_holiday:
                note = "عطلة رسمية"
            elif rec.official_id:
                note = rec.official_id.mission_type.name
            elif rec.normal_leave:
                note = rec.leave_id.holiday_status_id.name
            elif rec.approve_personal_permission:
                note = rec.personal_permission_id.permission_type_id.name

            attendance_value = rec.get_attendance_value(rec.employee_id, docs[1])
            start = rec.employee_id.get_time_permission(rec.personal_permission_id)
            extra = rec.official_hours - rec.office_hours
            late = rec.break_duration + rec.lateness + rec.approve_exit_out

            seq += 1
            data_row = [
                seq,
                rec.date,
                rec.employee_id.emp_no,
                rec.employee_id.name,
                rec.employee_id.department_id.name,
                rec.employee_id.job_id.name,
                format_hours(rec.sign_in),
                format_hours(rec.sign_out),
                format_hours(rec.lateness),
                format_hours(rec.office_hours),
                note,
                rec.calendar_id.name or '',
                format_hours(rec.additional_hours),
                rec.holiday_name.name if rec.holiday_name else '',
                str(start[0]) if start else '',
                str(start[1]) if start else '',
                format_hours(late),
                format_hours(attendance_value[1]),
                round((rec.break_duration + rec.lateness + rec.approve_exit_out) * attendance_value[0], 2)
            ]

            for col_num, value in enumerate(data_row):
                sheet.write(row, col_num, value, format_cell)

            row += 1


class EmployeeAttendanceReportDetailsXlsx(models.AbstractModel):
    _name = "report.hr_base_reports.employee_attendance_report_details_xlsx"
    _description = 'XLSX Employee Attendance Report'
    _inherit = 'report.report_xlsx.abstract'

    @api.model
    def generate_xlsx_report(self, workbook, data, objs):
        COLUMN_TITLES = {
            'employee_name': _('Employee Name'),
            'department': _('Department'),
            'in_office_count': _('In Office'),
            'tasks': _('Tasks work'),
            'assignments': _('Assignments'),
            'absent': _('Absence'),
            'actual_days_sum': _('Total'),
            'actual_working_days': _('Actual Working Days'),
            'discipline_percentage': _('Discipline Percentage'),
            'early_exit_count': _('Early Exit Count'),
            'lateness_count': _('Lateness Count'),
            'entrance_discipline_percentage': _('Entrance Discipline Percentage'),
            'total_office_hours': _('Total Office Hours'),
            'required_work_hours': _('Required Work Hours'),
            'hours_commitment_percentage': _('Hours Commitment Percentage'),

        }
        # COLUMN_TITLES = {
        #     'employee_name': 'اسم الموظف',
        #     'department': 'الإدارة',
        #     'in_office_count': 'في المكتب',
        #     'tasks': 'مهمة عمل',
        #     'assignments': 'انتدابات',
        #     'absent': 'الغياب',
        #     'actual_days_sum': 'المجموع',
        #     'actual_working_days': 'عدد أيام العمل',
        #     'discipline_percentage': 'نسبة الانضباط',
        #     'early_exit_count': 'عدد مرات الخروج المبكر',
        #     'lateness_count': 'عدد مرات التأخر',
        #     'entrance_discipline_percentage': 'نسبة انضباط الدخول',
        #     'total_office_hours': 'عدد ساعات العمل',
        #     'required_work_hours': 'عدد الساعات المطلوبة',
        #     'hours_commitment_percentage': 'نسبة الالتزام بالساعات'
        # }
        worksheet = workbook.add_worksheet('تفاصيل الحضور')
        bold = workbook.add_format({'bold': True, 'align': 'center'})
        normal = workbook.add_format({'align': 'center'})
        docs, start_date_str, end_date_str = self.env[
            'report.hr_base_reports.employee_attendance_report'].get_value_detailse(data)

        if not docs:
            worksheet.write(0, 0, "لا توجد بيانات")
            return

        all_keys = set()
        flat_rows = []
        dynamic_columns = set()
        for row in docs:
            flat_row = {}
            for key, value in row.items():
                if isinstance(value, dict):
                    for sub_key, sub_val in value.items():
                        name = sub_val.get('name')
                        count = sub_val.get('count')
                        if name:
                            flat_row[name] = count
                            all_keys.add(name)
                            dynamic_columns.add(name)
                else:
                    flat_row[key] = value
                    all_keys.add(key)
            flat_rows.append(flat_row)

        report_title = _('Employee Attendance Summary')

        worksheet.write(0, 4, report_title, workbook.add_format({'bold': True, 'font_size': 14}))
        worksheet.write(1, 4, _('From: ') + start_date_str, workbook.add_format({'bold': True, 'font_size': 14}))
        worksheet.write(1, 3, _('To: ') + end_date_str, workbook.add_format({'bold': True, 'font_size': 14}))

        worksheet.set_row(0, 25)
        worksheet.set_row(1, 25)
        row_num = 4

        FIRST_PART = [
            'employee_name',
            'department',
            'in_office_count',
            'tasks',
            'assignments'
        ]

        LAST_PART = [
            'absent',
            'actual_days_sum',
            'actual_working_days',
            'discipline_percentage',
            'early_exit_count',
            'lateness_count',
            'entrance_discipline_percentage',
            'total_office_hours',
            'required_work_hours',
            'hours_commitment_percentage'
        ]

        headers = []

        for key in FIRST_PART:
            if key in all_keys:
                headers.append(key)

        dynamic_headers = sorted(dynamic_columns)
        headers.extend(dynamic_headers)

        for key in LAST_PART:
            if key in all_keys:
                headers.append(key)
        header_format = workbook.add_format(
            {'bold': True, 'bg_color': '#eeeeee', 'border': 1, 'align': 'center', 'valign': 'vcenter'})

        remaining_keys = [k for k in all_keys if k not in headers]
        headers.extend(sorted(remaining_keys))

        for col, key in enumerate(headers):
            title = COLUMN_TITLES.get(key, key)
            worksheet.write(row_num, col, title, header_format)
            worksheet.set_column(col, col, 25)

        for r, row_data in enumerate(flat_rows, start=row_num + 1):
            for col, key in enumerate(headers):
                value = row_data.get(key)
                if value in (None, '', False):
                    value = 0
                if isinstance(value, (dict, list, tuple)):
                    value = str(value)
                worksheet.write(r, col, value, normal)
        hour_fields = {'total_office_hours', 'required_work_hours'}
        percentage_fields = {
            'discipline_percentage',
            'entrance_discipline_percentage',
            'hours_commitment_percentage',
        }

        def parse_hours(time_str):
            try:
                h, m, s = map(int, time_str.split(':'))
                return h + m / 60 + s / 3600
            except:
                return 0.0

        def parse_percentage(percent_str):
            try:
                return float(percent_str.strip('%'))
            except:
                return 0.0
        totals = {key: 0 for key in headers}

        for row_data in flat_rows:
            for key in headers:
                value = row_data.get(key)
                if value in (None, '', False):
                    value = 0
                try:
                    if key in hour_fields and isinstance(value, str):
                        totals[key] += parse_hours(value)
                    elif key in percentage_fields and isinstance(value, str):
                        totals[key] += parse_percentage(value)
                    elif isinstance(value, (int, float)):
                        totals[key] += value
                    elif isinstance(value, str):
                        totals[key] += float(value)
                except:
                    continue
        total_row_num = row_num + 1 + len(flat_rows)

        for col, key in enumerate(headers):
            total = totals.get(key)

            if key in hour_fields and isinstance(total, (int, float)):
                total_seconds = int(total * 3600)
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                time_str = f"{hours}:{minutes:02}:{seconds:02}"
                worksheet.write(total_row_num, col, time_str, bold)

            elif key in percentage_fields and isinstance(total, (int, float)):
                worksheet.write(total_row_num, col, f"{round(total, 2)}%", bold)

            elif isinstance(total, (int, float)) and total != 0:
                worksheet.write(total_row_num, col, round(total, 2), bold)

            else:
                worksheet.write(total_row_num, col, '', bold)


class EmployeeAttendanceReportDetailsDepartmentXlsx(models.AbstractModel):
    _name = "report.hr_base_reports.employee_attendance_dept_xlsx"
    _description = 'XLSX Department Attendance Report'
    _inherit = 'report.report_xlsx.abstract'

    @api.model
    def generate_xlsx_report(self, workbook, data, objs):

        COLUMN_TITLES = {
            'department_name': _('Department'),
            'employee_count': _('Employee Count'),
            'actual_working_days': _('Actual Working Days'),
            'total_office_hours': _('Total Office Hours'),
            'required_work_hours': _('Required Work Hours'),
            'difference': _('Difference'),
            'avg_sign_in_time': _('Average Sign In Time'),
            'avg_sign_out_time': _('Average Sign Out Time'),
            'avg_office_hours_per_day_formatted': _('Average Office Hours Per Day'),
            'assignments': _('Assignments'),
            'tasks': _('Tasks'),
            'holidays': _('Holidays'),
            'public_holidays': _('Public Holidays'),
            'missions_special': _('Special Missions'),
            'avg_permission_hours_per_day_formatted': _('Average Leave Hours Per Day'),
            'absent': _('Absences')
        }

        # COLUMN_TITLES = {
        #     'department_name': 'اسم القسم',
        #     'employee_count': 'عدد الموظفين',
        #     'actual_working_days': 'عدد أيام العمل الفعلي',
        #     'total_office_hours': 'إجمالي ساعات العمل',
        #     'required_work_hours': 'عدد الساعات المطلوبة',
        #     'difference': 'الفرق',
        #     'avg_sign_in_time': 'متوسط وقت الدخول',
        #     'avg_sign_out_time': 'متوسط وقت الخروج',
        #     'avg_office_hours_per_day_formatted': 'متوسط ساعات العمل اليومية',
        #     'assignments': 'الانتدابات',
        #     'tasks': 'مهام العمل',
        #     'holidays': 'الإجازات',
        #     'public_holidays': 'العطلات الرسمية',
        #     'missions_special': 'المهام الخاصة',
        #     'avg_leave_hours_per_day_formatted': 'متوسط ساعات الإجازة اليومية',
        #     'absent': 'عدد الغيابات'
        # }

        worksheet = workbook.add_worksheet('تفاصيل الحضور حسب القسم')
        bold = workbook.add_format({'bold': True, 'align': 'center'})
        normal = workbook.add_format({'align': 'center'})
        department_summary, start_date_str, end_date_str = self.env[
            'report.hr_base_reports.employee_attendance_report'].get_value_detailse_by_department(data)
        if not department_summary:
            worksheet.write(0, 0, "لا توجد بيانات")
            return

        all_keys = set()
        flat_rows = []
        dynamic_columns = set()
        for row in department_summary:
            flat_row = {}
            for key, value in row.items():
                if isinstance(value, dict):
                    for sub_key, sub_val in value.items():
                        name = sub_val.get('name')
                        count = sub_val.get('count')
                        if name:
                            flat_row[name] = count
                            all_keys.add(name)
                            dynamic_columns.add(name)
                else:
                    flat_row[key] = value
                    all_keys.add(key)
            flat_rows.append(flat_row)
        report_title = _('Department Attendance Summary')

        worksheet.write(0, 4, report_title, workbook.add_format({'bold': True, 'font_size': 14}))
        worksheet.write(1, 4, _(f'From Date: {start_date_str}').format(start_date=start_date_str),
                        workbook.add_format({'bold': True, 'font_size': 14}))
        worksheet.write(1, 3, _(f'To Date: {end_date_str}').format(end_date=end_date_str),
                        workbook.add_format({'bold': True, 'font_size': 14}))

        worksheet.set_row(0, 25)
        worksheet.set_row(1, 25)
        row_num = 4

        FIRST_PART = [
            'department_name',
            'employee_count',
            'actual_working_days',
            'total_office_hours',
            'required_work_hours',
            'difference',
            'avg_sign_in_time',
            'avg_sign_out_time',
            'avg_office_hours_per_day_formatted',
            'assignments',
            'tasks'


        ]

        LAST_PART = [
            'avg_permission_hours_per_day_formatted',
            'absent',
        ]

        headers = []

        for key in FIRST_PART:
            if key in all_keys:
                headers.append(key)

        dynamic_headers = sorted(dynamic_columns)
        headers.extend(dynamic_headers)

        for key in LAST_PART:
            if key in all_keys:
                headers.append(key)
        header_format = workbook.add_format(
            {'bold': True, 'bg_color': '#eeeeee', 'border': 1, 'align': 'center', 'valign': 'vcenter'})

        remaining_keys = [k for k in all_keys if k not in headers]
        headers.extend(sorted(remaining_keys))

        for col, key in enumerate(headers):
            title = COLUMN_TITLES.get(key, key)
            worksheet.write(row_num, col, title, header_format)
            worksheet.set_column(col, col, 25)


        for r, row_data in enumerate(flat_rows, start=row_num + 1):
            for col, key in enumerate(headers):
                value = row_data.get(key)
                if value in (None, '', False):
                    value = 0
                if isinstance(value, (dict, list, tuple)):
                    value = str(value)
                worksheet.write(r, col, value, normal)

        hour_fields = {'total_office_hours', 'required_work_hours','difference','avg_sign_in_time','avg_sign_out_time','avg_office_hours_per_day_formatted','avg_permission_hours_per_day_formatted'}
        totals = {key: 0 for key in headers}
        def parse_hours(time_str):
            try:
                h, m, s = map(int, str(time_str).split(':'))
                return h + m / 60 + s / 3600
            except:
                return 0.0

        for row_data in flat_rows:
            for key in headers:
                value = row_data.get(key)
                if value in (None, '', False):
                    value = 0
                try:
                    if key in hour_fields and isinstance(value, str):
                        totals[key] += parse_hours(value)
                    elif isinstance(value, (int, float)):
                        totals[key] += value
                    elif isinstance(value, str) and value.replace('.', '', 1).isdigit():
                        totals[key] += float(value)
                except:
                    continue

        def format_hours(total):
            total_seconds = int(total * 3600)
            h = total_seconds // 3600
            m = (total_seconds % 3600) // 60
            s = total_seconds % 60
            return f"{h:02}:{m:02}:{s:02}"

        total_row_index = row_num + len(flat_rows) + 1
        for col, key in enumerate(headers):
            total = totals.get(key, '')
            if key in hour_fields:
                value = format_hours(total)
            elif isinstance(total, (int, float)):
                value = round(total, 2) if total != 0 else ''
            else:
                value = ''
            worksheet.write(total_row_index, col, value, bold)




class EmployeeAttendanceSummaryReport(models.AbstractModel):
    _name = 'report.hr_base_reports.employee_attendance_summary_template'
    _description = 'Employee Attendance Summary Report'

    def _get_report_values(self, docids, data=None):
        docs, start_date_str, end_date_str = self.env[
            'report.hr_base_reports.employee_attendance_report'].get_value_detailse(data)

        if not docs:
            return {
                'doc_ids': docids,
                'doc_model': self._name,
                'data': data,
                'docs': [],
                'headers': [],
                'start_date': start_date_str,
                'end_date': end_date_str,
            }

        all_keys = set()
        flat_rows = []
        dynamic_columns = set()

        for row in docs:
            flat_row = {}
            for key, value in row.items():
                if isinstance(value, dict):
                    for sub_key, sub_val in value.items():
                        name = sub_val.get('name')
                        count = sub_val.get('count')
                        if name:
                            flat_row[name] = count
                            all_keys.add(name)
                            dynamic_columns.add(name)
                else:
                    flat_row[key] = value
                    all_keys.add(key)
            flat_rows.append(flat_row)

        FIRST_PART = [
            ('employee_name', 'اسم الموظف'),
            ('department', 'الإدارة'),
            ('in_office_count', 'في المكتب'),
            ('tasks', 'مهام العمل'),
            ('assignments', 'الانتدابات')
        ]

        LAST_PART = [
            ('absent', 'الغياب'),
            ('actual_days_sum', 'المجموع'),
            ('actual_working_days', 'عدد أيام العمل'),
            ('discipline_percentage', 'نسبة الانضباط'),
            ('early_exit_count', 'عدد مرات الخروج المبكر'),
            ('lateness_count', 'عدد مرات التأخر'),
            ('entrance_discipline_percentage', 'نسبة انضباط الدخول'),
            ('total_office_hours', 'إجمالي ساعات العمل'),
            ('required_work_hours', 'عدد الساعات المطلوبة'),
            ('hours_commitment_percentage', 'نسبة الالتزام بالساعات')
        ]


        translated_keys = FIRST_PART + LAST_PART

        header_map = []

        for key, title in FIRST_PART:
            if key in all_keys:
                header_map.append((title, key))

        dynamic_headers = sorted(dynamic_columns)
        for key in dynamic_headers:
            header_map.append((key, key))

        for key, title in LAST_PART:
            if key in all_keys:
                header_map.append((title, key))

        remaining_keys = [k for k in all_keys if
                          k not in [key for key, _ in translated_keys] and k not in dynamic_headers]
        for key in sorted(remaining_keys):
            header_map.append((key, key))

        headers = [title for title, _ in header_map]
        field_keys = [key for _, key in header_map]

        hour_fields = {'total_office_hours', 'required_work_hours'}
        percentage_fields = {
            'discipline_percentage',
            'entrance_discipline_percentage',
            'hours_commitment_percentage',
        }

        def parse_hours(time_str):
            try:
                h, m, s = map(int, time_str.split(':'))
                return h + m / 60 + s / 3600
            except:
                return 0.0

        def parse_percentage(percent_str):
            try:
                return float(percent_str.strip('%'))
            except:
                return 0.0

        totals = {}
        for key in field_keys:
            if key in ['employee_name', 'department']:
                totals[key] = ''
            else:
                totals[key] = 0

        for row_data in flat_rows:
            for key in field_keys:
                value = row_data.get(key)
                if value in (None, '', False):
                    value = 0
                try:
                    if key in hour_fields and isinstance(value, str):
                        totals[key] += parse_hours(value)
                    elif key in percentage_fields and isinstance(value, str):
                        totals[key] += parse_percentage(value)
                    elif isinstance(value, (int, float)):
                        totals[key] += value
                    elif isinstance(value, str):
                        totals[key] += float(value)
                except:
                    continue

        for key in field_keys:
            total = totals[key]
            if key in hour_fields and isinstance(total, (int, float)):
                total_seconds = int(total * 3600)
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                totals[key] = f"{hours}:{minutes:02}:{seconds:02}"
            elif key in percentage_fields:
                totals[key] = f"{round(total, 2)}%"
            elif isinstance(total, (int, float)):
                totals[key] = round(total, 2)
            else:
                totals[key] = ''

        return {
            'doc_ids': docids,
            'doc_model': self._name,
            'data': data,
            'docs': flat_rows,
            'headers': headers,
            'field_keys': field_keys,
            'start_date': start_date_str,
            'end_date': end_date_str,
            'totals': totals,
        }









class DepartmentAttendanceSummaryReport(models.AbstractModel):
    _name = 'report.hr_base_reports.department_attendance_summary_template'
    _description = 'Employee Attendance Summary Report'

    def _get_report_values(self, docids, data=None):
        docs, start_date_str, end_date_str = self.env[
            'report.hr_base_reports.employee_attendance_report'].get_value_detailse_by_department(data)

        if not docs:
            return {
                'doc_ids': docids,
                'doc_model': self._name,
                'data': data,
                'docs': [],
                'headers': [],
                'start_date': start_date_str,
                'end_date': end_date_str,
            }

        all_keys = set()
        flat_rows = []
        dynamic_columns = set()

        for row in docs:
            flat_row = {}
            for key, value in row.items():
                if isinstance(value, dict):
                    for sub_key, sub_val in value.items():
                        name = sub_val.get('name')
                        count = sub_val.get('count')
                        if name:
                            flat_row[name] = count
                            all_keys.add(name)
                            dynamic_columns.add(name)
                else:
                    flat_row[key] = value
                    all_keys.add(key)
            flat_rows.append(flat_row)

        FIRST_PART = [
            ('department_name','اسم القسم'),
            ('employee_count', 'عدد الموظفين'),
            ('actual_working_days','عدد أيام العمل الفعلي'),
            ('total_office_hours','إجمالي ساعات العمل'),
            ('required_work_hours','عدد الساعات المطلوبة'),
            ('difference','الفرق'),
            ('avg_sign_in_time','متوسط وقت الدخول'),
            ('avg_sign_out_time','متوسط وقت الخروج'),
            ('avg_office_hours_per_day_formatted','متوسط ساعات العمل اليومية'),
            ('assignments','الانتدابات'),
            ('tasks','مهام العمل')

        ]

        LAST_PART = [
            ('avg_permission_hours_per_day_formatted','متوسط ساعات الاستئذان'),
            ('absent','عدد الغيابات'),
        ]




        translated_keys = FIRST_PART + LAST_PART

        header_map = []

        for key, title in FIRST_PART:
            if key in all_keys:
                header_map.append((title, key))

        dynamic_headers = sorted(dynamic_columns)
        for key in dynamic_headers:
            header_map.append((key, key))

        for key, title in LAST_PART:
            if key in all_keys:
                header_map.append((title, key))

        remaining_keys = [k for k in all_keys if
                          k not in [key for key, _ in translated_keys] and k not in dynamic_headers]
        for key in sorted(remaining_keys):
            header_map.append((key, key))
        headers = [title for title, _ in header_map]
        field_keys = [key for _, key in header_map]

        hour_fields = {'total_office_hours', 'required_work_hours','difference','avg_sign_in_time','avg_sign_out_time','avg_office_hours_per_day_formatted','avg_permission_hours_per_day_formatted'}
        percentage_fields = set()

        def parse_hours(time_str):
            try:
                h, m, s = map(int, time_str.split(':'))
                return h + m / 60 + s / 3600
            except:
                return 0.0

        totals = {}
        for key in field_keys:
            if key in ['department_name']:
                totals[key] = ''
            else:
                totals[key] = 0

        for row_data in flat_rows:
            for key in field_keys:
                value = row_data.get(key)
                if value in (None, '', False):
                    value = 0
                try:
                    if key in hour_fields and isinstance(value, str):
                        totals[key] += parse_hours(value)
                    elif isinstance(value, (int, float)):
                        totals[key] += value
                    elif isinstance(value, str):
                        totals[key] += float(value)
                except:
                    continue

        for key in field_keys:
            total = totals[key]
            if key in hour_fields and isinstance(total, (int, float)):
                total_seconds = int(total * 3600)
                hours = total_seconds // 3600
                minutes = (total_seconds % 3600) // 60
                seconds = total_seconds % 60
                totals[key] = f"{hours}:{minutes:02}:{seconds:02}"
            elif isinstance(total, (int, float)):
                totals[key] = round(total, 2)
            elif totals[key] == 0:
                totals[key] = ''

        return {
            'doc_ids': docids,
            'doc_model': self._name,
            'data': data,
            'docs': flat_rows,
            'headers': headers,
            'field_keys': field_keys,
            'start_date': start_date_str,
            'end_date': end_date_str,
            'totals': totals,
        }


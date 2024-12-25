# -*- coding: utf-8 -*-

import collections
import datetime
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
import pytz
from pytz import timezone

week_dayS_arabic={0:"الاثنين",  1: 'الثلاثاء',  4:'الجمعة' , 2:'الاربعاء',3: 'الخميس', 6:'الاحد',5: 'السبت'}
class AttendancesReport(models.TransientModel):
    _name = "employee.attendance.report"
    _description = "Employee Attendance Report"

    from_date = fields.Date(string='From Date', required=True)
    to_date = fields.Date(string='To Date', required=True)
    employee_ids = fields.Many2many(comodel_name='hr.employee', string='Employees' ,required=True)
    resource_calender_id = fields.Many2one(comodel_name='resource.calendar', string='Employee work record')
    type = fields.Selection(selection=[('late', 'Late and Early exit'), ('absent', 'Absent'), ('employee', 'Employee')],
                            required=True,
                            default='late', string='Type')

    def print_report(self):
        if not self.employee_ids:
            raise ValidationError(_("Please select Employees Name"))
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'resource_calender_id': self.resource_calender_id.id,
                'from_date': self.from_date,
                'to_date': self.to_date,
                'employee_ids': self.employee_ids.ids,
                'type': self.type,
            },
        }
        return self.env.ref('attendances.general_attendance_action_report').report_action(self, data=data)

    def print_excel_report(self):
        data = {
            'ids': self.ids,
            'model': self._name,
            'form': {
                'resource_calender_id': self.resource_calender_id.id,
                'from_date': self.from_date,
                'to_date': self.to_date,
                'employee_ids': self.employee_ids.ids,
                'type': self.type,
            },
        }
        return self.env.ref('attendances.general_attendance_action_xls').report_action(self, data=data, config=False)


class ReportAttendancePublic(models.AbstractModel):
    _name = 'report.attendances.general_attendances_report_temp'
    _description = "General Attendances Report"

    def get_value(self, data):
        type = data['form']['type']
        employee_ids = data['form']['employee_ids']
        resource_calender_id = data['form']['resource_calender_id']
        from_date = data['form']['from_date']
        to_date = data['form']['to_date']
        domain = [('date', '>=', from_date), ('date', '<=', to_date)]
        data = []
        final_dic = {}
        key_list = []
        total_dic = {}
        mykey = []
        resource = self.env['resource.calendar'].browse(resource_calender_id)
        if resource  and not employee_ids:
            if resource.employee_ids:
                for emp in resource.employee_ids:
                    employee_ids.append(emp.id)
        # if resource_calender_id:
        #     contract_ids = self.env['hr.contract'].search([('state', '=', 'program_directory'), ('resource_calendar_id', '=', resource_calender_id)])
        #     for con in contract_ids:
        #         employee_ids.append(con.employee_id.id)
        # print(">>>>>>>>>>>>>>>>>>>>>>>employeesemployees",employees)
        if employee_ids:
            last_employee_ids = list(set(employee_ids))
            domain.append(('employee_id', 'in', last_employee_ids))
        attendance_transaction_ids = self.env['hr.attendance.transaction'].search(domain)
        employees = attendance_transaction_ids.mapped('employee_id.name')
        employee_ids = attendance_transaction_ids.mapped('employee_id')
        emp_data=[]
        for emp in employee_ids:
            emp_data.append({'job': emp.sudo().job_id.name, 'department': emp.department_id.name,
                                  'emp_no': emp.emp_no,'emp_namw':emp.name})
        grouped_data = collections.defaultdict(list)
        emp_data_dict={}
        for item in emp_data:
            grouped_data[item['emp_namw']].append(item)
        for key,value in grouped_data.items():
            emp_data_dict[key]=list(value)
        if type == 'late':
            for resource in attendance_transaction_ids:
                note=''
                if resource.is_absent:
                    note='غياب'
                elif resource.public_holiday:
                    note="عطلة رسمية"
                elif resource.official_id:
                    note = resource.official_id.mission_type.name
                elif resource.normal_leave:
                    note = resource.leave_id.holiday_status_id.name
                elif resource.approve_personal_permission:
                    note = resource.personal_permission_id.name

                data.append({
                    'date': resource.date,
                    'day': week_dayS_arabic[resource.date.weekday()],
                    'sig_in': resource.sign_in,
                    'sig_out': resource.sign_out,
                    'lateness': resource.lateness,
                    'early_exit': resource.early_exit,
                    'extra_hours': resource.additional_hours,
                    'office_hours':resource.office_hours,
                    'note':note,
                    'department':resource.employee_id.department_id.name,
                    'employee_number':resource.employee_number,
                    'calendar_id':resource.calendar_id.name,
                    'employee_id': resource.employee_id,
                    'employee_name': resource.employee_id.name,
                })

            data=sorted(data, key=lambda d: d['date'])
            for emp in employees:
                list_cat = attendance_transaction_ids.filtered(lambda r: r.employee_id.name == emp)
                total_lateness = sum(list_cat.mapped('lateness'))
                total_early_exit = sum(list_cat.mapped('early_exit'))
                total_late_early = str(datetime.timedelta(minutes=total_early_exit+total_lateness))
                total_extra_hours = sum(list_cat.mapped('additional_hours'))
                total_extra_hours = str(datetime.timedelta(minutes=total_extra_hours))
                list_absent = attendance_transaction_ids.filtered(
                    lambda r: r.employee_id.name == emp and r.is_absent == True)
                total_absent = len(list_absent)
                list_not_log_in = attendance_transaction_ids.filtered(
                    lambda r: r.employee_id.name == emp and r.sign_in == 0.0)
                total_not_sig_in = len(list_not_log_in)
                list_not_log_out = attendance_transaction_ids.filtered(
                    lambda r: r.employee_id.name == emp and r.sign_out == 0.0)
                list_leave = attendance_transaction_ids.filtered(
                    lambda r: r.employee_id.name == emp and (r.normal_leave or r.approve_personal_permission ))
                total_not_sig_out = len(list_not_log_out)
                total_leave = len(list_leave)
                total_dic[emp] = {'total_lateness': total_lateness, 'total_early_exit': total_early_exit,
                                  "total_extra_hours":total_extra_hours, "total_late_early":total_late_early,"total_leave":total_leave,'total_absent': total_absent, 'total_not_sig_in': total_not_sig_in,
                                  'total_not_sig_out': total_not_sig_out}
            grouped = collections.defaultdict(list)
            for item in data:
                grouped[item['employee_name']].append(item)
            for key, value in grouped.items():
                final_dic[key] = list(value)
                key_list.append(key)
            mykey = list(dict.fromkeys(key_list))
            return final_dic, mykey,total_dic,emp_data_dict

        elif type == 'absent':
            for resource in attendance_transaction_ids.filtered(lambda r: r.is_absent == True):
                data.append({
                    'date': resource.date,
                    'employee_name': resource.employee_id.name,
                    'employee_id_department_id_name': resource.employee_id.department_id.name,
                    'day': datetime.datetime.strptime(str(resource.date), '%Y-%m-%d').date().strftime('%A'),
                })
                grouped = collections.defaultdict(list)
                for item in data:
                    grouped[item['employee_id_department_id_name']].append(item)
                for key, value in grouped.items():
                    final_dic[key] = list(value)
                    key_list.append(key)
                mykey = list(dict.fromkeys(key_list))
            return final_dic, mykey, '',emp_data_dict
        elif type == 'employee':
            for emp in employees:
                list_cat = attendance_transaction_ids.filtered(lambda r: r.employee_id.name == emp)
                total_lateness = sum(list_cat.mapped('lateness'))
                total_lateness = str(datetime.timedelta(minutes=total_lateness))
                total_early_exit = sum(list_cat.mapped('early_exit'))
                total_early_exit = str(datetime.timedelta(minutes=total_early_exit))
                total_dic[emp] = {'total_lateness': total_lateness, 'total_early_exit': total_early_exit}
                key_list.append(emp)
            mykey = list(dict.fromkeys(key_list))
            print("mk",mykey,total_dic)
            return '', mykey, total_dic,emp_data_dict

    @api.model
    def _get_report_values(self, docids, data=None):
        final_dic, mykey, total,emp_data = self.get_value(data)
        start_date = data['form']['from_date']
        end_date = data['form']['to_date']
        type = data['form']['type']
        print("dataa",mykey,final_dic)
        local_tz = pytz.timezone(
            self.env.user.tz or 'GMT')
        print_date=datetime.datetime.now(timezone('UTC'))
        print_date=print_date.astimezone(local_tz)
        return {
            'doc_ids': data['ids'],
            'doc_model': data['model'],
            'date_start': start_date,
            'date_end': end_date,
            'type': type,
            'data': final_dic,
            'mykey': mykey,
            'emp_data':emp_data,
            'total': total,
            'print_date':print_date.strftime("%H:%m %m/%d/%Y" ),
            'print_user':self.env.user.name

        }


class AttendancesReportXls(models.AbstractModel):
    _name = 'report.attendances.general_attendance_xls'
    _inherit = 'report.report_xlsx.abstract'

    def generate_xlsx_report(self, workbook, data, datas):
        self = self.with_context(lang=self.env.user.lang)
        x = self.env['report.attendances.general_attendances_report_temp']
        final_dic, mykey, total,emp_data = ReportAttendancePublic.get_value(x, data)
        start_date = data['form']['from_date']
        end_date = data['form']['to_date']
        type = data['form']['type']
        sheet = workbook.add_worksheet(U'Holiday Report')
        sheet.right_to_left()
        sheet.set_column(1, 10, 15)
        # sheet.set_column(6, 100, 25)
        format2 = workbook.add_format(
            {'font_size': 10, 'bottom': True, 'right': True, 'left': True, 'top': True, 'align': 'center',
             'bold': True})
        format2.set_align('center')
        format2.set_align('vcenter')
        if type == 'late':
            sheet.merge_range('D3:I3', _("Attendance Reports"), format2)
            sheet.write('E4:E4', _("From date"), format2)
            sheet.write('G4:G4', _("To date"), format2)
            sheet.write(3, 5, str(start_date)[0:10], format2)
            sheet.write(3, 7, str(end_date)[0:10], format2)
            row = 8
            for key in mykey:
                n = 1
                h_col=4
                size = len(final_dic[key])
                tot_size = len(total[key])
                sheet.write(row - 3, h_col, _('Employee Number'), format2)
                sheet.write(row - 3, h_col+3, _('job '), format2)
                sheet.write(row - 2, h_col, _('Name'), format2)
                sheet.write(row - 2, h_col+3, _('Department'), format2)
                sheet.write(row, n, _('date'), format2)
                sheet.write(row, n+1, _('day'), format2)
                sheet.write(row, n +2 , _('Sign in'), format2)
                sheet.write(row, n + 3, _('Sign out'), format2)
                sheet.write(row, n + 4, _('lateness'), format2)
                sheet.write(row, n + 5, _('Early Exit'), format2)
                sheet.write(row, n + 6, _('Extra hours'), format2)
                sheet.write(row, n + 7, _('Office Hours'), format2)
                sheet.write(row, n + 8, _('Notes'), format2)
                sheet.write(row, n + 9, _('Shift'), format2)
                data_row = row + 1
                total_lateness = total_early_exit = total_extra_hours = total_office_hours = 0.0

                for line in final_dic[key]:

                    sheet.merge_range(row - 3, h_col + 1,row - 3,h_col + 2, emp_data[key][0]['emp_no'], format2)
                    sheet.write(row - 3, h_col + 4, emp_data[key][0]['job'], format2)
                    sheet.merge_range(row - 2, h_col + 1,row - 2,h_col + 2, emp_data[key][0]['emp_namw'], format2)
                    sheet.write(row - 2, h_col + 4, emp_data[key][0]['department'], format2)
                    sheet.write(data_row, n, str(line['date']), format2)
                    sheet.write(data_row, n+1, str(line['day']), format2)

                    sheet.write(data_row, n + 2, '{0:02.0f}:{1:02.0f}'.format(*divmod(float(line['sig_in']) * 60, 60)),
                                format2)
                    sheet.write(data_row, n + 3, '{0:02.0f}:{1:02.0f}'.format(*divmod(float(line['sig_out']) * 60, 60)),
                                format2)
                    sheet.write(data_row, n + 4,
                                '{0:02.0f}:{1:02.0f}'.format(*divmod(float(line['lateness']) * 60, 60)), format2)
                    sheet.write(data_row, n + 5,
                                '{0:02.0f}:{1:02.0f}'.format(*divmod(float(line['early_exit']) * 60, 60)), format2)
                    sheet.write(data_row, n + 6,
                                '{0:02.0f}:{1:02.0f}'.format(*divmod(float(line['extra_hours']) * 60, 60)), format2)
                    sheet.write(data_row, n + 7,
                                '{0:02.0f}:{1:02.0f}'.format(*divmod(float(line['office_hours']) * 60, 60)), format2)

                    sheet.write(data_row, n + 8,line['note'], format2)
                    sheet.write(data_row, n + 9, line['calendar_id'], format2)
                    total_lateness += float(line['lateness'])
                    total_early_exit += float(line['early_exit'])
                    total_extra_hours += float(line['extra_hours'])
                    total_office_hours += float(line['office_hours'])
                    data_row += 1

                sheet.write(data_row + 1, n + 3, _('الاجمالي'), format2)
                sheet.write(data_row + 1, n + 4, '{0:02.0f}:{1:02.0f}'.format(*divmod(total_lateness * 60, 60)),
                            format2)
                sheet.write(data_row + 1, n + 5, '{0:02.0f}:{1:02.0f}'.format(*divmod(total_early_exit * 60, 60)),
                            format2)
                sheet.write(data_row + 1, n + 6, '{0:02.0f}:{1:02.0f}'.format(*divmod(total_extra_hours * 60, 60)),
                            format2)
                sheet.write(data_row + 1, n + 7, '{0:02.0f}:{1:02.0f}'.format(*divmod(total_office_hours * 60, 60)),
                            format2)

                sheet.write(data_row+3, n+4, _('Total lateness'), format2)
                # sheet.set_column(data_row,data_row, 15)
                sheet.write(data_row+3, n + 5, str(total[key]['total_late_early'].split('.')[0]), format2)
                sheet.write(data_row+3, n + 6, _('Total Absent'), format2)
                sheet.write(data_row+3, n + 7, str(total[key]['total_absent']), format2)
                size -= 2
                sheet.write(data_row + 4, n+4, _('Total Extra'), format2)
                sheet.write(data_row + 4, n + 5, str(total[key]['total_extra_hours'].split('.')[0]), format2)
                sheet.write(data_row + 4, n + 6, _('Total Leave'), format2)
                sheet.write(data_row + 4, n + 7, total[key]['total_leave'], format2)
                n += 1
                row += size + 3 + tot_size
        elif type == 'absent':
            sheet.merge_range('C3:G3', _("Absent Report"), format2)
            sheet.merge_range('C4:G4', _("All Employee - Details"), format2)
            sheet.merge_range('B5:C5', _("From date"), format2)
            sheet.merge_range('F5:G5', _("To date"), format2)
            sheet.write(4, 3, str(start_date)[0:10], format2)
            sheet.write(4, 7, str(end_date)[0:10], format2)
            row = 8
            for key in mykey:
                n = 1
                size = len(final_dic[key])
                sheet.write(row - 2, n, _('Department'), format2)
                sheet.write(row, n, _('Employee Name'), format2)
                sheet.write(row, n + 1, _('Day'), format2)
                sheet.write(row, n + 2, _('date'), format2)
                sheet.write(row, n + 3, _('Notes'), format2)
                data_row = row + 1
                for line in final_dic[key]:
                    sheet.write(row - 2, n + 1, line['employee_id_department_id_name'], format2)
                    sheet.write(data_row, n, line['employee_name'], format2)
                    sheet.write(data_row, n + 1, line['day'], format2)
                    sheet.write(data_row, n + 2, line['date'], format2)
                    sheet.write(data_row, n + 3, (' '), format2)
                    data_row += 1
                n += 1
                row += size + 3
        elif type == 'employee':
            sheet.merge_range('C3:G3', _("Employee Attendance Report"), format2)
            sheet.merge_range('B4:C4', _("From date"), format2)
            sheet.merge_range('F4:G4', _("To date"), format2)
            sheet.write(3, 3, str(start_date)[0:10], format2)
            sheet.write(3, 7, str(end_date)[0:10], format2)
            row = 8
            for key in mykey:
                n = 1
                size = len(total[key])
                sheet.write(row, n, _('Employee Name'), format2)
                sheet.write(row, n + 1, _('Total of Lateness '), format2)
                sheet.write(row, n + 2, _('Total of Early Exit'), format2)
                data_row = row + 1
                sheet.write(data_row, n, key, format2)
                sheet.write(data_row, n + 1, total[key]['total_lateness'], format2)
                sheet.write(data_row, n + 2, total[key]['total_early_exit'], format2)
                data_row += 1
                n += 1
                row += size + 1

# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
import logging
_logger = logging.getLogger(__name__)
import json
from ..validator import validator


class Timesheet(models.Model):
    _inherit = 'hr_timesheet.sheet'
    
    def firebase_notification(self, users=None):
    # def timesheet_notification(self,users=None):
        if self.employee_id:
            record = False
            _logger.warning("Write inner");
            lines = []
            for line in self.timesheet_ids:
                v = {
                    'id': line.id,
                    'date': str(line.date),
                    'time': line.unit_amount,
                    'project_id': line.project_id.id,
                    'project_name': line.project_id.name,
                    'task_name': line.task_id.name,
                    'task_id': line.task_id.id,
                    'description': line.name,
                }
                lines.append(v)
            data = {
                'meta': json.dumps({
                    'type': 'timesheet',
                    'data': {
                        'id': self.id,
                        'employee_id': self.employee_id.id, 'employee_name': self.employee_id.name,
                        'state': validator.get_state_name(self, self.state),
                        'period': self.display_name,
                        'start_date': str(self.date_start),
                        'state_name': self.state,
                        'end_date': str(self.date_end),
                        'total_hours': self.total_time,
                        'lines': lines
                    }
                })
            }
            _logger.warning(type(data))
            if users:
                partner = users.mapped('partner_id')
                for part in partner:
                    if not self.env.context.get('refuse'):
                        part.send_notification(
                            _("Employee %s Timesheet Waiting Your Approve") % (self.employee_id.name),
                            " %s - %s" % (self.date_start, self.date_end), data=data, all_device=True)
            self.employee_id.user_id.partner_id.send_notification(
                _("Timesheet Has been Updated to %s") % (validator.get_state_name(self, self.state)),
                " %s - %s" % (self.date_start, self.date_end),
                data=data, all_device=True)

    # #@api.multi
    # def write(self,vals):
    #     res = super(Timesheet, self).write(vals)
    #
    #         return res


class HrHolidays(models.Model):
    _inherit = 'hr.holidays'

    def firebase_notification(self, users=None):
    # def holiday_notification(self,users=None):
        if self.employee_id:
            _logger.warning("Write inner");
            value = {'employee_id':self.employee_id.id, 'employee_name':self.employee_id.name,
                     'id': self.id, 'type': self.holiday_status_id.name, 'type_value': self.holiday_status_id.id,
                     'replacement_id': self.replace_by.id if self.replace_by else False,
                     'replacement_name': self.replace_by.name if self.replace_by else False,
                     'state_name': self.state,
                     'start_date': str(self.date_from), 'end_date': str(self.date_to), 'attachment': self.get_attchment(self),
                     'reason': self.name, 'state': validator.get_state_name(self, self.state)}
            if self.issuing_ticket:
                value.update({'issuing_clearance_form': self.issuing_clearance_form,
                              'issuing_deliver_custdy': self.issuing_deliver_custdy,
                              'permission_request_for': self.permission_request_for,
                              'issuing_exit_return': self.issuing_exit_return,
                              'exit_return_duration': self.exit_return_duration,
                              'ticket_cash_request_type_id': self.ticket_cash_request_type.id if self.ticket_cash_request_type else False,
                              'ticket_cash_request_type_name': self.ticket_cash_request_type.name if self.ticket_cash_request_type else False,
                              'ticket_cash_request_for': self.ticket_cash_request_for,
                              'issuing_ticket': self.issuing_ticket})
            data = {
                'meta': json.dumps({
                    'type': 'leave',
                    'data': value,
                })
            }
            _logger.warning(type(data))
            # _logger.warning(data)
            if users:
                partner = users.mapped('partner_id')
                for part in partner:
                    if not self.env.context.get('refuse'):
                        part.send_notification(_("Employee %s Leave Waiting Your Approve") % (self.employee_id.name),
                            " %s - %s" % (str(self.date_from), str(self.date_to)), data=data, all_device=True)
            self.employee_id.user_id.partner_id.send_notification(
                _("Leave Request Has Been Updated to %s") % (validator.get_state_name(self, self.state)),
                " %s - %s " % (self.date_from, self.date_to),
                data=data, all_device=True)

    def get_attchment(self, res_id):
        attachment = self.env['ir.attachment'].search([('res_model', '=', 'hr.holidays'), ('res_id', '=', res_id.id)])
        li = []
        if attachment:
            url_base = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            for att in attachment:
                url = url_base + "/api/content/%s" % (att.id)
                li.append(url)
        return li


class Overtime(models.Model):
    _inherit = 'employee.overtime.request'

    def firebase_notification(self, users=None):
    # def overtime_notification(self,users=None):
        records = False
        value = {'id': self.id, 'transfer_type': self.transfer_type, 'request_date': str(self.request_date),
                 'date_from': str(self.date_from), 'state_name': self.state,

                 'date_to': str(self.date_to), 'state': validator.get_state_name(self, self.state),
                 'reason': self.reason}
        record = value
        for rec in self.line_ids_over_time:
            if rec.employee_id:
                _logger.warning("Write inner");
                li = []
                if self.line_ids_over_time:
                    record = self.line_ids_over_time.filtered(lambda r: r.employee_id == rec.employee_id)
                    if record:
                        for r in record:
                            val = {
                                'employee_id': rec.employee_id.id, 'employee_name': rec.employee_id.name,
                                'id': r.id,
                                'over_time_workdays_hours': r.over_time_workdays_hours,
                                'over_time_vacation_hours': r.over_time_vacation_hours,
                                'price_hour': r.price_hour,
                            }
                            li.append(val)
                value['lines'] = li
                data = {
                    'meta': json.dumps({
                        'type': 'overtime',
                        'data':value
                    })
                }
                _logger.warning(type(data))
                if users:
                    partner = users.mapped('partner_id')
                    for part in partner:
                        if not self.env.context.get('refuse'):
                            part.send_notification(_("Employee Overtime Request Waiting Your Approve"),
                                                   " %s - %s" % (self.date_from, self.date_to), data=data,
                                                   all_device=True)
                if rec.employee_id.user_id:
                    rec.employee_id.user_id.partner_id.send_notification(
                        _("Overtime Request has been Updated to %s ") % (validator.get_state_name(self, self.state)), " %s - %s" % (self.date_from, self.date_to),
                        data=data, all_device=True)


class HrPersonalPermission(models.Model):
    _inherit = 'hr.personal.permission'

    # @api.multi
    def firebase_notification(self, users=None):
    # def permission_notification(self,users=None):
        if self.employee_id:
            value = {'employee_id':self.employee_id.id, 'employee_name':self.employee_id.name, 'id': self.id, 'date_from': str(self.date_from), 'date_to': str(self.date_to), 'duration': self.duration,
                     'date': str(self.date), 'state_name': self.state,
                     'state': validator.get_state_name(self, self.state), 'early_exit': self.early_exit,
                     'attachment': self.get_attchment(self)}

            _logger.warning("Write inner");
            data = {
                'meta': json.dumps({
                    'type': 'permission',
                    'data': value
                })
            }
            _logger.warning(type(data))
            if users:
                partner = users.mapped('partner_id')
                for part in partner:
                    if not self.env.context.get('refuse'):
                        part.send_notification(_("Employee %s Permission Waiting Your Approve") % (self.employee_id.name),
                                               " %s - %s" % (self.date_from, self.date_to), data=data, all_device=True)
            self.employee_id.user_id.partner_id.send_notification(
                _("Permission Request has been updated to %s ") % (validator.get_state_name(self, self.state)) , " %s - %s" % (self.date_from, self.date_to),
                data=data, all_device=True)

    def get_attchment(self, res_id):
        attachment = self.env['ir.attachment'].search([('res_model', '=', 'hr.holidays'), ('res_id', '=', res_id.id)])
        li = []
        if attachment:
            url_base = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            for att in attachment:
                url = url_base + "/api/content/%s" % (att.id)
                li.append(url)
        return li


#
class HrSalaryAdvance(models.Model):
    _inherit = 'hr.loan.salary.advance'

    # @api.multi
    def firebase_notification(self, users=None):
    # def firebase_notification(self, users=None):
        if self.employee_id:
            _logger.warning("Write inner");
            value = {'employee_id':self.employee_id.id, 'employee_name':self.employee_id.name, 'id': self.id, 'code': self.code, 'expect_amount': self.emp_expect_amount, 'date': str(self.date),
                     'installment_amount': self.installment_amount, 'state': validator.get_state_name(self, self.state),
                     'months': self.months, 'state_name': self.state,

                     'request_type_id': self.request_type.id, 'request_type_name': self.request_type.name}
            lines = []
            if self.deduction_lines:
                for l in self.deduction_lines:
                    vals = {
                        'installment_date': str(l.installment_date),
                        'installment_amount': l.installment_amount,
                        'paid': l.paid
                    }
                    lines.append(vals)
            value['lines'] = lines
            data = {
                'meta': json.dumps({
                    'type': 'loan',
                    'data': value
                })
            }
            _logger.warning(type(data))
            if users:
                partner = users.mapped('partner_id')
                for part in partner:
                    if not self.env.context.get('refuse'):
                        part.send_notification(_("Employee %s Loan  %s Waiting Your Approve") % (self.employee_id.name, self.code),
                                               _("Loan  %s Waiting Your Approve") % (self.code), data=data, all_device=True)
            self.employee_id.user_id.partner_id.send_notification(
                _("Loan %s") % (self.code), _("Has been updated to %s") % (validator.get_state_name(self, self.state)),
                data=data, all_device=True)

class HrOfficialMission(models.Model):
    _inherit = 'hr.official.mission'

    def firebase_notification(self, users=None):
        if self.employee_id:
            value = {'employee_id':self.employee_id.id, 'employee_name':self.employee_id.name, 'id': self.id, 'date_from': str(self.date_from), 'date_to': str(self.date_to), 'duration': self.date_duration,
                     'date': str(self.date), 'state_name': self.state,
                     'state': validator.get_state_name(self, self.state)}

            _logger.warning("Write inner")
            data = {
                'meta': json.dumps({
                    'type': 'mission',
                    'data': value
                })
            }
            _logger.warning(type(data))
            if users:
                partner = users.mapped('partner_id')
                for part in partner:
                    if not self.env.context.get('refuse'):
                        part.send_notification(_("Employee %s Mission Waiting Your Approve") % (self.employee_id.name),
                                               " %s - %s" % (self.date_from, self.date_to), data=data, all_device=True)
            self.employee_id.user_id.partner_id.send_notification(
                _("Mission Request has been updated to %s ") % (validator.get_state_name(self, self.state)) , " %s - %s" % (self.date_from, self.date_to),
                data=data, all_device=True)


class EmployeeOtherRequest(models.Model):
    _inherit = 'employee.other.request'

    def firebase_notification(self, users=None):
        if self.employee_id:
            value = {'employee_id':self.employee_id.id, 'employee_name':self.employee_id.name, 'id': self.id, 'request_type': self.request_type,
                     'date': str(self.date), 'state_name': self.state,
                     'state': validator.get_state_name(self, self.state)}

            _logger.warning("Write inner")
            data = {
                'meta': json.dumps({
                    'type': 'other_request',
                    'data': value
                })
            }
            _logger.warning(type(data))
            if users:
                partner = users.mapped('partner_id')
                for part in partner:
                    if not self.env.context.get('refuse'):
                        part.send_notification(_("Employee %s Salary Definition and Confirmation Order Waiting Your Approve") % (self.employee_id.name),
                                               " %s" % self.date, data=data, all_device=True)
            self.employee_id.user_id.partner_id.send_notification(
                _("The Salary Definition and Confirmation Order Request has been updated to %s ") % (validator.get_state_name(self, self.state)) , " %s" % self.date,
                data=data, all_device=True)

class HrAttendanceRegister(models.Model):
    _inherit = 'hr.attendance.register'

    def firebase_notification(self, users=None):
        if self.employee_id:
            value = {'employee_id':self.employee_id.id, 'employee_name':self.employee_id.name, 'id': self.id, 'action_type': self.action_type,
                     'register_date': str(self.register_date), 'action_date': str(self.action_date),'state_name': self.state,
                     'state': validator.get_state_name(self, self.state)}

            _logger.warning("Write inner")
            data = {
                'meta': json.dumps({
                    'type': 'attendance_register',
                    'data': value
                })
            }
            _logger.warning(type(data))
            if users:
                partner = users.mapped('partner_id')
                for part in partner:
                    if not self.env.context.get('refuse'):
                        part.send_notification(_("Employee %s Attendance Register Order Waiting Your Approve") % (self.employee_id.name),
                                               " %s" % self.register_date, data=data, all_device=True)
            self.employee_id.user_id.partner_id.send_notification(
                _("Attendance Register Order Request has been updated to %s ") % (validator.get_state_name(self, self.state)) , " %s" % self.register_date,
                data=data, all_device=True)
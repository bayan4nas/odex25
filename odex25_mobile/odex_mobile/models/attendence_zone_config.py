# -*- coding: utf-8 -*-
from odoo import models,fields,api,_
from odoo.exceptions import ValidationError
import datetime



class AttendanceZone(models.Model):
    _name = 'attendance.zone'
    _description = "Attendance Location for mobile"

    name = fields.Char(string="Zone Name",required=True)
    zone = fields.Char(string="Zone Name",)
    latitude = fields.Char(string="Latitude")
    longitude = fields.Char(string="Longitude")
    allowed_range = fields.Char(string="Allowed Range")
    general = fields.Boolean(string="General Zone")
    specific = fields.Boolean(string="Specific Zone")
    specific_period = fields.Boolean(string="Specific Period")
    start = fields.Date(string="Start Date")
    end = fields.Date(string="End Date")
    all_employee = fields.Boolean(string="All Employees")
    active_check = fields.Boolean(string="Archive",default=True)
    employee_ids = fields.Many2many('hr.employee',string="Employees",required=True)
    loc_ch_intv = fields.Integer('Location Change Interval - Minutes', default=1)
    loc_ch_dist = fields.Integer('Location Change Distance - Meter', default=100)
    srv_ch_tmout = fields.Integer('Services Change Timeout - Minutes', default=5)
    app_cl_tmout = fields.Integer('App Close Timeout - Minutes', default=5)

    auto_checkout = fields.Integer(string="Auto Checkout After" ,default=10)

    @api.constrains('start','end')
    def start_end(self):
        for rec in self:
            if rec.start and rec.end and rec.end < rec.start:
                raise ValidationError(_("End date should be greater than end start date"))

    @api.constrains('general','specific','all_employee','specific_employee')
    def constrain_type_general(self):
        for rec in self:
            if rec.general and rec.specific:
                raise ValidationError(_("You can not define general and specific zone at same time"))

    @api.onchange('all_employee')
    def get_employees(self):
        for rec in self:
            rec.employee_ids = False
            if rec.all_employee:
                emp_lst = rec.env['hr.employee'].sudo().search([('state','=','open')])
                if emp_lst:
                    rec.employee_ids = emp_lst.ids

    @api.model
    def archive_zone(self):
        date =  fields.Date.today()
        record = self.env['attendance.zone'].search([('specific_period','=',True),('end','<=',str(date)),('active_check','=',True)])
        if record:
            for r in record:
                r.active_check = False

    @api.model
    def get_coordinates(self):
        coordinates = self.env['attendance.zone'].search([], limit=1)
        data = {"lng":coordinates.longitude,"lat": coordinates.latitude,'range':coordinates.allowed_range}
        return data

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    auto_checkout = fields.Integer(related="company_id.auto_checkout" ,string="Auto Checkout After",readonly=False)
    fcm_server_key = fields.Char(string='Server Key:', related="company_id.fcm_server_key", readonly=False)
    service_account = fields.Binary(string='Service Account:', related="company_id.service_account", readonly=False)
    jwt_expire_days = fields.Integer(related='company_id.jwt_expire_days', readonly=False)
    sender_id = fields.Char(string='Sender ID:', related="company_id.sender_id", readonly=False)

class ResCompany(models.Model):
    _inherit = 'res.company'

    auto_checkout = fields.Integer(string="Auto Checkout After")
    fcm_server_key = fields.Char(string='Server Key')
    service_account = fields.Binary(string='Service Account', attachment=True)
    jwt_expire_days = fields.Integer(string="JWT expire (days)", default=14)
    sender_id = fields.Char(string='Sender ID')


from odoo import models, fields, api, _
import logging
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class RequestVehicleDelegation(models.Model):
    _name = 'request.vehicle.authorization'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    employee_id = fields.Many2one('hr.employee', string="Driver", default=lambda item: item.get_user_id(),
                                  tracking=True, required=True)
    state = fields.Selection(selection=[('draft', 'Draft'),
                                        ('confirm', 'Confirm'),
                                        ('direct_manager', 'Direct manager'),
                                        ('refused', 'Refused'),
                                        ('fleet_tool', 'Fleet tool'),
                                        ], default='draft', tracking=True)
    company_id = fields.Many2one('res.company', string='Company')
    project_id = fields.Many2one('project.project', string='Project')
    delegation_type = fields.Selection(selection=[('branch', 'Branch'), ('driver', 'driver')],
                                       string="Delegation Type")
    license_number = fields.Char(string="License Number", related='employee_id.license_number', tracking=True,
                                 readonly=False, required=True)
    license_end = fields.Date(string="License End", tracking=True, related='employee_id.license_end', readonly=False,
                              required=True)
    license_type = fields.Selection(selection=[('private', 'Private'), ('general', 'General'), ('public', 'Public')],
                                    string="License Type", related='employee_id.license_type', readonly=False,
                                    required=True)
    license_start = fields.Date(string="License Start", related='employee_id.license_start', readonly=False,
                                required=True)
    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle", tracking=True, required=True,
                                 domain=lambda self: [('id', 'not in', self._get_delegated_vehicle_ids())])

    license_plate = fields.Char(required=True, related='vehicle_id.license_plate', store=True, tracking=True, )
    vin_sn = fields.Char('Chassis Number', related='vehicle_id.vin_sn', store=True,
                         copy=False)
    model_id = fields.Many2one('fleet.vehicle.model', 'Model', related='vehicle_id.model_id', store=True, tracking=True)
    fleet_type_id = fields.Many2one('fleet.type', string="Fleet Type", related='vehicle_id.fleet_type_id', store=True,
                                    tracking=True)
    serial_number = fields.Char(related='vehicle_id.serial_number', string="Serial Number")
    # state_id = fields.Many2one('res.country.state', string="State", )
    start_date = fields.Date(string="Start Date", tracking=True)
    end_date = fields.Date(string="End Date", tracking=True)
    reason = fields.Text(string="Reject Reason", tracking=True, )
    custody_id = fields.Many2one('custom.employee.custody')
    entity_type = fields.Selection(selection=[('department', 'Department'), ('project', 'Project')],
                                   string="Entity Type")
    driver_department = fields.Many2one('driver.department', tracking=True)
    first_odometer = fields.Float(string='First Odometer', compute="get_first_odometer", store=True,
                                  help='The odometer value at the moment the car is authorized')
    odometer = fields.Float(string='Last Odometer', compute="get_odometer", store=True,
                            help='Odometer measure of the vehicle at the moment of this log', tracking=True)
    km_number = fields.Integer(string='KM Number', compute='get_km', store=True,
                               help='The value of the difference between the odometer at the moment of delivery and receipt')
    last_department_id = fields.Many2one(related='vehicle_id.department_id', string="Last Department",
                                         help='The last Department the vehicle was authorized for')
    last_project_id = fields.Many2one('project.project', string='Last Project', compute="get_last_project", store=True,
                                      tracking=True)
    last_branch_id = fields.Many2one('hr.department', string="Last Branch", compute="get_last_branch", store=True,
                                     help='The last Branch the vehicle was authorized for', tracking=True)
    from_hr_depart = fields.Boolean()
    name = fields.Char(string="Name")
    depart_id = fields.Many2one('hr.department', related='employee_id.department_id')
    driver = fields.Boolean(string="Is Driver", related='employee_id.driver')

    @api.onchange('license_number', 'license_end', 'license_type', 'license_start')
    def _onchange_license_fields(self):
        if self.employee_id:
            if self.license_number:
                self.employee_id.license_number = self.license_number
            if self.license_end:
                self.employee_id.license_end = self.license_end
            if self.license_type:
                self.employee_id.license_type = self.license_type
            if self.license_start:
                self.employee_id.license_start = self.license_start

    @api.onchange('driver')
    def _onchange_driver(self):
        if self.employee_id and not self.driver:
            self.driver = True
            self.employee_id.driver = True

    @api.model
    def _get_delegated_vehicle_ids(self):
        delegated_vehicles = self.env['vehicle.delegation'].search([
            ('state', 'in', ['draft', 'confirm', 'approve', 'in_progress'])
        ])
        return delegated_vehicles.mapped('vehicle_id.id')

    def get_user_id(self):
        employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        if employee_id:
            return employee_id.id
        else:
            return False

    @api.depends("vehicle_id")
    def get_first_odometer(self):
        for rec in self:
            if rec.vehicle_id:
                odometer_id = self.env['fleet.vehicle.odometer'].search([('vehicle_id', '=', rec.vehicle_id.id)],
                                                                        order="date desc", limit=1)
                rec.first_odometer = odometer_id.value

    @api.depends("vehicle_id")
    def get_odometer(self):
        for rec in self:
            if rec.vehicle_id:
                odometer_id = self.env['fleet.vehicle.odometer'].search([('vehicle_id', '=', rec.vehicle_id.id)],
                                                                        order="date asc", limit=1)
                rec.odometer = odometer_id.value

    @api.depends("vehicle_id")
    def get_last_project(self):
        for rec in self:
            obj = self.search([('vehicle_id', '=', rec.vehicle_id.name)], limit=1)
            rec.last_project_id = obj.project_id

    @api.depends("vehicle_id")
    def get_last_branch(self):
        for rec in self:
            rec.last_branch_id = rec.vehicle_id.branch_id

    @api.depends('odometer', 'first_odometer')
    def get_km(self):
        for rec in self:
            rec.km_number = rec.odometer - rec.first_odometer

    def action_confirm(self):
        for rec in self:
            rec.state = 'confirm'

    def action_refuse(self):
        form_view_id = self.env.ref("odex_fleet.wizard_reject_reason_fleet_wiz_form").id
        return {
            'name': _("Reject Reason"),

            'view_mode': 'form',
            'res_model': 'reject.reason.fleet.wiz',
            'views': [(form_view_id, 'form')],
            'type': 'ir.actions.act_window',
            'target': 'new',
            'context': {'default_delegation_id': self.id},
        }

    def direct_manager(self):
        for rec in self:
            rec.state = 'direct_manager'
            rec.send_notification_to_direct_manager_groups()

    def send_notification_to_fleet_tool_group(self):
        message_template = 'Dear {user_name}, you have an authorization request awaiting approval'
        group = self.env.ref('odex_fleet.group_fleet_tool')
        users = group.users

        for user in users:
            if user.partner_id:
                message_body = message_template.format(user_name=user.name)

                # Send the notification to appear as a real notification in Odoo
                self.env['mail.message'].create({
                    'message_type': 'notification',
                    'subtype_id': self.env.ref('mail.mt_comment').id,
                    'body': message_body,
                    'subject': 'New authorization request',
                    'partner_ids': [(4, user.partner_id.id)],
                    'model': 'request.vehicle.authorization',
                    'res_id': self.id,
                    'author_id': self.env.user.partner_id.id,
                    'notification_ids': [(0, 0, {
                        'res_partner_id': user.partner_id.id,
                        'notification_type': 'inbox'
                    })]
                })

    def send_notification_to_direct_manager_groups(self):
        message_template = 'Dear {user_name}, you have an authorization request awaiting approval'
        groups = [
            self.env.ref('odex_fleet.group_direct_manager')
        ]
        for group in groups:
            users = group.users
            for user in users:
                if user.partner_id:
                    message_body = message_template.format(user_name=user.name)

                    # Send the notification to appear as a real notification in Odoo
                    self.env['mail.message'].create({
                        'message_type': 'notification',
                        'subtype_id': self.env.ref('mail.mt_comment').id,
                        'body': message_body,
                        'subject': 'New authorization request',
                        'partner_ids': [(4, user.partner_id.id)],
                        'model': 'request.vehicle.authorization',
                        'res_id': self.id,
                        'author_id': self.env.user.partner_id.id,
                        'notification_ids': [(0, 0, {
                            'res_partner_id': user.partner_id.id,
                            'notification_type': 'inbox'
                        })]
                    })

    def fleet_tool(self):

        vehicle_vals = {
            'employee_id': self.employee_id.id,
            'name': self.name,
            'delegation_type': 'driver',
            'license_number': self.license_number,
            'license_end': self.license_end,
            'vehicle_id': self.vehicle_id.id,
            'license_plate': self.license_plate,
            'start_date': self.start_date,
            'end_date': self.end_date,
            'first_odometer': self.first_odometer,
            'odometer': self.odometer,
            'km_number': self.km_number,
            'last_department_id': self.last_department_id.id,
            'last_project_id': self.last_project_id.id if self.last_project_id else False,
            'last_branch_id': self.last_branch_id.id,
            'custody_id': self.custody_id.id if self.custody_id else False,
            'depart_id': self.depart_id.id if self.depart_id else False,
            'request_vehicle_authorization': self.id
        }
        _logger.info("Attempting to create vehicle delegation with values: %s", vehicle_vals)

        vehicle = self.env['vehicle.delegation'].create(vehicle_vals)
        _logger.info("Created vehicle delegation: %s", vehicle)
        self.send_notification_to_fleet_tool_group()
        self.state = "fleet_tool"

        return vehicle


class InheritVehicleDelegation(models.Model):
    _inherit = "vehicle.delegation"

    request_vehicle_authorization = fields.Many2one('request.vehicle.authorization')

from odoo import api,fields, models ,_
from odoo.exceptions import UserError, ValidationError



class FleetFuel(models.Model):
    _inherit = 'fleet.vehicle.log.fuel'

    integration_with_accounting = fields.Boolean(string='Integration With Accounting',compute="get_integ")
    state_a = fields.Selection(related='state')
    state_b = fields.Selection(related='state')
    @api.depends("vehicle_id")
    def get_integ(self):
        config = self.env["res.config.settings"].sudo().search([], limit=1, order="id desc")
        self.integration_with_accounting = config.integration_with_accounting_configuration

class FleetMaintenance(models.Model):
    _inherit = 'fleet.maintenance'

    integration_with_accounting = fields.Boolean(string='Integration With Accounting',compute="get_integ")
    state_a = fields.Selection(related='state')
    state_b = fields.Selection(related='state')
    @api.depends("vehicle_id")
    def get_integ(self):
        config = self.env["res.config.settings"].sudo().search([],limit=1 ,order ="id desc")
        self.integration_with_accounting = config.integration_with_accounting_configuration

    def action_approve(self):
        for rec in self:
            record = rec.quotation_ids.sudo().filtered(lambda r: r.approve == True)
            if not record and rec.integration_with_accounting == True:
                raise ValidationError(_("You Need Approve Quotation First"))
            else:
                print("no Validation")
            rec.state = 'approve'
            rec.vehicle_id.next_request_date = rec.next_request_date

class FormRenew(models.Model):
    _inherit = 'form.renew'

    integration_with_accounting = fields.Boolean(string='Integration With Accounting',compute="get_integ")

    @api.depends("vehicle_id")
    def get_integ(self):
        config = self.env["res.config.settings"].sudo().search([],limit=1 ,order ="id desc")
        self.integration_with_accounting = config.integration_with_accounting_configuration

class FleetServices(models.Model):
    _inherit = 'fleet.vehicle.log.services'

    integration_with_accounting = fields.Boolean(string='Integration With Accounting',compute="get_integ")
    status_a = fields.Selection(related='status')
    status_b = fields.Selection(related='status')
    @api.depends("vehicle_id")
    def get_integ(self):
        config = self.env["res.config.settings"].sudo().search([],limit=1 ,order ="id desc")
        self.integration_with_accounting = config.integration_with_accounting_configuration


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    integration_with_accounting_configuration = fields.Boolean(string='Integration With Accounting',config_parameter='odex25_fleet_account_custom.integration_with_accounting_configuration')

    @api.depends('integration_with_accounting_configuration')
    def _compute_integration_with_accounting(self):
        group1 = self.env.ref('odex25_fleet_account_custom.integration_with_account')
        group2 = self.env.ref('odex25_fleet_account_custom.disable_integration_with_account')
        for record in self:
            if record.integration_with_accounting_configuration == True:
                group1.write({'users': [(4, self.env.user.id)]})
                group2.write({'users': [(3, self.env.user.id)]})
            else:
                group1.write({'users': [(3, self.env.user.id)]})
                group2.write({'users': [(4, self.env.user.id)]})


    @api.model
    def create(self, values):
        # Call the create method of the superclass
        record = super(ResConfigSettings, self).create(values)

        # Call the dependency computation method to perform the desired actions
        record._compute_integration_with_accounting()

        return record

    def write(self, values):
        # Call the write method of the superclass
        result = super(ResConfigSettings, self).write(values)

        # Call the dependency computation method to perform the desired actions
        self._compute_integration_with_accounting()

        return result

from odoo import fields, models, api, _

class ProjectProjectInherit(models.Model):

    _inherit = 'project.project'

    #Fields for 'Home restoration' service and 'alternative_housing' service
    requested_service_amount = fields.Float(string="Requested Service Amount")
    restoration_max_amount = fields.Float(string='Restoration Max Amount')
    has_money_field_is_appearance = fields.Boolean(string='Has money Field is appearance?')
    has_money_to_pay_first_payment = fields.Boolean(string='Has money to pay first payment?')
    is_family_need_evacuate = fields.Boolean(string='Is family need evacuate?')
    #Fields for 'complete building house' service
    max_complete_building_house_amount = fields.Float(string='Max Complete Building House Amount')
    has_money_for_payment_is_appearance = fields.Boolean(string='Has money Field is appearance?')
    has_money_for_payment = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Has money for payment?')
    service_type = fields.Selection(
        [('rent', 'Rent'), ('home_restoration', 'Home Restoration'), ('alternative_housing', 'Alternative Housing'),
         ('home_maintenance', 'Home Maintenance')
            , ('complete_building_house', 'Complete Building House')], string='Service Type')
    service_requests_count = fields.Integer(
        string="Service Requests",
        compute='_compute_service_requests_count'
    )

    def _compute_service_requests_count(self):
        for rec in self:
            # Replace `related_field_ids` with the actual field
            # holding the relationship (e.g., a One2many field)
            rec.service_requests_count = self.env['service.request'].search_count([('project_id','=',rec.id)])

    def action_view_related_records(self):
        return {
            'name': 'Services Requests',
            'type': 'ir.actions.act_window',
            'res_model': 'service.request',  # replace with the actual model name
            'view_mode': 'tree,form',
            'domain': [('project_id', '=', self.id)],  # adjust the domain as needed
            'context': {'create': False},
            'target': 'current',
        }
    def create_alternative_housing_request(self):
        for rec in self:
            alternative_housing_request = self.env['service.request'].create(
                {
                    'family_id': self.env['grant.benefit'].search([('partner_id','=',rec.beneficiary_id.id)]).id,
                    'benefit_type':'family',
                    'service_cat': self.env['services.settings'].search([('service_type','=','alternative_housing')],limit=1).id,
                    'project_id': self.id
                }
            )
            alternative_housing_request.write({
                'main_service_category':alternative_housing_request.service_cat.parent_service.parent_service,
                'sub_service_category' : alternative_housing_request.service_cat.parent_service,
            })
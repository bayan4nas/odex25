from odoo import models, fields, _, api
from odoo.exceptions import ValidationError


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    plan_by = fields.Selection(string='Plan By', related='company_id.plan_by', readonly=False)
    detailed_plan_unit = fields.Selection(string="Detailed Plan Unit", related='company_id.detailed_plan_unit',
                                          readonly=False)
    plan_by_departments = fields.Boolean(string="Plan By Departments", related='company_id.plan_by_departments',
                                         readonly=False)

    @api.constrains('detailed_plan_unit')
    def detailed_plan_unit_constrain(self):
        plan_unit = self.env['time.plan.details'].search([])
        if plan_unit:
            raise ValidationError(_("sorry the Detailed Plan Unit can not be changed after set"))

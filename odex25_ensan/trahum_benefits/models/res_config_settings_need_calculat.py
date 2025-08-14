from odoo import models, fields, api
from odoo.exceptions import ValidationError

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    base_line_value = fields.Float(string="Base Line", config_parameter='trahum_benefits.base_line_value')

    ratio_parent = fields.Float(
        string="Head of Household Ratio",
        config_parameter='trahum_benefits.ratio_parent'
    )
    ratio_above_18 = fields.Float(
        string="Dependent Above 18 Ratio",
        config_parameter='trahum_benefits.ratio_above_18'
    )
    ratio_under_18 = fields.Float(
        string="Dependent Under 18 Ratio",
        config_parameter='trahum_benefits.ratio_under_18'
    )

    @api.constrains('ratio_under_18', 'ratio_above_18')
    def _check_needs(self):
        print(self.ratio_above_18,self.ratio_under_18)

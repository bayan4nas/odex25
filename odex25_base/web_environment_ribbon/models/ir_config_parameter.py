from odoo import fields, models, api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    ribbon_display = fields.Boolean(
        string="Display Ribbon",
        help="If checked, the ribbon will be displayed; otherwise, it will be hidden.",
        readonly=False
    )

    @api.model
    def get_values(self):
        res = super(ResConfigSettings, self).get_values()
        res.update(
            ribbon_display=self.env['ir.config_parameter'].sudo().get_param('ribbon_display', default=False)
        )
        return res

    def set_values(self):
        super(ResConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('ribbon_display', self.ribbon_display)

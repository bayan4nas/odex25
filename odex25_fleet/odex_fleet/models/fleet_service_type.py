from odoo import models, fields, api, _
from odoo.api import returns


class FleetServiceType(models.Model):
    _inherit = 'fleet.service.type'
    _description = 'Fleet Service Type'

    category = fields.Selection(selection='get_new_category_selection', string='Category', required=True,
                                help='Choose whether the service refer to contracts, vehicle services or both')

    def get_new_category_selection(self):
        selection = [(_('service'), _('Service'))]
        return selection

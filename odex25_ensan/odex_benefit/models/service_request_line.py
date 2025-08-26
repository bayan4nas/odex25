from odoo import fields, models, api, _
from odoo.exceptions import UserError, ValidationError



class ServiceRequestLine(models.Model):
    _name = 'service.request.line'
    _description = 'Service Request Product Line'

    request_id = fields.Many2one('service.request', string='Service Request', ondelete='cascade')
    product_id = fields.Many2one('product.template', string='Product', required=True)
    quantity = fields.Float(string='Quantity', required=True, default=1.0)
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure', required=True)
    description = fields.Text(string='Description')
    unit_value = fields.Float(string='Unit Value', required=True)

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.uom_id = self.product_id.uom_id

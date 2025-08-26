from odoo import models, fields


class IrModel(models.Model):
    _inherit = 'ir.model'

    trahum_export = fields.Boolean(string='Trahum Export', default=False)


class IrModelFields(models.Model):
    _inherit = 'ir.model.fields'

    trahum_export = fields.Boolean(
        string='Trahum Export',
        related='model_id.trahum_export',
        store=True,
        readonly=True
    )
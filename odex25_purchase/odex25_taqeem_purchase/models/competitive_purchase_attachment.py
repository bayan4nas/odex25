from odoo import fields, models


class CompetitivePurchaseAttachment(models.Model):
    _name = "competitive.purchase.attachment"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "competitive.purchase.attachment"

    purchase_ids = fields.One2many('purchase.request', 'competitive_purchase_id')
    name = fields.Char(string='Application brochure Name')
    attachment_scop = fields.Binary(
        string='Application brochure', readonly=False, attachment=True, required=True)

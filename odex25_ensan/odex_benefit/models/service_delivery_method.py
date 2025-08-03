from odoo import fields, models


class ServiceDeliveryMethod(models.Model):
    _name = "service.delivery.method"
    name = fields.Char(string="Name", required=True)

    _sql_constraints = [
        ("name_unique", "unique(name)", "the name its take it"),
    ]
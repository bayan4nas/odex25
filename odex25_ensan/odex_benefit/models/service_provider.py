from odoo import fields, models


class ServiceProvider(models.Model):
    _name = "service.provider"
    _description = "Service Provider"
    name = fields.Char(string="Name", required=True)
    need_partner = fields.Boolean(string="Need Partner",default=False)

    _sql_constraints = [
        ("name_unique", "unique(name)", "the name its take it"),
    ]
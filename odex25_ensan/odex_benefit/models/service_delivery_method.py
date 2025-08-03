from odoo import fields, models


class ServiceDeliveryMethod(models.Model):
    _name = "service.delivery.method"
    _description = "طرق تسليم الخدمة"
    name = fields.Char(string="الاسم", required=True)

    _sql_constraints = [
        ("name_unique", "unique(name)", "الاسم موجود مسبقًا!"),
    ]
from odoo import fields, models



class ServiceNeedStatus(models.Model):
    _name = "service.need.status"
    _description = "حالات الاحتياج"
    name = fields.Char(string="الاسم", required=True)

    _sql_constraints = [
        ("name_unique", "unique(name)", "الاسم موجود مسبقًا!"),
    ]

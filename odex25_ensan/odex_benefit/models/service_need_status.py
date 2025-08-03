from odoo import fields, models



class ServiceNeedStatus(models.Model):
    _name = "service.need.status"
    _description = "service need"
    name = fields.Char(string="Name", required=True)

    _sql_constraints = [
        ("name_unique", "unique(name)", "the name its take it"),
    ]

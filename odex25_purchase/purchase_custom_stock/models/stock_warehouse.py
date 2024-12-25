from odoo import api, fields, models, _


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    manager_id=fields.Many2one("hr.employee",string="Warehouse Manager",domain="[('department_id', '=',department_id)]",)
    department_id=fields.Many2one("hr.department",string="Warehouse Branch")
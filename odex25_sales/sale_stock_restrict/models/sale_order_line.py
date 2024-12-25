# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2023-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Saneen K (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    """Inherits the sale order line for checking the quantities and for
     showing the available quantity """
    _inherit = 'sale.order.line'

    available_qty = fields.Float(string="Available Qty", readonly=1,
                                 help='Available Quantity', compute='_compute_available_qty', store=True)

    @api.depends('product_id', 'order_id.warehouse_id')
    def _compute_available_qty(self):
        """Function that check whether the product restriction is enabled
        and the update the corresponding quantities """
        product_restriction = self.env['ir.config_parameter'].sudo().get_param(
            'sale_stock_restrict.product_restriction')
        check_stock = self.env[
            'ir.config_parameter'].sudo().get_param(
            'sale_stock_restrict.check_stock')
        for line in self:
            if product_restriction and check_stock == 'on_hand_quantity':
                line.available_qty = self.product_id.with_context(
                    warehouse=line.order_id.warehouse_id.id).qty_available
            elif product_restriction and check_stock == 'forecast_quantity':
                line.available_qty = line.product_id.with_context(
                    warehouse=line.order_id.warehouse_id.id).virtual_available
            else:
                line.available_qty = line.product_id.qty_available
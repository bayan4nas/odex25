# -*- coding: utf-8 -*-
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _


class StockPicking(models.Model):
    _inherit = "stock.picking"

    user_changed_to_done = fields.Many2one('res.users', string="User Who Changed to Done")

    def write(self, vals):
        res = super(StockPicking, self).write(vals)
        if self.state == 'done' and not self.user_changed_to_done:
            self.user_changed_to_done = self.env.user.id

        return res


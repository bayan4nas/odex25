# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_fix_budget_moves(self):
        for m in self :
            m.with_context(tracking_disable=True).button_draft()
            m.with_context(tracking_disable=True).action_general_secretary()

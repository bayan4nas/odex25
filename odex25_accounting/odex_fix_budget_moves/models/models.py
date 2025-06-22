# -*- coding: utf-8 -*-

from odoo import models, fields, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_fix_budget_moves(self):
        for m in self :
            seq = m.name
            m.with_context(tracking_disable=True).button_draft()
            m.with_context(tracking_disable=True).action_general_secretary()
            m.with_context(tracking_disable=True).write({'name' : seq})

    def check_need_repost(self):
        for m in self:
            for line in m.line_ids:
                if line.check_need_repost():
                    return True
        return False

    def get_need_repost(self):
        moves = self.env['account.move'].search([('state', '=', 'posted')])
        need_repost_moves = moves.filtered(lambda m: m.check_need_repost())
        ids = need_repost_moves.ids
        if ids:
            return {
                'name': 'Need Repost Moves',
                'view_mode': 'tree,form',
                'res_model': 'account.move',
                'type': 'ir.actions.act_window',
                'domain': [('id', 'in', ids)],
            }
        else:
            return {
                'name': 'No Need Repost Moves',
                'type': 'ir.actions.act_window_close',
            }

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'
    
    def get_budget_post(self):
        post = self.env.get("account.budget.post").search([('account_ids', 'in', self.account_id.id)])
        if post:
            return post[0]
        return False
    
    def check_link_budget(self):
        budget_post_id = self.get_budget_post()
        if not budget_post_id:  
            return False
        budget_line = self.env.get("crossovered.budget.lines").search([('general_budget_id', '=', budget_post_id.id), ('analytic_account_id', '=', self.analytic_account_id.id)])
        if budget_line:
            return True
        return False
    
    def check_need_repost(self):
        if self.check_link_budget :
            res = self.env.get("account.analytic.line").search([('analytic_account_id', '=', self.analytic_account_id.id), ('account_id', '=', self.account_id.id)])
        if not res:
            return True
        return False
    

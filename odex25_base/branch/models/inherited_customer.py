# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class ResPartnerIn(models.Model):
    _inherit = 'res.partner'

    
    @api.model
    def default_get(self, default_fields):
        res = super(ResPartnerIn, self).default_get(default_fields)
        if self.env.user.branch_id:
            res.update({
                'branch_id' : self.env.user.branch_id.id or False
            })
        return res

    branch_id = fields.Many2one('res.branch', string="Branch")

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        user = self.env.user
        if user.has_group("branch.group_branch_user") and not user.has_group("branch.group_branch_user_manager"):
            allowed_branch_ids = set()
            if user.branch_id:
                allowed_branch_ids.add(user.branch_id.id)
            if user.branch_ids:
                allowed_branch_ids.update(user.branch_ids.ids)
            if allowed_branch_ids:
                args += ['|', ('branch_id', '=', False), ('branch_id', 'in', list(allowed_branch_ids))]
                return super(ResPartnerIn, self).search(args, offset=offset, limit=limit, order=order, count=count)
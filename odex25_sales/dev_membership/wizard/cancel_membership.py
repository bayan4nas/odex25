# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class MembershipRefues(models.TransientModel):
    _name = "membership.request.cancel.wizard"
    _description = "Membership refuse Reason wizard"



    reason_id = fields.Many2one('cancellation.reason',string='Cancel Membership Reason' ,required=True)
    request_id = fields.Many2one('dev.membership')
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user,)


    @api.model
    def default_get(self, fields):
        res = super(MembershipRefues, self).default_get(fields)
        active_ids = self.env.context.get('active_ids', [])
        active_model = self.env.context.get('active_model', [])
        if active_model == 'dev.membership':
            res.update({'request_id': active_ids[0] if active_ids else False})
        return res

    # def request_cancel_reason(self):
    #     for record in self:
    #         record.ensure_one()
    #         subject = _("Membership Cancelled")
    #         body = _('The Membership was Cancelled by %s for the following reason: %s ') % (
    #             self.env.user.name, record.reason_id.name)
    #
    #         if record.request_id:
    #             record.request_id.cancel_reasone = record.reason_id.name
    #
    #             record.request_id.message_post(body=body, subject=subject)
    #             record.request_id.make_activity_group()
    #     # end chatter
    #     return {'type': 'ir.actions.act_window_close'}


    def request_cancel_reason(self):
        request_id = self.env.context.get('active_id')
        for record in self:
            if record.request_id:
                record.request_id.cancel_reasone = record.reason_id.id
        # Assuming self.env.context contains the ID of the membership
        if request_id:
            
            membership = self.env['dev.membership'].browse(request_id)
            self.env['membership.cancellation.request'].create({
                'member_id': membership.partner_id.id,
                'membership_type_id': membership.product_id.id,
                'membership_id': membership.id,
                'cancel_reason': self.reason_id.id,
                'state': 'draft'
            })
        # return {'type': 'ir.actions.act_window_close'}
        return {
            'type': 'ir.actions.act_window',
            'name': 'Membership Cancellation Requests',
            'view_mode': 'tree,form',
            'res_model': 'membership.cancellation.request',
            'context': dict(self.env.context, create=False)
        }



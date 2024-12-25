# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, timedelta
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class EntityRefusedReasonWizard(models.TransientModel):
    _name = 'entity.refused.reason.wizard'

    _description = "Refused Reason Wizard"

    def _default_entity(self):
        return self._context.get('active_id')

    def _default_state(self):
        return self._context.get('state')

    entity_id = fields.Many2one("grant.benefit", string="Benefit", default=_default_entity)
    refused_reason = fields.Text(string='Refused Reason', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('first_refusal', 'First Refusal'),
        ('approve', 'Approved'),
        ('record_end_date', 'Record end date'),
        ('refused', 'Refused'),
        ('black_list', 'Black List'),
    ], string='state', default=_default_state)

    # @api.multi
    def create_action(self):
        """Throw pop up to write the refusal reason for entity"""
        partner_ids = []
        for rec in self:
            if rec.entity_id:
                # if rec.entity_id.state == 'draft':
                self.env['entity.refuse_reason'].sudo().create(
                    {
                        'name': rec.refused_reason,
                        'entity_id': rec.entity_id.id,
                        'user_id': self.env.uid
                    }
                )
                state = "first_refusal"
                subject = _('Benefit')
                state_label = dict(rec.fields_get(allfields=['state'])['state']['selection'])[state]
                body = ' '.join(
                    (_(u'The Benefit  '), rec.entity_id.name, _(u' State changed to '), state_label, u'.')).encode(
                    'utf-8')
                partner_ids += [(6, 0, rec.entity_id.message_follower_ids.ids)]
                message_vals = {
                    'subject': subject,
                    'body': body,
                    'partner_ids': partner_ids,
                }
                now = fields.datetime.now()
                first_refuse_date = datetime.strftime(now, '%Y-%m-%d')
                rec.entity_id.message_post(body=body, subject=subject, message_type='email')
                result = rec.entity_id.sudo().write({
                    "state": 'first_refusal',
                    "first_refusal_reason": rec.refused_reason,
                    "first_refuse_date": first_refuse_date,
                })
            # elif rec.entity_id.state == "first_refusal":
            #     self.env['entity.refuse_reason'].sudo().create(
            #         {
            #             'name': 'first_refusal',
            #             'entity_id': rec.entity_id.id,
            #             'user_id': self.env.uid
            #         }
            #     )
            #     subject = _('Benefit')
            #     state_label = dict(rec.fields_get(allfields=['state'])['state']['selection'])[rec.entity_id.state]
            #     body = ' '.join(
            #         (_(u'The Benefit '), rec.entity_id.name, _(u' State changed to '), state_label, u'.')).encode(
            #         'utf-8')
            #     partner_ids += [(6, 0, rec.entity_id.message_follower_ids.ids)]
            #     partner_ids += [(6, 0, rec.entity_id.partner_id.id)]
            #
            #     message_vals = {
            #         'subject': subject,
            #         'body': body,
            #         'partner_ids': partner_ids,
            #     }
            #     rec.entity_id.message_post(body=body, subject=subject, message_type='email')
            #     result = rec.entity_id.sudo().write({
            #         "state": rec.entity_id.state,
            #         "first_refusal_reason": rec.refused_reason,
            #         # "end_subscribe_date": rec.end_subscribe_date,
            #     })
        return {'type': 'ir.actions.act_window_close'}

    # @api.multi
    def final_refuse(self):
        """Throw pop up to write the refusal reason for entity"""
        partner_ids = []
        for rec in self:
            if rec.entity_id:
                state = "refused"
                user = self.env['res.users'].search([('partner_id', '=', rec.entity_id.partner_id.id)], limit=1)

                refuse_reason = self.env['entity.refuse_reason'].sudo().create(
                    {
                        'name': rec.refused_reason,
                        'entity_id': rec.entity_id.id,
                        'user_id': self.env.uid,
                    }
                )
                subject = _('Benefit')
                state_label = dict(rec.fields_get(allfields=['state'])['state']['selection'])[state]
                body = ' '.join(
                    (
                        _(u'The Benefit record '), rec.entity_id.name, _(u' State changed to '), state_label,
                        u'.')).encode(
                    'utf-8')
                partner_ids += [(6, 0, rec.entity_id.message_follower_ids.ids)]
                message_vals = {
                    'subject': subject,
                    'body': body,
                    'partner_ids': partner_ids,
                }
                rec.entity_id.message_post(body=body, subject=subject, message_type='email')
                # rec.entity_id.sudo().unlink()
                if user:
                    user.sudo().unlink()
                # rec.entity_id.partner_id.sudo().unlink()
                result = rec.entity_id.sudo().write({
                    "state": 'refused',
                    "final_refusal_reason": rec.refused_reason,
                })
                return result
                    # return {
                    #     'name': _(u'Benefit To Accept'),
                    #     'view_mode': 'tree,form',
                    #     'views': [(self.env.ref('odex_benefit.grant_benefit_tree').id, 'tree'),(self.env.ref('odex_benefit.grant_benefit_form').id, 'form')],
                    #     'res_model': 'grant.benefit',
                    #     'type': 'ir.actions.act_window',
                    #     'target': 'main',
                    # }

#

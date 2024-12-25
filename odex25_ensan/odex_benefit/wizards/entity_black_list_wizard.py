# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class GrantRefusedReasonWizard(models.TransientModel):
    _name = 'entity.black.list.wizard'

    _description = "Entity Black List Wizard"

    def _default_entity(self):
        return self._context.get('active_id')

    def _default_state(self):
        return self._context.get('state')

    entity_id = fields.Many2one("grant.benefit", string="Entity", default=_default_entity)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('first_refusal', 'First Refusal'),
        ('approve', 'Approved'),
        ('record_end_date', 'Record end date'),
        ('refused', 'Refused'),
        ('black_list', 'Black List'),
    ], string="State", default=_default_state)
    black_list_reason = fields.Text(string='Black List Reason', required=True)
    black_list_message = fields.Text(string='Black List Message')

    # @api.multi
    def create_action(self):
        """Throw pop up to write the black list reason for grant"""
        partner_ids = []
        for rec in self:
            if rec.entity_id:
                result = rec.entity_id.sudo().write({
                    "state": rec.state,
                    "black_list_reason": rec.black_list_reason,
                    "black_list_message": rec.black_list_message,
                })
                # grant_ids = self.env['grant.task'].search([('entity_id', '=', rec.entity_id.id)]).unlink()
                subject = _('Entity')
                state_label = dict(rec.fields_get(allfields=['state'])['state']['selection'])[rec.state]
                body = ' '.join(
                    (_(u'The Entity '), rec.entity_id.name, _(u' State changed to '), state_label, u'.')).encode(
                    'utf-8')
                partner_ids += [(6, 0, rec.entity_id.message_follower_ids.ids)]
                message_vals = {
                    'subject': subject,
                    'body': body,
                    'partner_ids': partner_ids,
                }
                rec.entity_id.message_post(body=body, subject=subject,
                                           message_type='email')
                user = self.env['res.users'].search([('partner_id', '=', rec.entity_id.partner_id.id)], limit=1)

                user.sudo().write({
                    'groups_id': [(3, self.env.ref('base.group_erp_manager', False).id),
                                  ],

                })
                rec.entity_id.send_black_list_email()

        return {'type': 'ir.actions.act_window_close'}

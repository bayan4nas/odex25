# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_partner_sponsor = fields.Boolean(compute='_check_if_partner_sponsor')

    def _check_if_partner_sponsor(self):
        """ Check if Partner is Sponsor """
        for rec in self:
            # user = self.env['res.users'].sudo().search([('partner_id', '=', rec.id)], limit=1)
            # if user and user.has_group('odex_takaful.takaful_group_user_sponsor'):
            sponsor = self.env['takaful.sponsor'].sudo().search([('partner_id', '=', rec.id)], limit=1) 

            if sponsor:
                rec.is_partner_sponsor = True
            else:
                rec.is_partner_sponsor = False

    # @api.multi
    def view_sponsorship_payment_action(self):
        """Enable The Sponsor To Pay Sponsorships Entries"""
        sponsor = self.env['takaful.sponsor'].sudo().search([('partner_id', '=', self.id)], limit=1) 
        sponsorship_id = self.env['takaful.sponsorship'].sudo().search([('sponsor_id', '=', sponsor.id), ('has_delay', '=', True)], limit=1) 
        
        context = dict(self.env.context or {})
        context['default_sponsor_id'] = sponsor.id or False
        context['default_sponsorship_id'] = sponsorship_id.id or False
        return {
            'name': _('Sponsorship Payment'),
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(self.env.ref(
                'odex_takaful.takaful_sponsorship_payment_tree').id, 'tree'),
                      (self.env.ref('odex_takaful.takaful_sponsorship_payment_form').id, 'form')],
            'type': 'ir.actions.act_window',
            'res_model': 'sponsorship.payment',
            'domain': "[('sponsor_id','=',%s)]" % (sponsor.id or False),
            'target': 'current',
            'context': context,
        }

    
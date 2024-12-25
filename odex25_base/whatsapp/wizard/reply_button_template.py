# Part of Odoo. See LICENSE file for full copyright and licensing details.

import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)


class WhatsAppComposer(models.TransientModel):
    _name = 'reply.button.template'
    _description = 'Reply Button Template Wizard'

    button_line_id = fields.Many2one('whatsapp.template.button', string='Button Line ID')
    template_id = fields.Many2one(string='Reply Template', comodel_name='whatsapp.template', required=True)

    def change_template(self):
        self.button_line_id.write({'reply_template_id': self.template_id.id})

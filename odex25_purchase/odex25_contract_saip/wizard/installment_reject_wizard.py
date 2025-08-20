# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.tools.misc import format_date, formatLang


class InstallmentRejectWizard(models.TransientModel):
    _name = 'installment.reject.wizard'
    _description = 'Installment Reject Wizard'

    reason = fields.Text(string='Reason', required=True)

    def set_to_not_invoiced(self):
        global message
        self.ensure_one()
        installment = self.env['line.contract.installment'].browse(self._context.get('active_id'))
        coc = self.env['line.contract.installment.coc'].search([('installment_id', '=', installment.id)])
        if coc:
            coc.sudo().unlink()
        installment.write({'state': 'coc','taxed_invoice':'taxed_invoice'})
        message = _("installment  return to COC: {}").format(self.reason)
        installment.message_post(body=message)

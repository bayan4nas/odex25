# -*- coding: utf-8 -*-
from odoo.exceptions import UserError, ValidationError
from odoo import api, fields, models, _


class RefuseReason(models.TransientModel):
    _inherit = "refuse.reason"

    def action_refuse(self):
        res = super(RefuseReason, self).action_refuse()
        if self.request_id:
            request_id = self.env['purchase.request'].search([('id', '=', self.request_id)])
            if any(request_id.asset_request_line_ids.filtered(lambda line: line.asset_id.status == 'assigned')):
                raise ValidationError(
                    _("You have assigned an asset. Please return it before refusing the request."))
            else:
                # for line in request_id.asset_request_line_ids:
                #     if line.asset_id:
                #         line.asset_id.status = 'available'
                request_id.asset_request_line_ids.unlink()
            return res

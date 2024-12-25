# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, _
from odoo.exceptions import ValidationError


class BaseModuleUninstall(models.TransientModel):
    _name = "base.module.uninstall"
    _inherit = "base.module.uninstall"

    def action_uninstall(self):
        if 'odoo_dynamic_workflow' in [m.name for m in self.module_ids]:
            if self.env['odoo.workflow'].with_context(active_test=False).search([]):
                raise ValidationError(
                    _("Kindly DELETE all workflow (Active/Archived) before uninstall Dynamic Workflow Builder module."))
        return super(BaseModuleUninstall, self).action_uninstall()

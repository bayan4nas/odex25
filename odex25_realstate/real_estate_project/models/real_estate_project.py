# -*- coding: utf-8 -*-

import base64
import re
from odoo import models, fields, api, exceptions, tools, _
from odoo.modules.module import get_module_resource


class Project(models.Model):
    _inherit = 'project.project'
    _description = "Project Property"

    def action_done(self):
        res = super(Project, self).action_done()
        if self.project_owner_type == 'company':
            self.env['internal.property'].create({'name': self.name})
        return res
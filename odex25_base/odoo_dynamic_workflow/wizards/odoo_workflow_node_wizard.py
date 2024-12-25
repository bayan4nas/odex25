# -*- coding: utf-8 -*-
##########################################################
###                 Disclaimer                         ###
##########################################################
### Lately, I started to get very busy after I         ###
### started my new position and I couldn't keep up     ###
### with clients demands & requests for customizations ###
### & upgrades, so I decided to publish this module    ###
### for community free of charge. Building on that,    ###
### I expect respect from whoever gets his/her hands   ###
### on my code, not to copy nor rebrand the module &   ###
### sell it under their names.                         ###
##########################################################

from odoo import fields, models, api, _


class OdooWorkflowChangeModelWizard(models.TransientModel):
    _name = 'odoo.workflow.node.wizard'
    _description = 'Alternative Node Wizard'

    workflow_id = fields.Many2one('odoo.workflow')
    node_id = fields.Many2one('odoo.workflow.node')
    alter_node_id = fields.Many2one('odoo.workflow.node')

    def btn_confirm(self):
        rec = self.env[self.node_id.model].search([('state', '=', self.node_id.node_name)])
        rec.write({'state': self.alter_node_id.node_name})
        self.node_id.active = False


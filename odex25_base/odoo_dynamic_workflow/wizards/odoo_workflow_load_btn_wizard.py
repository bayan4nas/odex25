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


class OdooWorkflowLoadBtnWizard(models.Model):
    _name = 'odoo.workflow.load.btn.wizard'
    _description = 'Workflow Load Button Wizard'

    button_ids = fields.Many2many('odoo.workflow.btn.wizard', string='Model Buttons')
    node_id = fields.Many2one('odoo.workflow.node', string='Node')
    model_id = fields.Many2one('ir.model', string='Model Ref.', related='node_id.model_id')

    def btn_load(self):
        PYTHON_CODE_TEMP = """# Available locals:
        #  - time, date, datetime, timedelta: Python libraries.
        #  - env: Odoo Environement.
        #  - model: Model of the record on which the action is triggered.
        #  - obj: Record on which the action is triggered if there is one, otherwise None.
        #  - user, Current user object.
        #  - workflow: Workflow engine.
        #  - syslog : syslog(message), function to log debug information to Odoo logging file or console.
        #  - warning: warning(message), Warning Exception to use with raise.
        # To return an action, assign: action = {...}

        """
        for wiz in self:
            for btn in wiz.button_ids:
                PYTHON_CODE = ""
                action_type = 'link'
                if btn.type == 'object':
                    action_type = 'code'
                    PYTHON_CODE = PYTHON_CODE_TEMP+'\naction = obj.'+btn.name+'()'
                elif btn.type == 'action':
                    action_obj = self.env['ir.actions.actions'].browse(int(btn.name))
                    action_type = action_obj.type == 'ir.actions.server' and 'action' or 'win_act'

                wiz.node_id.button_ids.create({
                    'name': btn.string,
                    'is_highlight': btn.is_highlight,
                    'has_icon':  btn.icon,
                    'icon': btn.icon,
                    'action_type': action_type,
                    'node_id': wiz.node_id.id,
                    'model': wiz.node_id.model,
                    'workflow_id': wiz.node_id.workflow_id.id,
                    'group_ids': btn.groups and [(6, 0, [self.env.ref(g).id for g in btn.groups.split(',')])],
                    'view_ids': [(4, btn.view_id)],
                    'code': PYTHON_CODE,
                    'server_action_id': action_type == 'action' and btn.name,
                    'win_act_id': action_type == 'win_act' and btn.name
                })
        return True


class OdooWorkflowBtnWizard(models.Model):
    _name = 'odoo.workflow.btn.wizard'
    _description = 'Workflow Button Wizard'
    _rec_name = 'string'

    string = fields.Char(string='Button String')
    name = fields.Char(string='Button Name')
    is_highlight = fields.Boolean(string='Is Highlighted')
    icon = fields.Char(string='Icon')
    type = fields.Char(string='Type')
    code = fields.Text(string='Python Code')
    groups = fields.Char(string='Groups')
    view_id = fields.Integer(string='Views')
    server_action_id = fields.Many2one('ir.actions.server', string='Server Action')
    win_act_id = fields.Many2one('ir.actions.act_window', string='Window Action')
    model_id = fields.Many2one('ir.model', string='Model Ref.')
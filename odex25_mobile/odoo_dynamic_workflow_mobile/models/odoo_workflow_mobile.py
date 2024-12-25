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

import json
import pprint
from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval as eval
from odoo.exceptions import ValidationError, UserError, Warning
from datetime import datetime, date, time, timedelta
from lxml import etree
import random
import string
import logging

_logger = logging.getLogger(__name__)

CONDITION_CODE_TEMP = """# Available locals:
#  - time, date, datetime, timedelta: Python libraries.
#  - env: Odoo Environement.
#  - model: Model of the record on which the action is triggered.
#  - obj: Record on which the action is triggered if there is one, otherwise None.
#  - user, Current user object.
#  - workflow: Workflow engine.
#  - syslog : syslog(message), function to log debug information to Odoo logging file or console.
#  - warning: warning(message), Warning Exception to use with raise.


result = True"""

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

MODEL_DOMAIN = """[
        ('state', '=', 'base'),
        ('transient', '=', False),
        '!',
        '|',
        '|',
        '|',
        '|',
        '|',
        '|',
        '|',
        ('model', '=ilike', 'res.%'),
        ('model', '=ilike', 'ir.%'),
        ('model', '=ilike', 'workflow.mobile%'),
        ('model', '=ilike', 'bus.%'),
        ('model', '=ilike', 'base.%'),
        ('model', '=ilike', 'base_%'),
        ('model', '=', 'base'),
        ('model', '=', '_unknown'),
    ]"""

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

class OdooWorkflow(models.Model):
    _name = 'workflow.mobile'
    _description = 'Workflow'
    
    @api.onchange('model_id')
    def get_domain(self):
        return {'domain': {'view_id': [('type', '=', 'form'), ('model', '=', self.model_id.model)]}}

    name = fields.Char(string='Name', help="Give workflow a name.",translate=True,)
    mobile_id = fields.Char(string='Mobile ID', help="Give workflow a name.")
    model_id = fields.Many2one('ir.model', string='Model', domain=MODEL_DOMAIN, help="Enter business model you would like to modify its workflow.")
    view_id = fields.Many2one('ir.ui.view', string='Views',help="Enter business View you would like to modify its workflow.")
    btn_ids = fields.One2many('workflow.mobile.node.button', 'workflow_id', string='BTN', )
    node_ids = fields.One2many('workflow.mobile.node', 'workflow_id', string='Nodes', domain=[('active','=',True)])
    deactived_node_ids = fields.One2many('workflow.mobile.node', 'workflow_id', string='Deactivated Nodes', domain=[('active','=',False)])
    active = fields.Boolean(default=True)
    model_state = fields.Char()
    model_state_default = fields.Char()
    statusbar_visible = fields.Boolean('statusbar_visible')

    _sql_constraints = [
        ('uniq_name', 'unique(name)', _("Workflow name must be unique.")),
        ('uniq_mobile_id_mobile_id', 'unique(mobile_id)', _("Workflow mobile id must be unique."))
    ]
    
    # @api.multi
    def unlink(self):
        for wkf in self:
            if wkf.active:
                raise ValidationError(_("""Sorry, You can not delete an active workflow, You should archive it first."""))
        return super(OdooWorkflow, self).unlink()

    def toggle_active(self):
        if not self.active:
            super(OdooWorkflow, self).toggle_active()
        else:
            custom_nodes = [node.node_name for node in self.node_ids if not node.code_node]
            rec = self.env[self.model_id.model].with_context(active_test=False).search([('state', 'in', custom_nodes)])
            if self.model_state and rec:
                raise ValidationError(_("Some customized nodes are used as record state."))
            else:
                super(OdooWorkflow, self).toggle_active()

    @api.constrains('node_ids','node_ids.workflow','node_ids.flow_start','node_ids.name','node_ids.node_name')
    def validate_nodes(self):
        # Objects
        wkf_node_obj = self.env['workflow.mobile.node']
        for rec in self:
            # Must have one flow start node
            res = rec.node_ids.search_count([
                ('workflow_id', '=', rec.id),
                ('flow_start', '=', True),
                ('active', '=', True),
            ])
            if res > 1:
                raise ValidationError(_("Workflow must have only one start node."))
            for node in rec.node_ids:
                res = wkf_node_obj.search_count([
                    ('id', '!=', node.id),
                    ('workflow_id', '=', rec.id),
                    ('name', '=', node.name),
                ])
                if res:
                    raise ValidationError(_("Node name '%s' must be unique in workflow."%(node.name,)))
            for node in rec.node_ids:
                res = wkf_node_obj.search_count([
                    ('id', '!=', node.id),
                    ('workflow_id', '=', rec.id),
                    ('node_name', '=', node.node_name),
                ])
                if res:
                    raise ValidationError(_("Node technical name '%s' must be unique in workflow."%(node.node_name,)))

    # @api.multi
    def _load_view_btn(self):
        btn_wiz = self.env['workflow.mobile.node.button']
        for rec in self if self.view_id else []:
            view = self.env[rec.model_id.model]._fields_view_get(rec.view_id.id)
            arch = etree.XML(view['arch'])
            ids = []
            for btn in arch.xpath("//form/header/button"):
                attr = btn.attrib                
                PYTHON_CODE = ""
                PYTHON_CODE_readonly_attrs = ""
                PYTHON_CODE_invisible_attrs = ""
                action_type = 'link'
                if attr.get('type') == 'object':
                    action_type = 'code'
                    PYTHON_CODE = PYTHON_CODE_TEMP+'\naction = obj.'+attr.get('name')+'()'
                    if attr.get('attrs'):
                        attrs = eval(attr.get('attrs'))
                        if attrs.get('readonly',[]) :
                            PYTHON_CODE_readonly_attrs = PYTHON_CODE_TEMP+'\naction = obj.search(%s)' %(attrs.get('readonly',[]))
                        if attrs.get('invisible',[]) :
                            PYTHON_CODE_invisible_attrs = PYTHON_CODE_TEMP+'\naction = obj.search(%s)'%(attrs.get('invisible',[]))
                elif attr.get('type') == 'action':
                    action_obj = self.env['ir.actions.actions'].browse(int(attr.get('name')))
                    action_type = action_obj.type == 'ir.actions.server' and 'action' or 'win_act'
                btn_dict = {
                    'name': attr.get('name'),
                    'string': attr.get('string'),
                    'is_highlight': attr.get('class') == 'oe_highlight',
                    'icon': attr.get('icon'),
                    'type': attr.get('type'),
                    'readonly_attrs':PYTHON_CODE_readonly_attrs,
                    'invisible_attrs':PYTHON_CODE_invisible_attrs,
                    'groups': attr.get('groups'),
                    'view_id': view.get('view_id'),
                    'model_id': rec.model_id.id,
                    'action_type': action_type,
                    'workflow_id': rec.id,
                    'group_ids': [(6, 0, [self.env.ref(g).id for g in attr.get('groups').replace(" ", "").split(',')])] if attr.get('groups',False) else False,
                    'code': PYTHON_CODE,
                }
                str_state =  attr.get('states',False)
                for node_name in str_state.split(',') if str_state else []:
                    node_id = rec.node_ids.filtered(lambda node : node.node_name == node_name)
                    btn_dict['node_id'] = node_id.id
                    id = btn_wiz.create(btn_dict)
                    ids.append(id.id)
            rec.write({'btn_ids':[(6,0,ids)]})  
            
            for field in arch.xpath("//form/header/field") :
                attr_field = field.attrib
                statusbar_visible = attr_field.get('statusbar_visible',False)
                index = 0
                for node_name in statusbar_visible.split(',') if statusbar_visible else []:
                    node_id = rec.node_ids.filtered(lambda node : node.node_name == node_name)
                    if node_id :
                        rec.statusbar_visible = True
                        index = index + 1
                        node_id.sequence_in_hdr = index
  
                
    # @api.multi
    def btn_load_nodes(self):
        # Variables
        for rec in self:
            model = self.env[rec.model_id.model]
            max_seq = max([0]+[n.sequence for n in self.node_ids])
            if 'state' in model._fields:
                nodes = model._fields.get('state')._description_selection(self.env)
                flow_start = model.default_get(['state'])['state'] if model.default_get(['state']) else ''
                current_nodes = []
                has_start = False
                for n in rec.with_context( active_test=False).node_ids:
                    current_nodes.append(n.node_name)
                    if n.flow_start:
                        has_start = True
                for node in nodes:
                    max_seq += 1
                    if node[0] not in current_nodes:
                        rec.node_ids.create({
                            'node_name': node[0],
                            'name': node[1],
                            'flow_start': node[0] == flow_start and not has_start,
                            'workflow_id': rec.id,
                            'sequence': max_seq,
                            'code_node': True,
                            'view_ids': [(6, 0, [rec.view_id.id])],
                        })
                rec._load_view_btn()
                
    def firebase_notification(self):
        super(OdooWorkflow,self).firebase_notification()
        
    # @api.multi
    def btn_nodes(self):
        for rec in self:
            rec.firebase_notification()
            act = {
                'name': _('Nodes'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'view_id': False,
                'res_model': 'workflow.mobile.node',
                'domain': [('workflow_id', '=', rec.id),('view_ids','=',rec.view_id.id)],
                'context': {'default_workflow_id': rec.id},
                'type': 'ir.actions.act_window',
            }
            return act

    # @api.multi
    def btn_buttons(self):
        for rec in self:
            act = {
                'name': _('Buttons'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'view_id': False,
                'res_model': 'workflow.mobile.node.button',
                'domain': [('workflow_id', '=', rec.id)],
                'type': 'ir.actions.act_window',
            }
            return act

    @api.onchange('model_id','view_id')
    def onchange_model(self):
        if self.model_id:
            model = self.env[self.model_id.model]
            if 'state' in model._fields:
                states = model._fields.get('state')._description_selection(self.env)
                self.model_state = ','.join([i for t in states for i in t])
                self.model_state_default = model.default_get(['state'])['state'] if model.default_get(['state']) else ''
            else:
                self.model_state = ""
                self.model_state_default = ""
        else:
            self.model_state = ""
            self.model_state_default = ""


class OdooWorkflowNode(models.Model):
    _name = 'workflow.mobile.node'
    _description = 'Workflow Nodes'
    _order = 'sequence'

    name = fields.Char(string='Name', translate=True, help="Enter string name of the node.")
    node_name = fields.Char(string='Technical Name', help="Generated technical name which used by backend code.",readonly=True)
    sequence = fields.Integer(string='Sequence', default=100000, help="Arrange node by defining sequence.",readonly=True)
    sequence_in_hdr = fields.Integer(string='Sequence', default=100000, help="Arrange node by defining sequence.",readonly=True)
    flow_start = fields.Boolean(string='Flow Start', help="Check it if this node is the starting node.",readonly=True)
    flow_end = fields.Boolean(string='Flow End', help="Check it if this node is the ending node.",readonly=True)
    is_visible = fields.Boolean(string='Appear in Statusbar', default=True, help="Control visiability of the node/state in view.",readonly=True)
    button_ids = fields.One2many('workflow.mobile.node.button', 'node_id', string='Buttons',readonly=True)
    workflow_id = fields.Many2one('workflow.mobile', string='Workflow Ref.', ondelete='cascade',readonly=True)
    model_id = fields.Many2one('ir.model', string='Model Ref.', domain="[('state','=','base')]", related='workflow_id.model_id',readonly=True)
    model = fields.Char(string='Model', related='model_id.model',readonly=True)
    view_ids = fields.Many2many('ir.ui.view', string='Views', required=True,readonly=True)
    active = fields.Boolean(default=True,readonly=True)
    code_node = fields.Boolean(string='Loaded from Code',readonly=True)
    pre_active = fields.Boolean(default=True,readonly=True)

    def toggle_pre_active(self):
        if self.pre_active:
            if self.in_link_ids or self.out_link_ids:
                raise ValidationError(_("""Node with an outgoing/ingoing links can not archived"""))
            rec = self.env[self.model].with_context(active_test=False).search([('state', '=', self.node_name)])
            if rec:
                return {
                    'name': _('Alternative Node'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'workflow.mobile.node.wizard',
                    'target': 'new',
                    'context': {
                        'default_node_id': self.id,
                        'default_workflow_id': self.workflow_id.id,
                    },
                }
        self.pre_active = not self.pre_active


    # @api.multi
    def unlink(self):
        for node in self:
            if node.code_node:
                raise ValidationError(_("""Sorry, You can not delete nodes that loaded from code.
                                           Deactivate it if don't need it any more"""))
        return super(OdooWorkflowNode, self).unlink()

    # @api.multi
    def btn_load_fields(self):
        # Variables
        field_obj = self.env['ir.model.fields']
        for rec in self:
            # Clear Fields List
            rec.field_ids.unlink()
            # Load Fields
            fields = field_obj.search([('model_id', '=', rec.model_id.id)])
            for field in fields:
                rec.field_ids.create({
                    'model_id': rec.model_id.id,
                    'node_id': rec.id,
                    'name': field.id,
                })


class OdooWorkflowBtnWizard(models.Model):
    _name = 'workflow.mobile.node.button'
    _description = 'Workflow Button Wizard'
    _rec_name = 'string'
    _order = 'sequence'

    def _generate_key(self):
        return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(10))

    string = fields.Char(string='Button String' ,translate=True,)
    type = fields.Char(string='Type',readonly=True)
    groups = fields.Char(string='Groups',readonly=True)
    view_id = fields.Many2one('ir.ui.view', string='Views',readonly=True)
    model_id = fields.Many2one('ir.model', string='Model Ref.',readonly=True)
    name = fields.Char(string='Button Name', translate=True, help="Enter button string name that will appear in the view.",readonly=True)
    sequence = fields.Integer(string='Sequence', default=10, help="Arrange buttons by defining sequence.",readonly=True)
    is_highlight = fields.Boolean(string='Is Highlighted', default=True, help="Control highlighting of the button if needs user attention..",readonly=True)
    has_icon = fields.Boolean(string='Has Icon', help="Enable it to add icon to the button.",readonly=True)
    icon = fields.Char(string='Icon', help="Enter icon name like: fa-print, it's recommended to use FontAwesome Icons.",readonly=True)
    btn_key = fields.Char(string='Button Key', default=_generate_key,readonly=True)
    btn_hide = fields.Boolean(string="Hide Button if Condition isn't fulfilled", help="If condition is false the button will be hidden.",readonly=True)
    condition_code = fields.Text(string='Condition Code', default=CONDITION_CODE_TEMP, help="Enter condition to execute button action.",readonly=True)
    send_manager = fields.Boolean(string="Send Direct Manager", help="Send Direct Manager")
    is_refuse= fields.Boolean(string="Send Refuse", help="Send Refuse")
    action_type = fields.Selection([
        ('link', 'Trigger Link'),
        ('code', 'Python Code'),
        ('action', 'Server Action'),
        ('win_act', 'Window Action'),
    ], string='Action Type', default='code', help="Choose type of action to be trigger by the button.",readonly=True)
    code = fields.Text(string='Python Code', default=PYTHON_CODE_TEMP,readonly=True)
    readonly_attrs = fields.Text(string='Python readonly_attrs', default=PYTHON_CODE_TEMP,readonly=True)
    invisible_attrs = fields.Text(string='Python invisible_attrs', default=PYTHON_CODE_TEMP,readonly=True)
    server_action_id = fields.Many2one('ir.actions.server', string='Server Action',readonly=True)
    win_act_id = fields.Many2one('ir.actions.act_window', string='Window Action',readonly=True)
    node_id = fields.Many2one('workflow.mobile.node', string='Workflow Node Ref.', ondelete='cascade',readonly=True)
    workflow_id = fields.Many2one('workflow.mobile',  ondelete='cascade', related='node_id.workflow_id',store=True, string='Workflow Ref.',readonly=True)
    view_ids = fields.Many2many('ir.ui.view', string='Views', required=True,readonly=True)
    group_ids = fields.Many2many('res.groups', string='Groups',readonly=True)
    model = fields.Char(string='Model', related='node_id.model',readonly=True)

    @api.onchange('node_id')
    def change_workflow(self):
        for rec in self:
            if isinstance(rec.id, int) and rec.node_id and rec.node_id.workflow_id:
                rec.workflow_id = rec.node_id.workflow_id.id
            elif self.env.context.get('default_node_id', 0):
                model_id = self.env['workflow.mobile.node'].sudo().browse(self.env.context.get('default_node_id')).model_id.id
                rec.workflow_id = self.env['workflow.mobile'].sudo().search([('model_id', '=', model_id)])

    @api.constrains('btn_key')
    def validation(self):
        for rec in self:
            # Check if there is no duplicate button key
            res = self.search_count([
                ('id', '!=', rec.id),
                ('btn_key', '=', rec.btn_key),
            ])
            if res:
                rec.btn_key = self._generate_key()

    # @api.multi
    def run(self):
        for rec in self:
            # Check Condition Before Executing Action
            result = False
            cx = self.env.context.copy() or {}
            locals_dict = {
                'env': self.env,
                'model': self.env[cx.get('active_model', False)],
                'obj': self.env[cx.get('active_model', False)].browse(cx.get('active_id', 0)),
                'user': self.env.user,
                'datetime': datetime,
                'time': time,
                'date': date,
                'timedelta': timedelta,
                'workflow': self.env['workflow.mobile'],
                'warning': self.warning,
                'syslog': self.syslog,
            }
            try:
                eval(rec.condition_code, locals_dict=locals_dict, mode='exec', nocopy=True)
                result = 'result' in locals_dict and locals_dict['result'] or False
            except ValidationError as ex:
                raise ex
            except SyntaxError as ex:
                raise UserError(_("Wrong python code defined.\n\nError: %s\nLine: %s, Column: %s\n\n%s" % (
                ex.args[0], ex.args[1][1], ex.args[1][2], ex.args[1][3])))
            if result:
                # Run Proper Action
                func = getattr(self, "_run_%s" % rec.action_type)
                return func()

    # @api.multi
    def _run_win_act(self):
        # Variables
        cx = self.env.context.copy() or {}
        win_act_obj = self.env['ir.actions.act_window']
        # Run Window Action
        for rec in self:
            action = win_act_obj.with_context(cx).browse(rec.win_act_id.id).read()[0]
            action['context'] = cx
            return action
        return False

    # @api.multi
    def _run_action(self):
        # Variables
        srv_act_obj = self.env['ir.actions.server']
        # Run Server Action
        for rec in self:
            srv_act_rec = srv_act_obj.browse(rec.server_action_id.id)
            return srv_act_rec.run()

    # @api.multi
    def _run_readonly_attrs(self):
        # Variables

        for rec in self:
            if not rec.readonly_attrs:
                return False
            cx = self.env.context.copy() or {}
            obj = rec.env[cx.get('active_model', False)].browse(cx.get('active_id', 0))
            locals_dict = {
                'env': rec.env,
                'model': rec.env[cx.get('active_model', False)],
                'obj': obj,
                'user': rec.env.user,
                'datetime': datetime,
                'time': time,
                'date': date,
                'timedelta': timedelta,
                'workflow': rec.env['workflow.mobile'],
                'warning': rec.warning,
                'syslog': rec.syslog,
            }
        # Run readonly_attrs
            try:
                eval(rec.readonly_attrs, locals_dict=locals_dict, mode='exec', nocopy=True)
                action = 'action' in locals_dict and locals_dict['action'] or False
                if action:
                    return obj in action
            except Warning as ex:
                raise ex
            except SyntaxError as ex:
                raise UserError(_("Wrong python readonly_attrs defined.\n\nError: %s\nLine: %s, Column: %s\n\n%s" % (ex.args[0], ex.args[1][1], ex.args[1][2], ex.args[1][3])))
        return True
    
    # @api.multi
    def _run_invisible_attrs(self):
        # Variables

        # Run invisible_attrs
        for rec in self:
            if not rec.invisible_attrs:
                return True
            cx = self.env.context.copy() or {}
            obj = rec.env[cx.get('active_model', False)].browse(cx.get('active_id', 0))
            locals_dict = {
                'env': rec.env,
                'model': rec.env[cx.get('active_model', False)],
                'obj':obj,
                'user': rec.env.user,
                'datetime': datetime,
                'time': time,
                'date': date,
                'timedelta': timedelta,
                'workflow': rec.env['workflow.mobile'],
                'warning': rec.warning,
                'syslog': rec.syslog,
            }
            try:
                eval(rec.invisible_attrs, locals_dict=locals_dict, mode='exec', nocopy=True)
                action = 'action' in locals_dict and locals_dict['action'] or False
                if action:
                    
                    return obj in action
            except Warning as ex:
                raise ex
            except SyntaxError as ex:
                raise UserError(_("Wrong python readonly_attrs defined.\n\nError: %s\nLine: %s, Column: %s\n\n%s" % (ex.args[0], ex.args[1][1], ex.args[1][2], ex.args[1][3])))
        return True
   
    # @api.multi
    def _run_code(self,active_id=None , model=None ,env=None):
        # Variables
        cx = self.env.context.copy() or {}
        locals_dict = {
            'env': env or self.env,
            'model': self.env[cx.get('active_model', False) or model] ,
            'obj': self.env[cx.get('active_model', False) or model].browse(int(cx.get('active_id', 0) or active_id)) ,
            'user': env.user or  self.env.user,
            'datetime': datetime,
            'time': time,
            'date': date,
            'timedelta': timedelta,
            'workflow': self.env['workflow.mobile'],
            'warning': self.warning,
            'syslog': self.syslog,
        }
        # Run Code
        for rec in self:
            try:
                eval(rec.code, locals_dict=locals_dict, mode='exec', nocopy=True)
                action = 'action' in locals_dict and locals_dict['action'] or False
                if action:
                    return action
            except Warning as ex:
                raise ex
            except SyntaxError as ex:
                raise UserError(_("Wrong python code defined.\n\nError: %s\nLine: %s, Column: %s\n\n%s" % (ex.args[0], ex.args[1][1], ex.args[1][2], ex.args[1][3])))
        
        return True
    
    # @api.multi
    def _run_link(self):
        for rec in self:
            # Check Condition Before Executing Action
            result = False
            cx = self.env.context.copy() or {}
            locals_dict = {
                'env': self.env,
                'model': self.env[cx.get('active_model', False)],
                'obj': self.env[cx.get('active_model', False)].browse(cx.get('active_id', 0)),
                'user': self.env.user,
                'datetime': datetime,
                'time': time,
                'date': date,
                'timedelta': timedelta,
                'workflow': self.env['workflow.mobile'],
                'warning': self.warning,
                'syslog': self.syslog,
            }
            try:
                eval(rec.link_id.condition_code, locals_dict=locals_dict, mode='exec', nocopy=True)
                result = 'result' in locals_dict and locals_dict['result'] or False
            except ValidationError as ex:
                raise ex
            except SyntaxError as ex:
                raise UserError(_("Wrong python code defined.\n\nError: %s\nLine: %s, Column: %s\n\n%s" % (
                ex.args[0], ex.args[1][1], ex.args[1][2], ex.args[1][3])))
            if result:
                # Trigger link function
                return rec.link_id.trigger_link()

    def warning(self, msg):
        if not isinstance(msg, str):
            msg = str(msg)
        raise Warning(msg)

    def syslog(self, msg):
        if not isinstance(msg, str):
            msg = str(msg)
        _logger.info(msg)


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
        ('model', '=ilike', 'odoo.workflow%'),
        ('model', '=ilike', 'bus.%'),
        ('model', '=ilike', 'base.%'),
        ('model', '=ilike', 'base_%'),
        ('model', '=', 'base'),
        ('model', '=', '_unknown'),
    ]"""


class OdooWorkflow(models.Model):
    _name = 'odoo.workflow'
    _description = 'Odoo Workflow'

    name = fields.Char(string='Name', help="Give workflow a name.")
    model_id = fields.Many2one('ir.model', string='Model', domain=MODEL_DOMAIN,
                               help="Enter business model you would like to modify its workflow.")
    node_ids = fields.One2many('odoo.workflow.node', 'workflow_id', string='Nodes', domain=[('active','=',True)])
    deactived_node_ids = fields.One2many('odoo.workflow.node', 'workflow_id', string='Deactivated Nodes',
                                        domain=[('active','=',False)])
    remove_default_attrs_mod = fields.Boolean(string='Remove Default Attributes & Modifiers',
                                              help="""This option will remove default attributes set on 
                                                      fields & buttons of current model view in order to customized 
                                                      all attributes depending on your needs\n
                                                      Attributes like: [required, readonly, invisible].""")
    remove_default_header = fields.Boolean(string='Remove Default Views Header', default=True,
                                           help="""This option will remove default header from current model view 
                                                    in order to customized all Buttons depending on your needs.""")
    mail_thread_add = fields.Boolean(string='Add Mailthread/Messaging to Model', help="Add Mailthread area to model.")
    activities_add = fields.Boolean(string='Add Activities to Model', help="Enable Activities in Mailthread")
    followers_add = fields.Boolean(string='Add Followers to Model', help="Enable Followers in Mailthread")
    active = fields.Boolean(default=True)
    model_state = fields.Char()
    model_state_default = fields.Char()

    _sql_constraints = [
        ('uniq_name', 'unique(name)', _("Workflow name must be unique.")),
        ('uniq_model', 'unique(model_id)', _("Model must be unique.")),
    ]

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
        wkf_node_obj = self.env['odoo.workflow.node']
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

    def _load_view_btn(self):
        btn_wiz = self.env['odoo.workflow.btn.wizard']
        #btn_wiz.search([]).unlink()
        for rec in self:
            view = self.env[rec.model_id.model].fields_view_get()
            arch = etree.XML(view['arch'])
            for btn in arch.xpath("//form/header/button"):
                attr = btn.attrib
                if attr.get('custom_btn') or btn_wiz.search([('name', '=', attr.get('name')),
                                                             ('string', '=', attr.get('string')),
                                                             ('model_id', '=', rec.model_id.id)]):
                    continue
                btn_dict = {
                    'name': attr.get('name'),
                    'string': attr.get('string'),
                    'is_highlight': attr.get('class') == 'oe_highlight',
                    'icon': attr.get('icon'),
                    'type': attr.get('type'),
                    'groups': attr.get('groups'),
                    'view_id': view.get('view_id'),
                    'model_id': rec.model_id.id,
                }
                btn_wiz.create(btn_dict)

    def btn_load_nodes(self):
        # Variables
        for rec in self:
            model = self.env[rec.model_id.model]
            views = self.env['ir.ui.view'].search([('type', '=', 'form'), ('model', '=', rec.model_id.model)])

            max_seq = max([0]+[n.sequence for n in self.node_ids])
            if 'state' in model._fields:
                nodes = model._fields.get('state')._description_selection(self.env)
                flow_start = model.default_get(['state'])['state']
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
                            'view_ids': [(6, 0, [v.id for v in views])],
                        })

    def btn_reload_workflow(self):
        from odoo.addons import odoo_dynamic_workflow
        return odoo_dynamic_workflow.update_workflow_reload(self)

    def btn_nodes(self):
        for rec in self:
            act = {
                'name': _('Nodes'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'view_id': False,
                'res_model': 'odoo.workflow.node',
                'domain': [('workflow_id', '=', rec.id)],
                'context': {'default_workflow_id': rec.id},
                'type': 'ir.actions.act_window',
            }
            return act

    def btn_buttons(self):
        for rec in self:
            act = {
                'name': _('Buttons'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'view_id': False,
                'res_model': 'odoo.workflow.node.button',
                'domain': [('workflow_id', '=', rec.id)],
                'context': {'default_workflow_id': rec.id},
                'type': 'ir.actions.act_window',
            }
            return act

    def btn_links(self):
        for rec in self:
            act = {
                'name': _('Links'),
                'view_type': 'form',
                'view_mode': 'tree,form',
                'view_id': False,
                'res_model': 'odoo.workflow.link',
                'domain': [
                    '|',
                    ('node_from.workflow_id', '=', rec.id),
                    ('node_to.workflow_id', '=', rec.id),
                ],
                'context': {},
                'type': 'ir.actions.act_window',
            }
            return act

    @api.onchange('model_id')
    def onchange_model(self):
        if self.node_ids:
            raise ValidationError(_("Sorry, You can not change the model while workflow has an active nodes, deactivate nodes first."))
        if self.model_id:
            model = self.env[self.model_id.model]
            if 'state' in model._fields:
                states = model._fields.get('state')._description_selection(self.env)
                self.model_state = ','.join([i for t in states for i in t])
                self.model_state_default = model.default_get(['state'])['state']
            else:
                self.model_state = ""
                self.model_state_default = ""
            self._load_view_btn()
        else:
            self.model_state = ""
            self.model_state_default = ""


class OdooWorkflowNode(models.Model):
    _name = 'odoo.workflow.node'
    _description = 'Odoo Workflow Nodes'
    _order = 'sequence'

    name = fields.Char(string='Name', translate=True, help="Enter string name of the node.")
    node_name = fields.Char(string='Technical Name', help="Generated technical name which used by backend code.")
    sequence = fields.Integer(string='Sequence', default=10, help="Arrange node by defining sequence.")
    flow_start = fields.Boolean(string='Flow Start', help="Check it if this node is the starting node.")
    flow_end = fields.Boolean(string='Flow End', help="Check it if this node is the ending node.")
    is_visible = fields.Boolean(string='Appear in Statusbar', default=True, help="Control visiability of the node/state in view.")
    out_link_ids = fields.One2many('odoo.workflow.link', 'node_from', string='Outgoing Transitions')
    in_link_ids = fields.One2many('odoo.workflow.link', 'node_to', string='Incoming Transitions')
    field_ids = fields.One2many('odoo.workflow.node.field', 'node_id', string='Fields')
    button_ids = fields.One2many('odoo.workflow.node.button', 'node_id', string='Buttons')
    workflow_id = fields.Many2one('odoo.workflow', string='Workflow Ref.', ondelete='cascade')
    model_id = fields.Many2one('ir.model', string='Model Ref.', domain="[('state','=','base')]", related='workflow_id.model_id')
    model = fields.Char(string='Model', related='model_id.model')
    view_ids = fields.Many2many('ir.ui.view', string='Views', required=True)
    active = fields.Boolean(default=True)
    code_node = fields.Boolean(string='Loaded from Code')
    pre_active = fields.Boolean(default=True)

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
                    'res_model': 'odoo.workflow.node.wizard',
                    'target': 'new',
                    'context': {
                        'default_node_id': self.id,
                        'default_workflow_id': self.workflow_id.id,
                    },
                }
        self.pre_active = not self.pre_active

    @api.onchange('model')
    def onchange_model(self):
        views = self.env['ir.ui.view'].search([('type', '=', 'form'), ('model', '=', self.model)])
        return {'value':{'view_ids': [(6, 0, [v.id for v in views])]}}

    def unlink(self):
        for node in self:
            if node.code_node:
                raise ValidationError(_("""Sorry, You can not delete nodes that loaded from code.
                                           Deactivate it if don't need it any more"""))
        return super(OdooWorkflowNode, self).unlink()

    #@api.onchange('name')
    def _compute_node_name(self):
        for rec in self:
            if rec and rec.name:
                name = rec.name.lower().strip().replace(' ', '_')
                rec.node_name = name

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

    def btn_load_btns(self):
        return {
            'name': _('Model Buttons'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'odoo.workflow.load.btn.wizard',
            'target': 'new',
            'context': {
                'default_node_id': self.id,
            },
        }


class OdooWorkflowLink(models.Model):
    _name = 'odoo.workflow.link'
    _description = 'Odoo Workflow Links'

    name = fields.Char(string='Name', help="Enter friendly link name that describe the process.")
    condition_code = fields.Text(string='Condition Code', default=CONDITION_CODE_TEMP, help="Enter condition to pass thru this link.")
    workflow_id = fields.Many2one('odoo.workflow', ondelete='cascade', required=True)
    node_from = fields.Many2one('odoo.workflow.node', 'Source Node', domain="[('workflow_id','=',workflow_id)]",
                                ondelete='cascade', required=True)
    node_to = fields.Many2one('odoo.workflow.node', 'Destination Node', domain="[('workflow_id','=',workflow_id)]",
                              ondelete='cascade', required=True)

    @api.constrains('node_from', 'node_to')
    def check_nodes(self):
        for rec in self:
            if rec.node_from == rec.node_to:
                raise ValidationError(_("Sorry, source & destination nodes can't be the same."))

    @api.onchange('node_from', 'node_to')
    def onchange_nodes(self):
        for rec in self:
            if rec.node_from and rec.node_to:
                rec.name = "%s -> %s" % (rec.node_from.name, rec.node_to.name)

    def trigger_link(self):
        # Variables
        cx = self.env.context
        model_name = cx.get('active_model')
        rec_id = cx.get('active_id')
        model_obj = self.env[model_name]
        rec = model_obj.browse(rec_id)
        # Validation
        if rec.state == self.node_from.node_name:
            rec.state = self.node_to.node_name
        return True

    def unlink(self):
        if self.env['odoo.workflow.node.button'].search([('link_id', 'in', self.ids)]):
            raise ValidationError(_("You can not delete link that already used in node button."))
        return super(OdooWorkflowLink, self).unlink()


class OdooWorkflowNodeButton(models.Model):
    _name = 'odoo.workflow.node.button'
    _description = 'Odoo Workflow Node Buttons'
    _order = 'sequence'

    def _generate_key(self):
        return ''.join(random.SystemRandom().choice(string.ascii_uppercase + string.digits) for _ in range(10))

    name = fields.Char(string='Button String', translate=True, help="Enter button string name that will appear in the view.")
    sequence = fields.Integer(string='Sequence', default=10, help="Arrange buttons by defining sequence.")
    is_highlight = fields.Boolean(string='Is Highlighted', default=True, help="Control highlighting of the button if needs user attention..")
    has_icon = fields.Boolean(string='Has Icon', help="Enable it to add icon to the button.")
    icon = fields.Char(string='Icon', help="Enter icon name like: fa-print, it's recommended to use FontAwesome Icons.")
    btn_key = fields.Char(string='Button Key', default=_generate_key)
    btn_hide = fields.Boolean(string="Hide Button if Condition isn't fulfilled", help="If condition is false the button will be hidden.")
    condition_code = fields.Text(string='Condition Code', default=CONDITION_CODE_TEMP, help="Enter condition to execute button action.")
    action_type = fields.Selection([
        ('link', 'Trigger Link'),
        ('code', 'Python Code'),
        ('action', 'Server Action'),
        ('win_act', 'Window Action'),
    ], string='Action Type', default='code', help="Choose type of action to be trigger by the button.")
    link_id = fields.Many2one('odoo.workflow.link', string='Link')
    code = fields.Text(string='Python Code', default=PYTHON_CODE_TEMP)
    server_action_id = fields.Many2one('ir.actions.server', string='Server Action')
    win_act_id = fields.Many2one('ir.actions.act_window', string='Window Action')
    node_id = fields.Many2one('odoo.workflow.node', string='Workflow Node Ref.', ondelete='cascade')
    workflow_id = fields.Many2one('odoo.workflow',  ondelete='cascade', related='node_id.workflow_id', string='Workflow Ref.')
    view_ids = fields.Many2many('ir.ui.view', string='Views', required=True)
    group_ids = fields.Many2many('res.groups', string='Groups')
    model = fields.Char(string='Model', related='node_id.model')

    @api.onchange('model')
    def onchange_model(self):
        views = self.env['ir.ui.view'].search([('type', '=', 'form'), ('model', '=', self.model)])
        return {'value': {'view_ids': [(6, 0, [v.id for v in views])]}}

    @api.onchange('node_id')
    def change_workflow(self):
        for rec in self:
            if isinstance(rec.id, int) and rec.node_id and rec.node_id.workflow_id:
                rec.workflow_id = rec.node_id.workflow_id.id
            elif self.env.context.get('default_node_id', 0):
                model_id = self.env['odoo.workflow.node'].sudo().browse(self.env.context.get('default_node_id')).model_id.id
                rec.workflow_id = self.env['odoo.workflow'].sudo().search([('model_id', '=', model_id)])

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
                'workflow': self.env['odoo.workflow'],
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

    def _run_action(self):
        # Variables
        srv_act_obj = self.env['ir.actions.server']
        # Run Server Action
        for rec in self:
            srv_act_rec = srv_act_obj.browse(rec.server_action_id.id)
            return srv_act_rec.run()

    def _run_code(self):
        # Variables
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
            'workflow': self.env['odoo.workflow'],
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
                'workflow': self.env['odoo.workflow'],
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


class OdooWorkflowNodeField(models.Model):
    _name = 'odoo.workflow.node.field'
    _description = 'Odoo Workflow Node Fields'

    name = fields.Many2one('ir.model.fields', string='Field')
    model_id = fields.Many2one('ir.model', string='Model', domain="[('state','=','base')]")
    readonly = fields.Boolean(string='Readonly')
    required = fields.Boolean(string='Required')
    invisible = fields.Boolean(string='Invisible')
    group_ids = fields.Many2many('res.groups', string='Groups')
    user_ids = fields.Many2many('res.users', string='Users')
    node_id = fields.Many2one('odoo.workflow.node', string='Node Ref.', ondelete='cascade', required=True)

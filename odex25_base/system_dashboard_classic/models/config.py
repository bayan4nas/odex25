from odoo import fields, models, api,_
from odoo.exceptions import  ValidationError

class BaseDashboard(models.Model):
    _name = 'base.dashbord'
    _description = 'Base Dashboard'
    _order = 'sequence'

    sequence = fields.Integer()

    rec_name ="model_id "

   
    name = fields.Char(
        string='Card name', translate=True
    )
    

    model_name = fields.Char(
        string='model name',
    )

    model_id = fields.Many2one(string='Model', comodel_name='ir.model',)

    line_ids = fields.One2many(
        string='Line',
        comodel_name='base.dashbord.line',
        inverse_name='board_id'
    )

    
    card_image = fields.Binary(
        string='Card Image',
    )
    
    is_self_service = fields.Boolean(
        string='Self Service?',
    )

    form_view_id = fields.Many2one('ir.ui.view', string='Form View', )
    list_view_id = fields.Many2one('ir.ui.view', string='List View',)
    action_id = fields.Many2one('ir.actions.act_window', string='Action',)
    field_id = fields.Many2one('ir.model.fields', string='Fields',)
                             
   
    is_button = fields.Boolean(
        string='is_button',
    )

    is_stage = fields.Boolean(
        string='is_stage',compute='_compute_field',store = True
    )

    is_double = fields.Boolean(
        string='is_double',compute='_compute_field' ,store = True
    )
    is_state = fields.Boolean(
        string='is_state',compute='_compute_field' ,store = True
    )

    
    action_domain = fields.Char(
        string='action_domain',
        compute='_compute_action_domain',
        store=True,
    )
    action_context = fields.Char(
        string='action_domain',
        compute='_compute_action_domain',
        store=True ) 
    relation = fields.Char(
        string='action_domain',
    )
    
    @api.constrains('action_id')
    def _check_action_id(self):
        for record in self:
            is_record = self.sudo().search_count([('action_id','=',record.action_id.id)])
            if is_record > 1:
                raise ValidationError(_('there is a record for this action.'))
            
    @api.depends('action_id')
    def _compute_action_domain(self):
        for record in self:
            record.action_domain = record.action_id.domain
            record.action_context = record.action_id.context


    @api.onchange('model_id')
    def _get_stage_value(self):
        for rec in self:
            if rec.model_id: 
                rec.model_name = rec.model_id.model
                  
               
    @api.depends('model_name')
    def _compute_field(self):
        for rec in self:
            if rec.model_id:
                #use those fileds to attr invisiable 
                model = self.env[rec.model_name]
                #model holidays has special case,
                #becuase when holiday work flow installed records of leave can hold state or stage depends on holiday type.
                if rec.model_name == 'hr.holidays':
                    rec.is_double =  True

                elif 'stage_id' in model._fields:
                    rec.is_stage =  True  
            
                elif 'state' in model._fields:
                    rec.is_state =  True
              
    
    @api.depends('name', 'model_id')
    def name_get(self):
        result = []
        for record in self:
            if record.name:
                name = record.name
            else:
                name = record.model_id.name
            result.append((record.id, name))
        return result
    
    def _get_stage(self,rel):
        #this method recive the relation model and return the stage on this obj
        #we get the stage ids for rel and create them in intermediate table.
        for rec in self:
            current_model = self.env['stage.stage'].sudo().search([('model_id','=',rec.model_id.id)])
            stage_ids = self.env[rel].sudo().search([])
            if not current_model:
                for stage in stage_ids:
                    # TODO: find a way to fix translation without searching in translation model &
                    #we got translaton issue stage name is translatable ,so we get the stage translation
                    value = self.env['ir.translation'].sudo().search([('source','=',stage.name)],limit=1).value
                    stage = self.env['stage.stage'].sudo().create({'model_id':rec.model_id.id , 'form_view_id':rec.form_view_id.id , 'list_view_id':rec.list_view_id.id ,'stage_id':stage.id ,'name':stage.name,'value':value})
            else:
                self.update_selection()           

         
    def update_selection(self):
        '''
        in this method we need to check if new states or stages were added
        we have a module in which new state will be added "odoo_dynamic_workflow",
        so we need to check if its installed , and get only the new state and update the intermediate object with it.
        same goes when deleting state , we search for the deleted ones and remove them from our intermediate object.
        we have three types of lines choose either stage or state or both depends on the model,
        both is only when the modeli is "hr.holidays",because there is a workflow mdouel that replace the state with stage depends on holiday type

        '''
        odoo_dynamic_workflow = self.env['ir.module.module'].sudo().search([('name', '=', 'odoo_dynamic_workflow')])

        
        for rec in self:
            if odoo_dynamic_workflow and odoo_dynamic_workflow.state == 'installed': 
                model = self.env[rec.model_name]
                work_folow_active = self.env['odoo.workflow'].sudo().search([('model_id','=',rec.model_id.id),('active','=',True)])
                work_folow_inactive = self.env['odoo.workflow'].sudo().search([('model_id','=',rec.model_id.id),('active','=',False)])
                state = self.env['node.state'].sudo().search([('is_workflow','=',True)])
                work_folow_name = work_folow_active.node_ids.filtered( lambda r: r.code_node == False and r.active ==True ).mapped( "node_name" ) 
                state_name = state.mapped('state')
                if not rec.is_stage and rec.model_name != 'hr.holidays':
                    for line in work_folow_active.node_ids:
                        if not line.code_node and line.active:
                            if not self.env['node.state'].sudo().search([('state','=',line.node_name)]):
                                state = self.env['node.state'].create({'model_id':rec.model_id.id , 'form_view_id':rec.form_view_id.id , 'list_view_id':rec.list_view_id.id ,'action_id':rec.action_id.id,'state':line.node_name ,'name':line.name,'is_workflow':True})

                    diffs = (list(set(state_name) - set(work_folow_name)))
                    state = self.env['node.state'].sudo().search([('state','in',diffs)]).unlink()

                    for line in work_folow_inactive.node_ids:
                        to_remove = []
                        if not line.code_node:
                            to_remove.append(line.node_name)
                            for stat in rec.line_ids:
                                if stat.state_id.state == line.node_name or stat.state_id.name == line.name or  stat.state_id.state == line.node_name  or stat.state_id.name == line.name:
                                    stat.unlink()
                        self.env['node.state'].sudo().search([('state','in',to_remove)]).unlink()




            if rec.is_stage:
                rel = self.env['ir.model.fields'].sudo().search([('model_id','=',rec.model_id.id),('name','=','stage_id')])
                current_model = self.env['stage.stage'].sudo().search([('model_id','=',rec.model_id.id)]).ids
                rel_ids = self.env[rel.relation].sudo().search([])
                if current_model:
                    for rel in rel_ids:
                        if rel.id not in current_model:
                            stage = self.env['stage.stage'].create({'model_id':rec.model_id.id , 'form_view_id':rec.form_view_id.id , 'list_view_id':rec.list_view_id.id ,'stage_id':rel.id ,'name':rel.name,})   

            if rec.model_name == 'hr.holidays':
                rel = self.env['ir.model.fields'].sudo().search([('model_id','=',rec.model_id.id),('name','=','stage_id')])
                current_model = self.env['node.state'].sudo().search([('model_id','=',rec.model_id.id)]).mapped('name')
                for line in work_folow_active.node_ids:
                    if not line.code_node and line.active:
                        if not self.env['node.state'].sudo().search([('state','=',line.node_name)]):
                            state = self.env['node.state'].create({'model_id':rec.model_id.id , 'form_view_id':rec.form_view_id.id , 'list_view_id':rec.list_view_id.id ,'action_id':rec.action_id.id,'state':line.node_name ,'name':line.name,'is_workflow':True})
                if rel:
                    rel_ids = self.env[rel.relation].sudo().search([('state','=','approved')]).mapped('name')
                    diffs = (list(set(rel_ids) - set(current_model))) 
                    for diff in diffs:
                        stage = self.env['node.state'].create({'model_id':rec.model_id.id , 'form_view_id':rec.form_view_id.id , 'list_view_id':rec.list_view_id.id , 'action_id':rec.action_id.id,'stage_id':rel.id ,'state':diff,'name':diff,'is_holiday_workflow':True})

                    holiday_workflow_leave = self.env['node.state'].sudo().search([('is_holiday_workflow','=',True)]).mapped( "name" )
                    diffs = (list(set(holiday_workflow_leave) - set(rel_ids)))
                    state = self.env['node.state'].sudo().search([('name','in',diffs)]).unlink()

                for line in work_folow_inactive.node_ids:
                        diff = []
                        if not line.code_node:
                            diff.append(line.node_name)
                            for stat in rec.line_ids:
                                if stat.state_id.state == line.node_name or stat.state_id.name == line.name or  stat.state_id.state == line.node_name  or stat.state_id.name == line.name:
                                    stat.unlink()
                        self.env['node.state'].sudo().search([('state','in',diffs)]).unlink()
  
    def compute_selection(self):
        ''' method used to compute the states or stages depends on chosen model
        it looks in model fields and see if it contains state or stage fields
        then dive in those fields and get their values and create them in a middle obj
        yet "hr.holidays could have both states and stages if holiday workflow module is installed"
        '''

        for rec in self:
            rec.is_button = True
            model = self.env[rec.model_name]
            current_model = self.env['node.state'].sudo().search([('model_id','=',rec.model_id.id)])
            if rec.model_name == 'hr.holidays':
                rec.is_double = True
                if not current_model:
                    nodes = model._fields.get('state')._description_selection(self.env)
                    rel = self.env['ir.model.fields'].sudo().search([('model_id','=',rec.model_id.id),('name','=','stage_id')])
                   
                    
                    for node in nodes:
                        state = self.env['node.state'].create({'model_id':rec.model_id.id , 'form_view_id':rec.form_view_id.id , 'list_view_id':rec.list_view_id.id ,'action_id':rec.action_id.id,'state':node[0] ,'name':node[1]})
                    if rel:
                        rel_ids = self.env[rel.relation].sudo().search([])
                        for rel in rel_ids:
                            if rel.state == 'approved':
                                stage = self.env['node.state'].create({'model_id':rec.model_id.id , 'form_view_id':rec.form_view_id.id , 'list_view_id':rec.list_view_id.id , 'action_id':rec.action_id.id,'stage_id':rel.id ,'name':rel.name,'is_holiday_workflow':True})

                else:
                    self.update_selection()            
            
            if 'state' in model._fields and rec.model_name != 'hr.holidays' :
                if not current_model:
                    nodes = model._fields.get('state')._description_selection(self.env)
                    
                    for node in nodes:
                        state = self.env['node.state'].create({'model_id':rec.model_id.id , 'form_view_id':rec.form_view_id.id , 'list_view_id':rec.list_view_id.id ,'action_id':rec.action_id.id,'state':node[0] ,'name':node[1]})
                else:
                    self.update_selection()

            if 'stage_id' in model._fields and rec.model_name != 'hr.holidays':
                rel = self.env['ir.model.fields'].sudo().search([('model_id','=',rec.model_id.id),('name','=','stage_id')])
                #call method to get the stage of the model 
                self._get_stage(rel.relation)

            if 'state' not in model._fields and not 'stage_id' in model._fields :
                #raise error if no state nor state
                raise ValidationError(_('This model has no states nor stages.'))


class BaseDashboardUser(models.Model):
    _name = 'base.dashbord.line'

   
    name = fields.Char(
        string='name',
    )
    
    group_ids = fields.Many2many(
        string='Group',
        comodel_name='res.groups',

        
    )
    board_id = fields.Many2one(
        string='Bord',
        comodel_name='base.dashbord'

    )
    state_id = fields.Many2one(
        string='State',
        comodel_name='node.state'

    )
    stage_id = fields.Many2one(
        string='Stage',
        comodel_name='stage.stage'

    )
    

    model_id = fields.Many2one(string='Model', comodel_name='ir.model')

    model_name = fields.Char(
        string='Model Name',

    )
    sequence = fields.Integer(
        string='sequence',
    )

    @api.onchange('state_id')
    def onchange_state_id(self):
       
        state_ids = []
        if self.state_id:
            for stat in self.board_id.line_ids:
                state_ids.append(stat.state_id.id)
            if state_ids.count(self.state_id.id) > 2:
                raise ValidationError(_('already choose this state'))


    @api.onchange('stage_id')
    def onchange_stage_id(self):
        
        stage_ids = []
        if self.stage_id:
            for stat in self.board_id.line_ids:
                stage_ids.append(stat.stage_id.id)
            if stage_ids.count(self.stage_id.id) > 2:
                raise ValidationError(_('already choose this stage'))
    
    
class NodeState(models.Model):
    _name = 'node.state'

    @api.depends('name', 'state')
    def name_get(self):
        result = []
        for record in self:
            if self.env.user.lang == 'en_US':
                if record.state:
                    name = record.state
            if self.env.user.lang == 'ar_001' or self.env.user.lang == 'ar_EG':
                if record.name:
                    name = record.name
            result.append((record.id, name))
        return result

    
   

    
    name = fields.Char(
        string='name', translate=True
    )
    
    state = fields.Char(
        string='state', translate=True
    )

    stage_id = fields.Char(
        string='Stage',readonly=True 
    )
    
    is_workflow = fields.Boolean(
        string='is_workflow',
        readonly=True 
        
    )

    
    is_holiday_workflow = fields.Boolean(
        string='is_holiday_workflow', readonly=True 
    )
    
    
    model_id = fields.Many2one(string='Model', comodel_name='ir.model', readonly=True )
    
    form_view_id = fields.Many2one('ir.ui.view', string='Form View', readonly=True )
    list_view_id = fields.Many2one('ir.ui.view', string='List View',readonly=True)
    action_id = fields.Many2one('ir.actions.act_window', string='Action',readonly=True)

   

class StageStage(models.Model):
    _name = 'stage.stage'


    @api.depends('name', 'value')
    def name_get(self):
        result = []
        for record in self:
            if self.env.user.lang == 'en_US':
                if record.name:
                    name = record.name
            if self.env.user.lang == 'ar_001' or self.env.user.lang == 'ar_EG':
                if record.value:
                    name = record.value
            result.append((record.id, name))
        return result
   

    
    name = fields.Char(
        string='name', translate=True,readonly=True
    )
    
    stage_id = fields.Char(
        string='Stage',readonly=True
    )

    value = fields.Char(
        string='value',readonly=True
    )


    model_id = fields.Many2one(string='Model', comodel_name='ir.model',readonly=True)
    
    form_view_id = fields.Many2one('ir.ui.view', string='Form View',readonly=True)
    list_view_id = fields.Many2one('ir.ui.view', string='List View',readonly=True)
    action_id = fields.Many2one('ir.actions.act_window', string='Action',readonly=True)    

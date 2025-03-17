# -*- coding: utf-8 -*-

from datetime import timedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class ProjectPhaseType(models.Model):
    _name = "project.phase.type"
    _description = 'Phase Type'

    name = fields.Char(string="Name")
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.user.company_id)
    
    
class ProjectPhase(models.Model):
    _name = 'project.phase'
    _description = 'Phase'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'project_id,start_date'

    name = fields.Char(string='Phase Name', compute='_compute_name', store=True)
    phase_id = fields.Many2one('project.phase.type', string="Phase")
    sequence = fields.Integer(string='Sequence')
    project_id = fields.Many2one('project.project', string='Project',ondelete="restrict",
                                 default=lambda self: self.env.context.get('default_project_id'))
    start_date = fields.Date(string='Start Date', copy=True)
    end_date = fields.Date(string='End Date', copy=True)
    estimated_hours = fields.Float("Allocated By",copy=False)
    company_id = fields.Many2one('res.company', related="project_id.company_id", string='Company')
    task_count = fields.Integer(compute="get_task", string='Tasks')
    task_ids = fields.One2many("project.task",'phase_id',string='Tasks')
    weight = fields.Float(string="Weight")
    progress = fields.Float(compute="get_progress", store=True, string="Progress")
    notes = fields.Text(string='Notes',copy=False)
    certificate_id = fields.Many2one('completion.certificate',string='Completion Certificate')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('open', 'Running'),
        ('close', 'Closed')], string='Status',
        copy=False, default='draft', required=True, readonly=True, tracking=True)
    # phase_id = fields.Many2one('project.phase', string="Stage")

    allowed_internal_user_ids = fields.Many2many('res.users', 'project_phase_allowed_internal_users_rel',
                                                 string="Allowed Internal Users", default=lambda self: self.env.user, domain=[('share', '=', False)])
    allowed_portal_user_ids = fields.Many2many('res.users', 'project_phase_allowed_portal_users_rel', string="Allowed Portal Users", domain=[('share', '=', True)])
    # allowed_user_ids = fields.Many2many('res.users', compute='_compute_allowed_users', inverse='_inverse_allowed_user')
    
    # @api.depends('allowed_internal_user_ids', 'allowed_portal_user_ids')
    # def _compute_allowed_users(self):
    #     for project in self:
    #         users = project.allowed_internal_user_ids | project.allowed_portal_user_ids
    #         project.allowed_user_ids = users

    # def _inverse_allowed_user(self):
    #     for project in self:
    #         allowed_users = project.allowed_user_ids
    #         project.allowed_portal_user_ids = allowed_users.filtered('share')
    #         project.allowed_internal_user_ids = allowed_users - project.allowed_portal_user_ids

    def write(self, values):
        if 'start_date' in values or 'end_date' in values:
            #send notification to pm to edit ivoice date
            if self.project_id.user_id:
                users = [self.project_id.user_id]
                notification_ids = [(0, 0,
                                     {
                                         'res_partner_id': user.partner_id.id,
                                         'notification_type': 'inbox'
                                     }
                                     ) for user in users if user.partner_id]

                if notification_ids:
                    self.env['mail.message'].create({
                        'message_type': "notification",
                        'body': _(
                            "The Stage %s Dates for project %s Edit ,edit invoice dates accordingly") % (self.display_name,self.project_id.display_name),
                        'subject': _("Stage Dates has been updated"),
                        'partner_ids': [(4, user.partner_id.id) for user in users if users],
                        'model': self._name,
                        'res_id': self.id,
                        'notification_ids': notification_ids,
                        'author_id': self.env.user.partner_id and self.env.user.partner_id.id
                    })
        if self._context.get('open_from',False):
            if self._context.get('open_from',False) == 'vo':
                vo_id = self._context.get('vo_id',[])
                vo = self.env['project.variation.order'].browse(vo_id)
                message = str('from ' + (vo and vo.name or "VO"))
                if self._context.get('edit_reasone',False):
                    message = message + _(" For Reasone: %s"%(self._context.get('edit_reasone'," ")))
            else:
                message = _("From Project For Reasone: %s"%(self._context.get('edit_reasone'," ")))
                
            body = _("<p style='color: #FF0000;'><b>Project Phase updated %s</b></p><ul>"%( message ))
            fields = self.fields_get()
            old_values = self.read(values.keys())[0]
            for k, v in values.items():
                field = fields.get(k)
                if field['type'] == 'selection':
                    val = dict(field['selection'])[v]
                    old_val = dict(field['selection'])[old_values[k]]
                elif field['type'] == 'many2one':
                    val = self.env[field['relation']].sudo().browse(v).name_get()[0][1]
                    old_val = old_values[k][1]
                elif field['type'] == 'many2many':
                    val = ""
                    old_val = ""
                    for mv in v:
                        val += self.env[field['relation']].sudo().browse(mv).name_get()[0][1] +"  "
                else:
                    val = v
                    old_val = old_values[k]
                body += "<li>%s: %s -> %s</li>" % (field['string'], old_val, val)
            body += "</ul>"
            self.env['mail.message'].create({
                'body': body,
                'model': 'project.phase',
                'res_id': self.id,
                'subtype_id': '2',
            })
        return super(ProjectPhase, self).write(values)

    def unlink(self):
        for rec in self:
            invoice_ids = self.env['project.invoice'].search([('phase_id','=',rec.id), ('project_id', '=', rec.project_id.id)])
            invoice_ids.unlink()
        super(ProjectPhase, self).unlink()

    @api.depends('task_ids.weight', 'task_ids.task_progress','task_ids')        
    def get_progress(self):
        for rec in self:
            progress = 0.0
            if rec.task_ids:
                done_task = self.env['project.task'].search([('phase_id', '=', rec.id)])
                # import pdb
                # pdb.set_trace()
                progress =  ((sum([x.weight * x.task_progress for x in done_task]))  / 100)
                # progress = round(100.0 * float((len(done_task) / len(rec.task_ids))), 2)
            rec.progress = progress
            
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for rec in self:
            # Ensure that the fields are not None or False before comparison
            if not rec.end_date or not rec.project_id.start or not rec.project_id.date:
                continue  # Skip validation if any date field is missing
            
            # Perform the date comparison safely
            if rec.end_date < rec.project_id.start or rec.end_date > rec.project_id.date:
                raise ValidationError("End date must be between the project's start and end dates.")
            
            if rec.filtered(lambda c: c.end_date and c.start_date > c.end_date):
                raise ValidationError(_('Phase start date must be earlier than Phase end date.'))
            if rec.project_id.start and rec.project_id.date and (rec.start_date < rec.project_id.start or rec.start_date > rec.project_id.date) or \
               (rec.end_date < rec.project_id.start or rec.end_date > rec.project_id.date):
                raise ValidationError(_('Phase dates must be between project dates.'))

    def action_draft(self):
        return self.write({'state': 'draft'})

    def action_confirm(self):
        for rec in self:
            if not rec.start_date or not rec.end_date:
                raise ValidationError(_('Make sure that stage dates is set.'))
        return self.write({'state': 'open'})

    def action_close(self):                
        return self.write({'state': 'close'})

    def action_reopen(self):
        return self.write({'state': 'open'})

    @api.depends('phase_id')
    def _compute_name(self):
        for rec in self:
            rec.name = rec.phase_id.name

    def action_project_phase_task(self):
        self.ensure_one()
        return {
            'name': 'Tasks',
            'type': 'ir.actions.act_window',
            'view_mode': 'tree,form',
            'res_model': 'project.task',
            'domain': [('phase_id', '=', self.id)],
        }

    def action_view_project_invoice(self):
        self.ensure_one()
        action_window = {
            "type": "ir.actions.act_window",
            "res_model": "project.invoice",
            "name": "Invoice Requests",
            'view_type': 'form',
            'view_mode': 'tree,form',
            "context": {"create": False, "edit": False},
            "domain": [('phase_id', '=', self.id), ('project_id', '=', self.project_id.id)]
        }
        return action_window

    def get_task(self):
        for rec in self:
            records = self.env['project.task'].search([('phase_id', '=', rec.id)])
            rec.task_count = len(records)


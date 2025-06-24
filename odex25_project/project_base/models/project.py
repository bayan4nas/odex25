# -*- coding: utf-8 -*-
import ast
import calendar
from datetime import datetime, time, timedelta
from dateutil import relativedelta
from odoo.osv import expression
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from dateutil.relativedelta import relativedelta
from odoo.fields import Date
from lxml import etree


















class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        if self._context.get('from_project_owner_field'):
            args = args or []
            employees = self.sudo().search([('name', operator, name)] + args, limit=limit)
            return employees.name_get()
        return super().name_search(name, args, operator, limit)

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        if self._context.get('from_project_owner_field'):
            return super(HrEmployee, self.sudo()).search(args, offset=offset, limit=limit, order=order, count=count)
        return super().search(args, offset=offset, limit=limit, order=order, count=count)


class Project(models.Model):
    _inherit = "project.project"
    _order = "project_no desc"
    owner_employee_id = fields.Many2one(
        'hr.employee',
        string="Owner Employee",
        context={'from_project_owner_field': True, 'no_open': True}
    )

    def _get_task_type(self):
        """
        :return:  project task type if it default
        """
        type_ids = self.env['project.task.type'].search([('is_default', '=', True)])
        return type_ids

    name = fields.Char("Name", index=True, tracking=True, required=False)
    project_no = fields.Char("Project Number", default=lambda self: self._get_next_projectno(), tracking=True,
                             copy=False)
    completion_certificate_ids =fields.One2many('completion.certificate','project_id')
    category_id = fields.Many2one('project.category', string='Project Category', tracking=True)
    parent_id = fields.Many2one('project.project', index=True, string='Parent Project', tracking=True)
    sub_project_id = fields.One2many('project.project', 'parent_id', string='Sub-Project', tracking=True)
    department_id = fields.Many2one('hr.department', string='Department')
    department_execute_id = fields.Many2one('hr.department', string='Department to which executed')
    consultant_id = fields.Many2one('res.partner', string='Consultant')
    beneficiary_id = fields.Many2one('res.partner', string='Beneficiary')
    lessons_learned = fields.Html(string='Lessons learned')
    launch_date = fields.Datetime("Launch date", tracking=True)
    start = fields.Date(string="Start Date", index=True, tracking=True)
    date = fields.Date(string='End Date', index=True, tracking=True)
    project_phase_ids = fields.One2many('project.phase', 'project_id', string="Project Phases")
    tag_ids = fields.Many2many('project.tags', string='Tags')
    type_ids = fields.Many2many('project.task.type', 'project_task_type_rel', 'project_id', 'type_id',
                                string='Tasks Stages', default=_get_task_type)
    priority = fields.Selection([('0', 'Normal'),('1', 'Important'),], default='0', index=True, string="Priority")
    #
    # address fields
    street = fields.Char()
    street2 = fields.Char()
    zip = fields.Char(change_default=True)
    country_id = fields.Many2one('res.country', string='Country', default=lambda self: self.env.company.country_id,
                                 ondelete='restrict', tracking=True)
    state_id = fields.Many2one("res.country.state", string='Region', ondelete='restrict')
    city = fields.Char()
    # Contract fields
    contract_number = fields.Char(string="Contract Number", tracking=True)
    signature_date = fields.Date(string="Signature Date", tracking=True)
    contract_value = fields.Float("Total Contract Value")
    consultant_cost = fields.Float(
        string='Consultant Cost',)
    tax_amount = fields.Float("Taxes Amount")
    contract_value_untaxed = fields.Float("Contract Value")
    state = fields.Selection([
        ('draft', 'PMO'),
        ('confirm', 'PM'),
        ('done', 'Done')], string='State', copy=False, default='draft', required=True, tracking=True)
    status = fields.Selection([
        ('new', 'New'), ('open', 'Running'),
        ('hold', 'Hold'), ('close', 'Closed')], string='Status', copy=False, default='new', tracking=True)
    hold_reason = fields.Text(string="Hold Reason")
    close_reason = fields.Text(string="Close Reason")
    project_team_ids = fields.One2many('project.team', 'project_id', string="Project Team")
    invoice_ids = fields.One2many('project.invoice', 'project_id', "Invoice", copy=False, help="The Details of invoice")
    total_invoiced_amount = fields.Float('Total Invoiced Amount',store=True, compute='compute_total_invoiced_amount')
    no_of_invoices = fields.Integer(compute='compute_total_invoiced_payment')
    no_of_paid_invoices = fields.Integer(compute='compute_total_invoiced_payment')
    total_invoiced_payment = fields.Float('Paid Amount',store=True, compute='compute_total_invoiced_payment')
    residual_amount = fields.Float('Remaining Amount',store=True, compute='compute_residual_amount')
    back_log_amount = fields.Float('Back Log Amount',store=True, compute='compute_back_log_amount')
    # TODO check if this fields needed
    is_down_payment = fields.Boolean('Down Payment')
    to_invoice = fields.Boolean(compute="compute_to_invoice", store=True)
    invoice_method = fields.Selection([
        ('per_stage', 'Invoicing Per Phase'),
        ('per_period', 'Invoicing Per Period'),
    ], string='Invoicing Method', default=lambda self: self.env.company.invoice_method, )
    invoice_period = fields.Integer(string="Invoicing Every", default=lambda self: self.env.company.invoice_period)
    resource_calendar_id = fields.Many2one('resource.calendar', string='Working Time',
                                           default=lambda self: self.env.company.resource_calendar_id, related=False,
                                           help="Working Time used in this project")
    sale_order_amount = fields.Monetary("SO Total Amount", tracking=True)
    type = fields.Selection([
        ('revenue', 'Revenue'),
        ('expense', 'Expense'),
        ('internal', 'Internal')], default=lambda self: self.env.company.type, string='Type')
    man_hours = fields.Boolean('Man hours', default=False)
    progress = fields.Float(compute="get_progress", store=True, string="Progress")
    task_count_all = fields.Integer(compute='_compute_task_count_all', string="All Task Count")
    task_count_finished = fields.Integer(compute='_compute_task_count_finished', string="Finished Task Count")
    task_count_new = fields.Integer(compute='_compute_task_count_new', string="New Task Count")
    task_count_inprogress = fields.Integer(compute='_compute_task_count_inprogress', string="In progress Task Count")
    user_id = fields.Many2one('res.users', string='Project Manager', default=lambda self: self.env.user, tracking=True,domain=lambda self: [("groups_id", "in", self.env.ref("project.group_project_manager").id)])

    privacy_visibility = fields.Selection([
            ('followers', 'Invited internal users'),
            ('employees', 'All internal users'),
            ('portal', 'Invited portal users and all internal users'),
        ],
        string='Visibility', required=False,
        default='portal',
        help="People to whom this project and its tasks will be visible.\n\n"
            "- Invited internal users: when following a project, internal users will get access to all of its tasks without distinction. "
            "Otherwise, they will only get access to the specific tasks they are following.\n "
            "A user with the project > administrator access right level can still access this project and its tasks, even if they are not explicitly part of the followers.\n\n"
            "- All internal users: all internal users can access the project and all of its tasks without distinction.\n\n"
            "- Invited portal users and all internal users: all internal users can access the project and all of its tasks without distinction.\n"
            "When following a project, portal users will get access to all of its tasks without distinction. Otherwise, they will only get access to the specific tasks they are following.")

    allowed_internal_user_ids = fields.Many2many('res.users', 'project_allowed_internal_users_rel',
                                                 string="Allowed Internal Users", default=lambda self: self.env.user, domain=[('share', '=', False)])
    allowed_portal_user_ids = fields.Many2many('res.users', 'project_allowed_portal_users_rel', string="Allowed Portal Users", domain=[('share', '=', True)])



    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        # إذا كان البحث يتم على موظفين، استخدم sudo لتجاوز الصلاحيات
        if self._name == 'hr.employee':
            employees = self.env['hr.employee'].sudo().search(
                args or [], limit=limit
            )
            return employees.name_get()
        return super(Project, self).name_search(name, args, operator, limit)

    # @api.model
    # def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
    #     res = super(Project, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar, submenu=submenu)
    #
    #     if view_type == 'form':
    #         doc = etree.XML(res['arch'])
    #         for field in doc.xpath("//field[@name='owner_employee_id']"):
    #             employees = self.env['hr.employee'].sudo().search([])
    #             employee_ids = employees.ids
    #             field.set('domain', "[('id', 'in', %s)]" % employee_ids)
    #
    #         res['arch'] = etree.tostring(doc, encoding='unicode')
    #     return res

    @api.onchange('department_id')
    def _onchange_department_id(self):

        if self.department_id:
            self.owner_employee_id = False
            manager = self.env['hr.employee'].search([
                ('department_id', '=', self.department_id.id),
                ('user_id', '!=', False)
            ], limit=1)
            if manager:
                self.owner_employee_id = manager.id



    allow_timesheets = fields.Boolean(
        "Timesheets", compute='_compute_allow_timesheets', store=True, readonly=False,
        default=False, help="Enable timesheeting on the project.")
    def get_attached_domain(self):
        return ['|','|','|',
            '&',('res_model', '=', 'project.project'),
            ('res_id', 'in', self.ids),
            '&',('res_model', '=', 'project.task'),
            ('res_id', 'in', self.task_ids.ids),
            '&',('res_model', '=', 'project.invoice'),
            ('res_id', 'in', self.invoice_ids.ids),
            '&',('res_model', '=', 'project.phase'),
            ('res_id', 'in', self.project_phase_ids.ids),
        ]
    @api.onchange('department_execute_id')
    def onchange_department_execute_id(self):
        self.analytic_account_id = self.department_execute_id.analytic_account_id.id
        
    def _compute_attached_docs_count(self):
        Attachment = self.env['ir.attachment']
        for project in self:
            project.doc_count = Attachment.search_count(self.get_attached_domain())
    
    def attachment_tree_view(self):
        action = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        action['domain'] = str(self.get_attached_domain())
        action['context'] = "{'default_res_model': '%s','default_res_id': %d}" % (self._name, self.id)
        return action
    def _compute_task_count_all(self):
        task_data = self.env['project.task'].read_group([('project_id', 'in', self.ids)], ['project_id'],
                                                        ['project_id'])
        result = dict((data['project_id'][0], data['project_id_count']) for data in task_data)
        for project in self:
            project.task_count_all = result.get(project.id, 0)

    def _compute_task_count_finished(self):
        task_data = self.env['project.task'].read_group([('project_id', 'in', self.ids),
                                                         ('stage_id.is_closed', '=', True)], ['project_id'],
                                                        ['project_id'])
        result = dict((data['project_id'][0], data['project_id_count']) for data in task_data)
        for project in self:
            project.task_count_finished = result.get(project.id, 0)

    def _compute_task_count_new(self):
        task_data = self.env['project.task'].read_group([('project_id', 'in', self.ids),
                                                         ('stage_id.sequence', '=', 0)], ['project_id'], ['project_id'])
        result = dict((data['project_id'][0], data['project_id_count']) for data in task_data)
        for project in self:
            project.task_count_new = result.get(project.id, 0)

    def _compute_task_count_inprogress(self):
        task_data = self.env['project.task'].read_group(
            [('project_id', 'in', self.ids), ('stage_id.is_closed', '=', False),
             ('stage_id.fold', '=', False), ('stage_id.sequence', '!=', 0)], ['project_id'], ['project_id'])
        result = dict((data['project_id'][0], data['project_id_count']) for data in task_data)
        for project in self:
            project.task_count_inprogress = result.get(project.id, 0)

    @api.depends('project_phase_ids', 'project_phase_ids.weight', 'project_phase_ids.progress')
    def get_progress(self):
        for rec in self:
            progress = 0.0
            for phase in rec.project_phase_ids:
                progress += phase.weight * phase.progress / 100
            rec.progress = progress
            
    @api.depends('invoice_ids', 'invoice_ids.amount')
    def compute_total_invoiced_amount(self):
        for rec in self:
            rec.total_invoiced_amount = sum(rec.invoice_ids.mapped('amount'))
            
    @api.depends('invoice_ids', 'invoice_ids.amount','invoice_ids.payment_amount')
    def compute_total_invoiced_payment(self):
        for rec in self:
            rec.total_invoiced_payment = 0
            rec.no_of_invoices = 0
            rec.no_of_paid_invoices = 0
            total_paid = 0
            total_prepaid=0
            if rec.invoice_ids:
                rec.no_of_invoices = len(rec.invoice_ids)
                total_paid_prepaid = len(rec.invoice_ids.sudo().filtered(lambda x: x.invoice_id))
                total_prepaid = len(rec.invoice_ids.sudo().filtered(lambda x: not x.invoice_id and x.prepaid))
                rec.no_of_paid_invoices = total_paid_prepaid + total_prepaid
                rec.total_invoiced_payment = sum(rec.invoice_ids.mapped("payment_amount"))

    @api.depends('total_invoiced_amount', 'total_invoiced_payment')
    def compute_residual_amount(self):
        for rec in self:
            rec.residual_amount = rec.total_invoiced_amount - rec.total_invoiced_payment

    @api.depends('total_invoiced_amount', 'contract_value')
    def compute_back_log_amount(self):
        for rec in self:
            rec.back_log_amount = rec.contract_value - rec.total_invoiced_amount

    @api.model
    def _get_next_projectno(self):
        next_sequence = "/ "
        sequence = self.env['ir.sequence'].search(
            ['|', ('company_id', '=', self.env.company[0].id), ('company_id', '=', False),
             ('code', '=', 'project.project')], limit=1)
        if sequence:
            next_sequence = sequence.get_next_char(sequence.number_next_actual)
        return next_sequence

    @api.model
    def create(self, vals):
        company_id = vals.get('company_id', self.default_get(['company_id'])['company_id'])
        self_comp = self.with_company(company_id)
        if not vals.get('project_no', False):
            vals['project_no'] = self_comp.env['ir.sequence'].next_by_code('project.project') or '/'
        return super().create(vals)

    def write(self, vals):
        """
        If invoice method=per_stage when add stage create project invoice
        """
        line_ids = []
        res = super(Project, self).write(vals)
        for project in self:
            if project.type != 'internal' and vals.get('project_phase_ids') and project.invoice_method == 'per_stage':
                line_ids = []
                phase_ids = project.invoice_ids.mapped('phase_id').ids
                for line in project.sudo().sale_order_id.order_line:
                    line_ids.append((0, 0, {
                    'order_line_id': line.id,
                    'product_id': line.product_id.id,
                    'product_uom': line.product_uom.id,
                    'price_unit': line.price_unit,
                    'discount': line.discount,
                    'tax_id': [(6, 0, line.tax_id.ids)],
                    }))
                project.invoice_ids = [(0, 0, {
                    'name': phase.display_name,
                    'phase_id': phase.id,
                    'project_invline_ids': line_ids,
        }) for phase in project.project_phase_ids.filtered(lambda x: x.id not in phase_ids)]
        return res

    def name_get(self):
        res = []
        for record in self:
            if record.project_no:
                res.append((record.id, ("[" + record.project_no + "] " + (record.name or " "))))
            else:
                res.append((record.id, record.name))
        return res

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        args = args or []
        if operator == 'ilike' and not (name or '').strip():
            domain = []
        else:
            connector = '&' if operator in expression.NEGATIVE_TERM_OPERATORS else '|'
            domain = [connector, ('project_no', operator, name), ('name', operator, name)]
        return self._search(expression.AND([domain, args]), limit=limit, access_rights_uid=name_get_uid)

    # State funtions
    def action_draft(self):
        return self.write({'state': 'draft'})

    def action_confirm(self):
        for record in self:
            # Send Notification to Project manger
            if record.user_id:
                users = [record.user_id]
                notification_ids = [(0, 0, {
                    'res_partner_id': user.partner_id.id,
                    'notification_type': 'inbox'}) for user in users if user.partner_id]
                if notification_ids:
                    self.env['mail.message'].create({
                        'message_type': "notification",
                        'body': _(
                            "You Have been assign as a manger for The project %s kindly complete project data") % record.display_name,
                        'subject': _("You Have been assign As project manger"),
                        'partner_ids': [(4, user.partner_id.id) for user in users if users],
                        'model': record._name,
                        'res_id': record.id,
                        'notification_ids': notification_ids,
                        'author_id': self.env.user.partner_id and self.env.user.partner_id.id})
            if record.type != 'internal':
                record.create_project_invoice()
        return self.write({'state': 'confirm'})

    def action_done(self):
        for record in self:
            line_ids = []
            # check project Stages
            if record.type != 'internal':
                if not record.project_phase_ids and record.invoice_method == 'per_stage':
                    raise ValidationError(_("Kindly Enter project Stage first."))
        return self.write({'state': 'done'})

    def create_project_invoice(self):
        """
        Create Project Invoice in confirm base on invoice_method = per_period 
        """
        for record in self:
            line_ids = []
            if record.invoice_ids:
                return True
            if (record.date and record.start) and record.invoice_method == 'per_period':
                for line in record.sudo().sale_order_id.order_line.filtered(lambda x: not x.is_downpayment):
                    line_ids.append(
                        (0, 0, {'order_line_id': line.id, 'product_id': line.product_id.id,
                                'product_uom': line.product_uom.id,
                                'price_unit': line.price_unit, 'discount': line.discount,
                                'tax_id': [(6, 0, line.tax_id.ids)]}))
                diff = record.date - record.start
                project_days = diff.days
                period = project_days / record.invoice_period
                invoice_date = record.start + relativedelta.relativedelta(days=record.invoice_period)
                for rec in range(int(period)):
                    record.invoice_ids = [(0, 0, {'project_invline_ids': line_ids, 'plan_date': invoice_date})]
                    invoice_date = invoice_date + relativedelta.relativedelta(days=record.invoice_period)

    def action_view_tasks_analysis(self):
        """ return the action to see the tasks analysis report of the project """
        action = self.env['ir.actions.act_window']._for_xml_id('project.action_project_task_user_tree')
        action_context = ast.literal_eval(action['context']) if action['context'] else {}
        action_context['search_default_project_id'] = self.id
        return dict(action, context=action_context)

    def action_creat_tasks(self):
        action = self.with_context(active_id=self.id, active_ids=self.ids) \
            .env.ref('project_base.create_tast_proj') \
            .sudo().read()[0]
        action['display_name'] = self.name
        return action

    def action_view_finished_tasks(self):
        action = self.with_context(active_id=self.id, active_ids=self.ids) \
            .env.ref('project_base.act_project_project_2_project_task_finished') \
            .sudo().read()[0]
        action['display_name'] = self.name
        return action

    def action_view_inprogress_tasks(self):
        action = self.with_context(active_id=self.id, active_ids=self.ids) \
            .env.ref('project_base.act_project_project_2_project_task_inprogress') \
            .sudo().read()[0]
        action['display_name'] = self.name
        return action

    def action_view_new_tasks(self):
        action = self.with_context(active_id=self.id, active_ids=self.ids) \
            .env.ref('project_base.act_project_project_2_project_task_new') \
            .sudo().read()[0]
        action['display_name'] = self.name
        return action

    # Status funtions
    def action_open(self):
        for rec in self:
            # check that all invoice planned issue dates is entred
            invoice_ids = self.invoice_ids.filtered(lambda x: x.plan_date == False)
            if invoice_ids:
                raise ValidationError(_('Please be sure to enter all planned issue dates for invoices.'))
        return self.write({'status': 'open'})

    def action_reopen(self):
        return self.write({'status': 'open', 'close_reason': False})

    def action_hold(self):
        return self.write({'status': 'hold'})

    def action_close(self):
        return self.write({'status': 'close'})

    def action_project_invoice(self):
        action_window = {
            "type": "ir.actions.act_window",
            "res_model": "project.invoice",
            "name": "project Invoice",
            'view_type': 'form',
            'view_mode': 'tree,form',
            "context": {"create": True, "project_id": self.id, 'search_default_project': 1},
            "domain": [('project_id', '=', self.id)]
        }
        return action_window

    def action_paid_invoice(self):
        action_window = {
            "type": "ir.actions.act_window",
            "res_model": "project.invoice",
            "name": "project Invoice",
            'view_type': 'form',
            'view_mode': 'tree,form',
            "context": {"create": True, "project_id": self.id, 'search_default_project': 1},
            "domain": [('project_id', '=', self.id), ('state', '=', 'done')]
        }
        return action_window

    def action_view_expense(self):
        self.ensure_one()
        action_window = {
            "type": "ir.actions.act_window",
            "res_model": "hr.expense",
            "name": "Expenses",
            "views": [[False, "tree"]],
            "context": {"create": False},
            "domain": [('analytic_account_id', '=', self.analytic_account_id.id)]
        }
        return action_window

    def action_view_purchase(self):
        self.ensure_one()
        action_window = {
            "type": "ir.actions.act_window",
            "res_model": "purchase.order",
            "name": "Purchase",
            "views": [[False, "tree"]],
            "context": {"create": False},
            "domain": [('project_id', '=', self.id)]
        }
        return action_window

    @api.model
    def update_project_status(self):
        """ 
        this funtion call by cron to close the project if end date come
        """
        projects = self.env['project.project'].search([('status', '=', 'open'), ('date', '<=', fields.Date.today())])
        for record in projects:
            close_reason = "The Project Auto Closed by system because reach end date %s" % (record.date)
            record.write({'status': 'close', 'close_reason': close_reason, 'state': 'confirm'})
            users = [record.user_id]
            notification_ids = []
            if users:
                notification_ids = [(0, 0,
                                     {
                                         'res_partner_id': user.partner_id.id,
                                         'notification_type': 'inbox'
                                     }
                                     ) for user in users if user.partner_id]
            if notification_ids:
                self.env['mail.message'].create({
                    'message_type': "notification",
                    'body': close_reason,
                    'subject': _("The project %s was automatically Closed by system") % record.display_name,
                    'partner_ids': [(4, user.partner_id.id) for user in users if users],
                    'model': record._name,
                    'res_id': record.id,
                    'notification_ids': notification_ids,
                    'author_id': self.env.user.partner_id and self.env.user.partner_id.id
                })

    @api.model
    def project_invoice_notification(self):
        """
           send notification to PM in invoice date
        """
        projects = self.env['project.invoice'].search([])
        for record in projects:
            if record.plan_date == datetime.now().date() and not record.invoice_id:
                record.to_invoice = True
                user_ids = self.env.ref('project.group_project_manager').users
                self.env['mail.message'].create({'message_type': "notification",
                                                 'body': _('This invoice is due and must be issue %s' % (record.name)),
                                                 'subject': _("Project Invoice Creation"),
                                                 'partner_ids': [(6, 0, user_ids.mapped('partner_id').ids)],
                                                 'notification_ids': [(0, 0, {'res_partner_id': user.partner_id.id,
                                                                              'notification_type': 'inbox'})
                                                                      for user in user_ids if user_ids],
                                                 'model': self._name,
                                                 'res_id': record.project_id.id,
                                                 })
            else:
                record.to_invoice = False

    def create_invoice(self):
        self.ensure_one()
        line_id = self.env['project.invoice'].search(
            [('project_id', '=', self.id), ('to_invoice', '=', True)], limit=1)
        return {
            'name': _('Invoices'),
            'res_model': 'project.invoice',
            'type': 'ir.actions.act_window',
            'res_id': line_id.id,
            'view_mode': 'form',
        }

    def update_invoices(self, is_down_payment):
        InvLine = self.env['project.invoice.line']
        for record in self:
            if is_down_payment:
                downpayment_line = record.sale_order_id.mapped('order_line').filtered(lambda l: l.is_downpayment)
                for line in downpayment_line:
                    for inv in record.invoice_ids:
                        if not inv.has_downpayment:
                            values = {'project_invoice_id': inv.id, 'order_line_id': line.id,
                                      'product_id': line.product_id.id, 'product_uom': line.product_uom.id,
                                      'price_unit': line.price_unit, 'product_uom_qty': 0}
                            InvLine.create(values)

    def create_down_payment(self):
        ''' Opens a wizard to create down payment '''
        self.ensure_one()
        ctx = {
            'active_model': 'sale.order',
            'active_ids': self.sale_order_id.ids,
            'active_id': self.sale_order_id.id,
            'project_id': self.id,
        }
        return {
            'type': 'ir.actions.act_window',
            'view_mode': 'form',
            'res_model': 'sale.advance.payment.inv',
            'views': [(False, 'form')],
            'view_id': False,
            'target': 'new',
            'context': ctx,
        }

    @api.depends('invoice_ids', 'invoice_ids.to_invoice')
    def compute_to_invoice(self):
        for rec in self:
            invoice_id = rec.invoice_ids.filtered(lambda x: x.to_invoice == True)
            if invoice_id:
                rec.to_invoice = True
            else:
                rec.to_invoice = False


class ProjectCategory(models.Model):
    _name = "project.category"

    name = fields.Char(string="Name")
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.user.company_id)


class ProjectHoldReason(models.Model):
    _name = "project.hold.reason"

    name = fields.Char(string="Name")
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.user.company_id)


class Stage(models.Model):
    _inherit = 'project.task.type'

    color_gantt = fields.Char(
        string="Color Task Bar",
        help="Choose your color for Task Bar",
        default="rgba(170,170,13,0.53)")
    stage_for = fields.Selection(
        string='',
        selection=[('project', 'Project'),
                   ('tasks', 'Tasks'), ],
        required=True, default='project')
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.user.company_id)
    is_default = fields.Boolean(string="Default in new project")


class ProjectTeam(models.Model):
    _name = "project.team"

    employee_id = fields.Many2one('hr.employee', string="Employee")
    project_id = fields.Many2one('project.project', string="Project")
    department_id = fields.Many2one('hr.department', related="employee_id.department_id", string="Department")
    job_id = fields.Many2one('hr.job', related="employee_id.job_id", string="Job")
    project_job = fields.Char(string="Job In Project")

    @api.onchange('job_id')
    def _onchange_job(self):
        if not self.project_job:
            self.project_job = self.job_id and self.job_id.name or ''
# project_base.group_project_department_manager
#             <field name="user_id" string="Project Manager" widget="many2one_avatar_user" attrs="{'readonly':[('active','=',False)]}" domain="[('share', '=', False)]"/>




class CompletionCertificateOutput(models.Model):
    _name = 'completion.certificate.output'
    _description = 'Certificate Output'

    certificate_id = fields.Many2one(
        'completion.certificate',
        string='Completion Certificate',
        required=True,
        ondelete='cascade'
    )
    name = fields.Char(string='Output Name', required=True)
    description = fields.Text(string='Description', required=True)

















class CompletionCertificateAttachment(models.Model):
    _name = 'completion.certificate.attachment'
    _description = 'Completion Certificate Attachment'

    certificate_id = fields.Many2one('completion.certificate', string='Completion Certificate', required=True)
    attachment = fields.Binary(string='Attachment', required=True)
    name = fields.Char(string='File Name', required=True)









class CompletionCertificate(models.Model):
    _name = 'completion.certificate'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = _('Completion Certificate')
    name = fields.Char(string='Certificate Name',
                       required=True, readonly=True,
                       default=lambda self: self.env['ir.sequence'].next_by_code('completion.certificate')
)
    description = fields.Text(string='Description')
    project_id = fields.Many2one('project.project', string='Project', required=True)
    check_project_owner = fields.Boolean(
        string='Is Project Owner',
        compute='_compute_check_project_owner',
        store=False
    )
    phase_id4 = fields.Many2one(
        'project.phase',
        string='Project Phase',
        domain="[('project_id', '=', project_id)]" if project_id else [('id', '=', '')],
        required=True
    )
    certificate_output_ids = fields.One2many(
        'completion.certificate.output',
        'certificate_id',
        string="Outputs",
        required=True
    )

    date = fields.Date(string='Date', required=True)
    attachment = fields.Binary(string="Attachment", attachment=True)
    state = fields.Selection([
        ('project_manager_preparation', 'Project Manager Preparation'),
        ('project_manager_review', 'Waiting for Project Manager Review'),
        ('project_owner_approval', 'Waiting for Project Owner Approval'),

        ('strategy_office_review', 'Waiting for Strategy Office Review'),
        ('secretary_general_approval', 'Waiting for Secretary General Approval'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='project_manager_preparation', tracking=True)

    previous_state_map = {
        'project_manager_review': 'project_manager_preparation',
        'project_owner_approval': 'project_manager_review',
        'strategy_office_review': 'project_owner_approval',
        'secretary_general_approval': 'strategy_office_review',
    }

    check_project_user = fields.Boolean(
        string='Is Project User?',
        compute='_compute_check_project_user',
        store=False
    )
    equivalent_output_weight = fields.Float(
        string='Equivalent Weight (%)',
        required=True
    )

    achievement_percentage = fields.Float(
        string='Achievement (%)',
        required=True
    )

    service_provider_performance = fields.Text(
        string='Provider Performance',
        required=True
    )

    planned_spending_until_delivery = fields.Float(
        string='Planned Spending (SAR)',
        required=True
    )

    actual_spending_until_delivery = fields.Float(
        string='Actual Spending (SAR)',
        required=True
    )

    attachment_ids = fields.Many2many(
        'ir.attachment',
        'completion_certificate_ir_attachments_rel',
        'certificate_id',
        'attachment_id',
        string="Attachments",
        help="Attach files to the completion certificate"
    )
    project_duration = fields.Char('Project Duration', store=True)

    project_manager_preparation_id = fields.Many2one('res.users', string='Approver User', readonly=True)
    project_manager_preparation_date = fields.Date(string="Approver Date", readonly=True)

    project_owner_approval_id = fields.Many2one('res.users', string="Owner Project Approval", readonly=True)
    project_owner_approval_date = fields.Date(string="Owner Approval Date", readonly=True)

    project_manager_review_id = fields.Many2one('res.users', string='Project Manager Review', readonly=True)
    project_manager_review_date = fields.Date(string="Manager Review Date", readonly=True)

    strategy_office_review_id = fields.Many2one('res.users', string='Strategy Office Review', readonly=True)
    strategy_office_review_date = fields.Date(string="Strategy Review Date", readonly=True)

    secretary_general_approval_id = fields.Many2one('res.users', string='Secretary General Approval', readonly=True)
    secretary_general_approval_date = fields.Date(string="Secretary Approval Date", readonly=True)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('completion.certificate') or '/'

        self._validate_required_fields(vals)
        return super().create(vals)

    def write(self, vals):
        self._validate_required_fields(vals)
        return super().write(vals)

    def _validate_required_fields(self, vals):
        required_fields = [
            'equivalent_output_weight',
            'achievement_percentage',
            'planned_spending_until_delivery',
            'actual_spending_until_delivery',
            'service_provider_performance',
        ]
        for field in required_fields:
            if field in vals and not vals[field]:
                raise ValidationError(_(f"The field '{self._fields[field].string}' is required."))

    @api.constrains('achievement_percentage')
    def _check_achievement_percentage(self):
        for record in self:
            if not (0 <= record.achievement_percentage <= 100):
                raise ValidationError(_("Achievement Percentage must be between 0 and 100."))
    @api.constrains('equivalent_output_weight')
    def _check_equivalent_output_weight(self):
        for rec in self:
            if not (0 <= rec.equivalent_output_weight <= 100):
                raise ValidationError(_("Equivalent Weight (%) must be between 0 and 100."))

    @api.depends('project_id')
    def _compute_check_project_user(self):
        current_user = self.env.uid
        if current_user ==self.project_id.user_id.id:
            self.check_project_user = True
        else:
            self.check_project_user = False

    @api.depends('project_id')
    def _compute_check_project_owner(self):
        for rec in self:
            current_user = rec.env.uid
            project_owner_user_id = rec.project_id.sudo().owner_employee_id.sudo().user_id.id
            rec.check_project_owner = (current_user == project_owner_user_id)

    def action_go_back(self):
        # report_action = self.env.ref('project_base.action_completion_certificate_report')
        #
        # return report_action.report_action(self)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Go Back'),
            'res_model': 'go.back.reason.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_certificate_id': self.id,
            },
        }

    def action_cancel(self):
        return {
            'type': 'ir.actions.act_window',
            'name': _('Cancel'),
            'res_model': 'cancel.reason.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_certificate_id': self.id,
            },
        }

    def re_draft(self):
        self.ensure_one()
        self.state = 'project_manager_preparation'

    def action_confirm_preparation(self):
        self.ensure_one()
        self.state = 'project_manager_review'
        self.project_manager_preparation_id = self.env.uid
        self.project_manager_preparation_date =Date.today()

    def action_approve_project_owner(self):

        # if self.env.user.has_group('project_base.group_project_owner'):
            self.state = 'strategy_office_review'
            self.project_owner_approval_id = self.env.uid
            self.project_owner_approval_date =Date.today()




    def action_review_project_manager(self):
        self.ensure_one()
        # if self.env.user.has_group('project.group_project_manager'):
        self.state = 'project_owner_approval'
        self.project_manager_review_id = self.env.uid
        self.project_manager_review_date = Date.today()

    def action_review_strategy_office(self):
        self.ensure_one()
        # if self.env.user.has_group('strategy_office.group_strategy_manager'):
        print(Date.today())
        self.state = 'secretary_general_approval'
        self.strategy_office_review_id = self.env.uid
        self.strategy_office_review_date = Date.today()



    def action_approve_secretary_general(self):
        self.ensure_one()
        # if self.env.user.has_group('admin.group_secretary_general'):
        self.state = 'done'
        self.secretary_general_approval_id = self.env.uid
        self.secretary_general_approval_date = Date.today()




    def action_done(self):
        self.ensure_one()
        self.state = 'done'

    def unlink(self):
        for rec in self:
            if rec.state != 'project_manager_preparation':
                raise UserError(_("You can only delete a certificate when it's in the Draft state."))
        return super(CompletionCertificate, self).unlink()





class ReportCompletionCertificate(models.AbstractModel):
    _name = 'report.project_base.completion_certificate_report_template'
    _description = 'Completion Certificate Report'

    def _get_report_values(self, docids, data=None):
        docs = self.env['completion.certificate'].browse(docids)
        for doc in docs:
            if doc.state != 'done':
                raise UserError(_("You cannot print an incomplete completion certificate."))
            doc.project_duration = self.get_duration(doc.project_id.start, doc.project_id.date)

            doc.project_duration = self.get_duration(doc.project_id.start, doc.project_id.date)

        return {
            'doc_ids': docids,
            'doc_model': 'completion.certificate',
            'docs': docs,
            'no_attachment': True,
        }

    def get_duration(self, start_date, end_date):
        if not start_date or not end_date:
            return ''
        delta = relativedelta(end_date, start_date)
        parts = []
        if delta.years:
            parts.append(f"{delta.years}سنة" if delta.years == 1 else f"{delta.years}سنوات")
        if delta.months:
            parts.append(f"{delta.months}شهر" if delta.months == 1 else f"{delta.months}أشهر")
        if delta.days:
            parts.append(f"{delta.days}يوم" if delta.days == 1 else f"{delta.days}أيام")
        return ' و'.join(parts)





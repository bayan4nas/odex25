# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.tools.safe_eval import safe_eval
from odoo.tools.sql import column_exists, create_column


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    tasks_ids = fields.Many2many('project.task', compute='_compute_tasks_ids', string='Tasks associated to this purchase')
    tasks_count = fields.Integer(string='Tasks', compute='_compute_tasks_ids', groups="project.group_project_user")

    visible_project = fields.Boolean('Display project', compute='_compute_visible_project', readonly=True)
    visible_project_btn = fields.Boolean('Display project BTN', compute='_compute_visible_project_btn', readonly=True)
    project_id = fields.Many2one(
        'project.project', 'Project', readonly=True,
        states={'draft': [('readonly', False)], 'sent': [('readonly', False)]},
        help='Select a project for tasks related to this purchase order.')
    project_ids = fields.Many2many('project.project', compute="_compute_project_ids", string='Projects', copy=False, help="Projects used in this purchases order.")

    @api.depends('order_line.product_id.purchase_project_id')
    def _compute_tasks_ids(self):
        for order in self:
            order.tasks_ids = self.env['project.task'].search([('purchase_line_id', 'in', order.order_line.ids), ('purchase_order_id', '=', order.id)])
            order.tasks_count = len(order.tasks_ids)

    @api.depends('order_line.product_id.purchase_service_tracking')
    def _compute_visible_project(self):
        for order in self:
            order.visible_project = any(
                purchase_service_tracking == 'task_in_project' for purchase_service_tracking in order.order_line.mapped('product_id.purchase_service_tracking')
            )
    @api.depends('order_line.product_id.purchase_service_tracking')
    def _compute_visible_project_btn(self):
        for order in self:
            order.visible_project_btn = any(
                purchase_service_tracking in ['task_in_project','task_global_project','project_only'] for purchase_service_tracking in order.order_line.mapped('product_id.purchase_service_tracking')
            )
            # if visible_project_btn and not order.tasks_ids and not order.project_ids:
            #     order.visible_project_btn = visible_project_btn
            # else :
            #     order.visible_project_btn = False
    @api.depends('order_line.product_id', 'order_line.project_id')
    def _compute_project_ids(self):
        for order in self:
            projects = order.order_line.mapped('product_id.purchase_project_id')
            projects |= order.order_line.mapped('project_id')
            projects |= order.project_id
            order.project_ids = projects

    @api.onchange('project_id')
    def _onchange_project_id(self):
        """ Set the PO analytic account to the selected project's analytic account """
        if self.project_id.analytic_account_id:
            self.account_analytic_id = self.project_id.analytic_account_id

    def button_create_project_tasks(self):
        """ On PO confirmation, some lines should generate a task or a project. """
        if len(self.company_id) == 1:
            # All orders are in the same company
            self.order_line.sudo().with_company(self.company_id)._timesheet_service_generation()
        else:
            # Orders from different companies are confirmed together
            for order in self:
                order.order_line.sudo().with_company(order.company_id)._timesheet_service_generation()

    def action_view_task(self):
        self.ensure_one()
        list_view_id = self.env.ref('project.view_task_tree2').id
        form_view_id = self.env.ref('project.view_task_form2').id
        action = {'type': 'ir.actions.act_window_close'}
        task_projects = self.tasks_ids.mapped('project_id')
        if len(task_projects) == 1 and len(self.tasks_ids) > 1:
            action = self.with_context(active_id=task_projects.id).env['ir.actions.actions']._for_xml_id('project.act_project_project_2_project_task_all')
            action['domain'] = [('id', 'in', self.tasks_ids.ids)]
            if action.get('context'):
                eval_context = self.env['ir.actions.actions']._get_eval_context()
                eval_context.update({'active_id': task_projects.id})
                action_context = safe_eval(action['context'], eval_context)
                action_context.update(eval_context)
                action['context'] = action_context
        else:
            action = self.env["ir.actions.actions"]._for_xml_id("project.action_view_task")
            action['context'] = {}
            if len(self.tasks_ids) > 1:
                action['views'] = [[False, 'kanban'], [list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'calendar'], [False, 'pivot']]
            elif len(self.tasks_ids) == 1:
                action['views'] = [(form_view_id, 'form')]
                action['res_id'] = self.tasks_ids.id

        action.setdefault('context', {})
        action['context'].update({'search_default_purchase_order_id': self.id})
        return action

    def action_view_project_ids(self):
        self.ensure_one()
        view_form_id = self.env.ref('project.edit_project').id
        view_kanban_id = self.env.ref('project.view_project_kanban').id
        action = {
            'type': 'ir.actions.act_window',
            'domain': [('id', 'in', self.project_ids.ids)],
            'views': [(view_kanban_id, 'kanban'), (view_form_id, 'form')],
            'view_mode': 'kanban,form',
            'name': _('Projects'),
            'res_model': 'project.project',
        }
        return action

    def write(self, values):
        if 'state' in values and values['state'] == 'cancel':
            self.project_id.sudo().purchase_line_id = False
        return super(PurchaseOrder, self).write(values)



class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"

    project_id = fields.Many2one(
        'project.project', 'Generated Project',
        index=True, copy=False, help="Project generated by the purchases order item")
    task_id = fields.Many2one(
        'project.task', 'Generated Task',
        index=True, copy=False, help="Task generated by the purchases order item")
    is_service = fields.Boolean("Is a Service", compute='_compute_is_service', store=True, compute_sudo=True, help="purchase Order item should generate a task and/or a project, depending on the product settings.")

    @api.depends('product_id.type')
    def _compute_is_service(self):
        for line in self:
            line.is_service = line.product_id.type == 'service'
    
    def _auto_init(self):
        """
        Create column to stop ORM from computing it himself (too slow)
        """
        if not column_exists(self.env.cr, 'purchase_order_line', 'is_service'):
            create_column(self.env.cr, 'purchase_order_line', 'is_service', 'bool')
            self.env.cr.execute("""
                UPDATE purchase_order_line line
                SET is_service = (pt.type = 'service')
                FROM product_product pp
                LEFT JOIN product_template pt ON pt.id = pp.product_tmpl_id
                WHERE pp.id = line.product_id
            """)
        return super()._auto_init()
    
    @api.model_create_multi
    def create(self, vals_list):
        lines = super().create(vals_list)
        # Do not generate task/project when expense PO line, but allow
        # generate task with hours=0.
        for line in lines:
            if line.state == 'purchase':
                line.sudo()._timesheet_service_generation()
                # if the PO line created a task, post a message on the order
                if line.task_id:
                    msg_body = _("Task Created (%s): <a href=# data-oe-model=project.task data-oe-id=%d>%s</a>") % (line.product_id.name, line.task_id.id, line.task_id.name)
                    line.order_id.message_post(body=msg_body)
        return lines
    
    def write(self, values):
        result = super().write(values)
        # changing the ordered quantity should change the planned hours on the
        # task, whatever the PO state. It will be blocked by the super in case
        # of a locked purchase order.
        if 'product_uom_qty' in values and not self.env.context.get('no_update_planned_hours', False):
            for line in self:
                if line.task_id and line.product_id.type == 'service':
                    planned_hours = line._convert_qty_company_hours(line.task_id.company_id)
                    line.task_id.write({'planned_hours': planned_hours})
        return result
    
    def _convert_qty_company_hours(self, dest_company):
        return self.product_uom_qty
    
    def _prepare_analytic_account_data(self, prefix=None):
        """
        Prepare method for analytic account data

        :param prefix: The prefix of the to-be-created analytic account name
        :type prefix: string
        :return: dictionary of value for new analytic account creation
        """
        name = self.name
        if prefix:
            name = prefix + ": ["+ self.order_id.name +"]"+ self.name
        return {
            'name': name,
            'code': self.order_id.partner_ref,
            'company_id': self.company_id.id,
            'partner_id': self.partner_id.id
        }   

    def _create_analytic_account(self, prefix=None):
        for order in self:
            analytic = self.env['account.analytic.account'].create(order._prepare_analytic_account_data(prefix))
            order.account_analytic_id = analytic

    def _timesheet_create_project_prepare_values(self):
        """Generate project values"""
        account = self.account_analytic_id
        if not account:
            self._create_analytic_account(prefix=self.product_id.default_code or None)
            account = self.account_analytic_id

        # create the project or duplicate one
        return {
            'name': '%s - %s' % (self.order_id.partner_ref, self.name) if self.order_id.partner_ref else self.name,
            'analytic_account_id': account.id,
            'partner_id': self.order_id.partner_id.id,
            'purchase_line_id': self.id,
            'purchase_order_id': self.order_id.id,
            'active': True,
            'company_id': self.company_id.id,
            'contract_value_untaxed':self.price_subtotal,
            'tax_amount':self.price_tax,
            'contract_value':self.price_total,
            'type':'expense',
        }

    def _timesheet_create_project(self):
        """ Generate project for the given po line, and link it.
            :param project: record of project.project in which the task should be created
            :return task: record of the created task
        """
        self.ensure_one()
        values = self._timesheet_create_project_prepare_values()
        if self.product_id.purchase_project_template_id:
            values['name'] = "%s - %s" % (values['name'], self.product_id.purchase_project_template_id.name)
            project = self.product_id.purchase_project_template_id.copy(values)
            project.tasks.write({
                'purchase_line_id': self.id,
                'partner_id': self.order_id.partner_id.id,
                'email_from': self.order_id.partner_id.email,
            })
            # duplicating a project doesn't set the PO on sub-tasks
            project.tasks.filtered(lambda task: task.parent_id != False).write({
                'purchase_line_id': self.id,
                'purchase_order_id': self.order_id,
            })
        else:
            project = self.env['project.project'].create(values)

        # Avoid new tasks to go to 'Undefined Stage'
        if not project.type_ids:
            project.type_ids = self.env['project.task.type'].create({'name': _('New')})

        # link project as generated by current po line
        self.write({'project_id': project.id})
        return project

    def _timesheet_create_task_prepare_values(self, project):
        self.ensure_one()
        planned_hours = self._convert_qty_company_hours(self.company_id)
        purchase_line_name_parts = self.name.split('\n')
        title = purchase_line_name_parts[0] or self.product_id.name
        description = '<br/>'.join(purchase_line_name_parts[1:])
        return {
            'name': title if project.purchase_line_id else '%s: %s' % (self.order_id.name or '', title),
            'planned_hours': planned_hours,
            'partner_id': self.order_id.partner_id.id,
            'email_from': self.order_id.partner_id.email,
            'description': description,
            'project_id': project.id,
            'purchase_line_id': self.id,
            'purchase_order_id': self.order_id.id,
            'company_id': project.company_id.id,
            'user_id': False,  # force non assigned task, as created as sudo()
        }
        
    def _timesheet_create_task(self, project):
        """ Generate task for the given po line, and link it.
            :param project: record of project.project in which the task should be created
            :return task: record of the created task
        """
        values = self._timesheet_create_task_prepare_values(project)
        task = self.env['project.task'].sudo().create(values)
        self.write({'task_id': task.id})
        # post message on task
        task_msg = _("This task has been created from: <a href=# data-oe-model=purchase.order data-oe-id=%d>%s</a> (%s)") % (self.order_id.id, self.order_id.name, self.product_id.name)
        task.message_post(body=task_msg)
        return task
        
    def _timesheet_service_generation(self):
        
        po_line_task_global_project = self.filtered(lambda pol: pol.product_id.purchase_service_tracking == 'task_global_project')
        po_line_new_project = self.filtered(lambda pol: pol.product_id.purchase_service_tracking in ['project_only', 'task_in_project'])

        # search po lines from PO of current po lines having their project generated, in order to check if the current one can
        # create its own project, or reuse the one of its order.
        map_po_project = {}
        if po_line_new_project:
            order_ids = self.mapped('order_id').ids
            po_lines_with_project = self.search([('order_id', 'in', order_ids), ('project_id', '!=', False), ('product_id.purchase_service_tracking', 'in', ['project_only', 'task_in_project']), ('product_id.purchase_project_template_id', '=', False)])
            map_po_project = {pol.order_id.id: pol.project_id for pol in po_lines_with_project}
            po_lines_with_project_templates = self.search([('order_id', 'in', order_ids), ('project_id', '!=', False), ('product_id.purchase_service_tracking', 'in', ['project_only', 'task_in_project']), ('product_id.purchase_project_template_id', '!=', False)])
            map_po_project_templates = {(pol.order_id.id, pol.product_id.purchase_project_template_id.id): pol.project_id for pol in po_lines_with_project_templates}

        # search the global project of current PO lines, in which create their task
        map_pol_project = {}
        if po_line_task_global_project:
            map_pol_project = {pol.id: pol.product_id.with_company(pol.company_id).purchase_project_id for pol in po_line_task_global_project}

        def _can_create_project(pol):
            if not pol.project_id:
                if pol.product_id.purchase_project_template_id:
                    return (pol.order_id.id, pol.product_id.purchase_project_template_id.id) not in map_po_project_templates
                elif pol.order_id.id not in map_po_project:
                    return True
            return False

        def _determine_project(po_line):
            """Determine the project for this purchase order line.
            Rules are different based on the purchase_service_tracking:

            - 'project_only': the project_id can only come from the purchase order line itself
            - 'task_in_project': the project_id comes from the purchase order line only if no project_id was configured
              on the parent purchase order"""

            if po_line.product_id.purchase_service_tracking == 'project_only':
                return po_line.project_id
            elif po_line.product_id.purchase_service_tracking == 'task_in_project':
                return po_line.order_id.project_id or po_line.project_id

            return False
        # import pdb
        # pdb.set_trace()
        # task_global_project: create task in global project
        for po_line in po_line_task_global_project:
            if not po_line.task_id:
                if map_pol_project.get(po_line.id):
                    po_line._timesheet_create_task(project=map_pol_project[po_line.id])

        # project_only, task_in_project: create a new project, based or not on a template (1 per PO). May be create a task too.
        # if 'task_in_project' and project_id configured on PO, use that one instead
        for po_line in po_line_new_project:
            project = _determine_project(po_line)
            if not project and _can_create_project(po_line):
                project = po_line._timesheet_create_project()
                if po_line.product_id.purchase_project_template_id:
                    map_po_project_templates[(po_line.order_id.id, po_line.product_id.purchase_project_template_id.id)] = project
                else:
                    map_po_project[po_line.order_id.id] = project
            elif not project:
                # Attach subsequent PO lines to the created project
                po_line.project_id = (
                    map_po_project_templates.get((po_line.order_id.id, po_line.product_id.purchase_project_template_id.id))
                    or map_po_project.get(po_line.order_id.id)
                )
            if po_line.product_id.purchase_service_tracking == 'task_in_project':
                if not project:
                    if po_line.product_id.purchase_project_template_id:
                        project = map_po_project_templates[(po_line.order_id.id, po_line.product_id.purchase_project_template_id.id)]
                    else:
                        project = map_po_project[po_line.order_id.id]
                if not po_line.task_id:
                    po_line._timesheet_create_task(project=project)


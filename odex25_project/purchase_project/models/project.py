# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from ast import literal_eval

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class Project(models.Model):
    _inherit = 'project.project'

    purchase_line_id = fields.Many2one(
        'purchase.order.line', 'Purchase Order Item', copy=False,
        domain="[('is_service', '=', True), ('is_expense', '=', False), ('order_id', '=', purchase_order_id), ('state', 'in', ['purchase', 'done']), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="Purchase order item to which the project is linked. Link the timesheet entry to the Purchase order item defined on the project. "
        "Only applies on tasks without purchase order item defined, and if the employee is not in the 'Employee/Purchase Order Item Mapping' of the project.")
    purchase_order_id = fields.Many2one('purchase.order', 'Purchase Order',
        domain="[('order_line.product_id.type', '=', 'service'), ('partner_id', '=', partner_id), ('state', 'in', ['purchase', 'done'])]",
        copy=False, help="Purchase order to which the project is linked.")

    _sql_constraints = [
        ('purchase_order_required_if_purchase_line', "CHECK((purchase_line_id IS NOT NULL AND purchase_order_id IS NOT NULL) OR (purchase_line_id IS NULL))", 'The project should be linked to a purchase order to select a purchase order item.'),
    ]

    @api.model
    def _map_tasks_default_valeus(self, task, project):
        defaults = super()._map_tasks_default_valeus(task, project)
        defaults['purchase_line_id'] = False
        return defaults

    def action_view_po(self):
        self.ensure_one()
        action_window = {
            "type": "ir.actions.act_window",
            "res_model": "purchase.order",
            "name": "Purchase Order",
            "views": [[False, "form"]],
            "context": {"create": False, "show_purchase": True},
            "res_id": self.purchase_order_id.id
        }
        return action_window


class ProjectTask(models.Model):
    _inherit = "project.task"

    purchase_order_id = fields.Many2one('purchase.order', 'Purchase Order', help="Purchase order to which the task is linked.")
    purchase_line_id = fields.Many2one(
        'purchase.order.line', 'Purchase Order Item', 
        domain="[('company_id', '=', company_id), ('is_service', '=', True), ('partner_id', 'child_of', commercial_partner_id), ('state', 'in', ['purchase', 'done']), ('order_id', '=?', project_purchase_order_id)]",
        compute='_compute_purchase_line', store=True, readonly=False, copy=False,
        help="Purchase order item to which the project is linked. Link the timesheet entry to the Purchase order item defined on the project. "
        "Only applies on tasks without purchase order item defined, and if the employee is not in the 'Employee/Purchase Order Item Mapping' of the project.")
    project_purchase_order_id = fields.Many2one('purchase.order', string="Project's purchase order", related='project_id.purchase_order_id')
    invoice_count = fields.Integer("Number of invoices", related='purchase_order_id.invoice_count')
    task_to_invoice = fields.Boolean("To invoice", compute='_compute_task_to_invoice', search='_search_task_to_invoice')

    @api.depends('project_id.purchase_line_id.partner_id')
    def _compute_partner_id(self):
        for task in self:
            if not task.partner_id:
                task.partner_id = task.project_id.purchase_line_id.partner_id
        super()._compute_partner_id()

    @api.depends('commercial_partner_id', 'purchase_line_id.partner_id.commercial_partner_id', 'parent_id.purchase_line_id', 'project_id.purchase_line_id')
    def _compute_purchase_line(self):
        for task in self:
            print("*****************************")
            if not task.purchase_line_id:
                task.purchase_line_id = task.parent_id.purchase_line_id or task.project_id.purchase_line_id
            # check purchase_line_id and customer are coherent
            if task.purchase_line_id.partner_id.commercial_partner_id != task.partner_id.commercial_partner_id:
                task.purchase_line_id = False

    @api.constrains('purchase_line_id')
    def _check_purchase_line_type(self):
        for task in self.sudo():
            if task.purchase_line_id:
                if not task.purchase_line_id.is_service :
                    raise ValidationError(_(
                        'You cannot link the order item %(order_id)s - %(product_id)s to this task because it is a re-invoiced expense.',
                        order_id=task.purchase_line_id.order_id.name,
                        product_id=task.purchase_line_id.product_id.display_name,
                    ))

    def unlink(self):
        if any(task.purchase_line_id for task in self):
            raise ValidationError(_('You have to unlink the task from the purchase order item in order to delete it.'))
        return super().unlink()

    # ---------------------------------------------------
    # Actions
    # ---------------------------------------------------

    def _get_action_view_po_ids(self):
        return self.purchase_order_id.ids

    def action_view_po(self):
        self.ensure_one()
        po_ids = self._get_action_view_po_ids()
        action_window = {
            "type": "ir.actions.act_window",
            "res_model": "purchase.order",
            "name": "Purchase Order",
            "views": [[False, "tree"], [False, "form"]],
            "context": {"create": False, "show_purchase": True},
            "domain": [["id", "in", po_ids]],
        }
        if len(po_ids) == 1:
            action_window["views"] = [[False, "form"]]
            action_window["res_id"] = po_ids[0]

        return action_window

    def rating_get_partner_id(self):
        partner = self.partner_id or self.purchase_line_id.order_id.partner_id
        if partner:
            return partner
        return super().rating_get_partner_id()

    @api.depends('purchase_order_id.invoice_status', 'purchase_order_id.order_line')
    def _compute_task_to_invoice(self):
        for task in self:
            if task.purchase_order_id:
                task.task_to_invoice = bool(task.purchase_order_id.invoice_status not in ('no', 'invoiced'))
            else:
                task.task_to_invoice = False

    @api.model
    def _search_task_to_invoice(self, operator, value):
        query = """
            SELECT po.id
            FROM purchase_order po
            WHERE po.invoice_status != 'invoiced'
                AND po.invoice_status != 'no'
        """
        operator_new = 'inselect'
        if(bool(operator == '=') ^ bool(value)):
            operator_new = 'not inselect'
        return [('purchase_order_id', operator_new, (query, ()))]

    def action_create_invoice(self):
        # ensure the PO exists before invoicing, then confirm it
        po_to_confirm = self.filtered(
            lambda task: task.purchase_order_id and task.purchase_order_id.state in ['draft', 'sent']
        ).mapped('purchase_order_id')
        po_to_confirm.action_confirm()

        # redirect create invoice wizard (of the Purchase Order)
        action = self.env["ir.actions.actions"]._for_xml_id("purchase.action_view_purchase_advance_payment_inv")
        context = literal_eval(action.get('context', "{}"))
        context.update({
            'active_id': self.purchase_order_id.id if len(self) == 1 else False,
            'active_ids': self.mapped('purchase_order_id').ids,
            'default_company_id': self.company_id.id,
        })
        action['context'] = context
        return action

class ProjectTaskRecurrence(models.Model):
    _inherit = 'project.task.recurrence'

    def _new_task_values(self, task):
        values = super(ProjectTaskRecurrence, self)._new_task_values(task)
        task = self.sudo().task_ids[0]
        values['purchase_line_id'] = self._get_purchase_line_id(task)
        return values

    def _get_purchase_line_id(self, task):
        return task.purchase_line_id.id

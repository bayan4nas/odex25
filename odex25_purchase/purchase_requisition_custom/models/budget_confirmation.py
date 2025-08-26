from odoo import fields, models, _


class BudgetConfirmationCustom(models.Model):
    _inherit = 'budget.confirmation'

    po_id = fields.Many2one('purchase.order')
    request_id = fields.Many2one('purchase.request')
    confirm_po = fields.Boolean()
    confirm_invoice = fields.Boolean()
    planned_for = fields.Boolean(string="Planned For")
    emergency = fields.Boolean(string="Emergency")
    available = fields.Boolean(string="Available")
    unavailable = fields.Boolean(string="Unavailable")
    specifications_conform = fields.Boolean(string="Technical specifications conform")
    specifications_not_conform = fields.Boolean(string="Technical specifications do not match")

    # def cancel(self):
    #     super(BudgetConfirmationCustom, self).cancel()
    #     for rec in self:
    #         if rec.po_id and rec.type == 'purchase.order':
    #             rec.po_id.write({'state': 'budget_rejected'})
    #             body = _(
    #                 "Purchase Order %s is Rejected By : %s  With Reject Reason : %s" % (
    #                     str(rec.name), str(rec.env.user.name),
    #                     str(rec.reject_reason or self.env.context.get('reject_reason', ''))))
    #             # Send Notifications
    #             subject = _('Reject Purchase Order')
    #             author_id = rec.env.user.partner_id.id or None
    #             rec.create_uid.partner_id.send_notification_message(subject=subject, body=body, author_id=author_id)
    #             rec.po_id.message_post(body=body)
    #         if rec.request_id and rec.type == 'purchase.request':
    #             rec.request_id.write({'state': 'refuse'})
    #             body = _(
    #                 "Purchase Request %s is Rejected By : %s  With Reject Reason : %s" % (
    #                     str(rec.name), str(rec.env.user.name),
    #                     str(rec.reject_reason or self.env.context.get('reject_reason', ''))))
    #             # Send Notifications
    #             subject = _('Reject Purchase Request Budget Confirmation')
    #             author_id = rec.env.user.partner_id.id or None
    #             rec.create_uid.partner_id.send_notification_message(subject=subject, body=body, author_id=author_id)
    #             rec.request_id.message_post(body=body)
    #
    # def done(self):
    #     super(BudgetConfirmationCustom, self).done()
    #     for line in self.lines_ids:
    #         budget_post = self.env['account.budget.post'].search([]).filtered(
    #             lambda x: line.account_id in x.account_ids)
    #         analytic_account_id = line.analytic_account_id
    #         budget_lines = analytic_account_id.crossovered_budget_line.filtered(
    #             lambda x: x.general_budget_id in budget_post and
    #                       x.crossovered_budget_id.state == 'done' and
    #                       x.date_from <= self.date <= x.date_to)
    #         for rec in budget_lines:
    #             if self.po_id and self.type == 'purchase.order':
    #                 # Update reserve of budget_lines
    #                 amount = rec.reserve
    #                 amount += line.amount
    #                 budget_lines.write({'reserve': amount})
    #
    #     if self.po_id.requisition_id and self.po_id.requisition_type_exclusive == 'exclusive':
    #         self.po_id.requisition_id.write({'state': 'checked'})
    #     if self.po_id:
    #         if self.po_id.requisition_id:
    #             self.po_id.write({'state': 'to approve'})
    #         else:
    #             self.po_id.write({'state': 'draft'})
    #     if self.request_id and self.type == 'purchase.request':
    #         # Update reserve of budget_lines
    #         self.request_id.write({'state': 'waiting'})


class CrossoveredBudgetLines(models.Model):
    _inherit = "crossovered.budget.lines"

    budget_confirm_line_ids = fields.One2many('budget.confirmation.line', 'budget_line_id', 'Confirmation')

# -*- coding: utf-8 -*-
##############################################################################
#
#   Expert (LCT, Life Connection Technology)
#    Copyright (C) 2021-2022 LCT
#
##############################################################################


from odoo import models, fields, tools, _

class ProjectTask(models.Model):
    _inherit = "project.task"

    days = fields.Integer(string="Days To be done")
    project_type_id = fields.Many2one('project.type', string="Project Type", ondelete="cascade")
    project_task_id = fields.Many2one('khawald.project.task')
    state = fields.Selection([('draft', 'Draft'),
                              ('done', 'Done')], string="Status", default='draft')
    marketing = fields.Boolean(string="Marketing")
    email_formatted = fields.Char(string="Formatted Email")
    completion_rate = fields.Float('Completion Rate')

    # def notification_message(self, group):
    #     receiver = []
    #     groups = []
    #     for ref in group:
    #         group_id = self.env.ref(ref).id
    #         groups.append(group_id)
    #     domain = [('id', 'in', groups)]
    #     group_ids = self.env['res.groups'].search(domain)
    #     if len(group_ids)> 1:
    #         for group in group_ids:
    #             for user in group.users:
    #                 if user.partner_id not in receiver:
    #                     receiver.append(user.partner_id)
    #     else:
    #         for user in group_ids.users:
    #             if user.partner_id not in receiver:
    #                 receiver.append(user.partner_id)
    #     return receiver

    # def compute_email(self, receiver):
    #     email_formatted = []
    #     final_receiver = receiver[0]
    #     count = len(final_receiver)
    #     for partner in range(count):
    #         if final_receiver[partner].email:
    #             email_formatted.append(tools.formataddr((final_receiver[partner].name or u"False", final_receiver[partner].email or u"False")))
    #         else:
    #             email_formatted = []
    #     return email_formatted

    # def action_draft(self):
    #     self.write({'state': 'draft'})

    # def action_done(self):
    #     for rec in self:
    #         rec.write({'state': 'done'})
    #         # Internal User Notification
    #         if rec.marketing:
    #             receiver = rec.notification_message(['real_estate_marketing.group_marketer_manager_user', 'real_estate_marketing.group_marketer_normal_user'])
    #             email = rec.compute_email(receiver)
    #             email = ','.join(email)
    #             rec.email_formatted = email
    #             template = rec.env.ref('khawald_project.template_marketing_task_complete', raise_if_not_found=False)
    #             ctx = dict(rec._context)
    #             ctx.update({
    #                 'model': rec._name
    #             })
    #             if template:
    #                 template.sudo().with_context(ctx).send_mail(rec.id, force_send=True)


from odoo import models, fields, api, _
from datetime import timedelta


class ServiceRequest(models.Model):
    _inherit = 'service.request'

    deadline = fields.Datetime(_("Deadline"), compute="_compute_deadline", store=True, readonly=True)
    escalated = fields.Boolean(_("Escalated"), default=False)
    service_id = fields.Many2one('benefits.service', string=_("Service"))
    sent_notification = fields.Boolean("Notification Sent", default=False)
    available_outputs = fields.Many2many(
        'benefits.output',
        compute='_compute_available_outputs',
        store=False
    )
    service_output = fields.Many2many(
        'benefits.output',
        string='Service Output',
        domain="[('id', 'in', available_outputs)]"
    )



    @api.depends('service_cats')
    def _compute_available_outputs(self):
        for record in self:
            if record.service_cats:
                record.available_outputs = record.service_cats.output_ids.ids
            else:
                record.available_outputs = []

    @api.onchange('service_cats')
    def _onchange_service_cats(self):
        if self.service_cats:
            if self.service_output and self.service_output not in self.service_cats.output_ids:
                self.service_output = False
        else:
            self.service_output = False

    @api.depends('date', 'service_id.sla_duration', 'service_id.sla_unit')
    def _compute_deadline(self):
        for rec in self:
            if rec.date and rec.service_id:
                delta = timedelta(hours=rec.service_id.sla_duration) if rec.service_id.sla_unit == 'hours' else timedelta(days=rec.service_id.sla_duration)
                rec.deadline = rec.date + delta


    @api.model
    def check_sla_deadlines(self):
        now = fields.Datetime.now()
        requests = self.search([('state', 'in', ['draft']), ('deadline', '<', now), ('escalated', '=', False)])

        managers_group = self.env.ref("odex_benefit.group_benefit_manager")
        employees = self.env["hr.employee"].search([("user_id", "in", managers_group.users.ids)])

        for req in requests:
            if req.service_id.auto_cancelled:
                req.escalated = True
                req.state = 'refused'
                req.message_post(body=_("The request was refused due to SLA timeout."))

                template = self.env.ref("service_sla.mail_template_sla_cancel")
                for emp in employees:
                    if emp.work_email:
                        template.with_context(employee_name=emp.name).send_mail(
                            req.id,
                            email_values={"email_to": emp.work_email},
                            force_send=True,
                            notif_layout="mail.mail_notification_light",
                        )
                        req.message_post(body=_("Cancellation notification sent to %(name)s (%(email)s)") % {
                            "name": emp.name, "email": emp.work_email
                        })
                req.sent_notification = True

            else:
                if not req.escalated:
                    req.escalated = True
                    req.message_post(
                        body=_("The request SLA has been breached and is escalated to the Service Manager."))

                    template = self.env.ref("service_sla.mail_template_sla_escalation")
                    for emp in employees:
                        if emp.work_email:
                            template.with_context(employee_name=emp.name).send_mail(
                                req.id,
                                email_values={"email_to": emp.work_email},
                                force_send=True,
                                notif_layout="mail.mail_notification_light",
                            )
                            req.message_post(body=_("Escalation notification sent to %(name)s (%(email)s)") % {
                                "name": emp.name, "email": emp.work_email
                            })
                    req.sent_notification = True
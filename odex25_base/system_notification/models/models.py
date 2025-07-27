# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime


class BaseAutomation(models.Model):
    _inherit = 'base.automation'
     # add new optine send notify
    send_notify = fields.Boolean(string='Send Notify',help="Send Notifications Within The System")
    notify_title = fields.Char(
        string='Notification Title',related='model_id.name')
    notify_note = fields.Char(
        string='Notification Note')
    notify_summary = fields.Char(
        string='Notification Message')
    # end option
    notify_to_groups_ids = fields.Many2many(comodel_name='res.groups',
                                            relation='automation_notifications_to_groups_rel',
                                            string='TO Notify Groups')

    notify_cc_groups_ids = fields.Many2many(comodel_name='res.groups',
                                            relation='automation_notifications_cc_groups_rel',
                                            string='CC Notify Groups')

    """ TO HR Modules Notification Depend on (Employee Id) only"""
    hr_notifys = fields.Boolean(string='HR Notifys',help="Send Notifications HR Moduls Depend on (Employee Id) only")
    direct_manager_notify = fields.Boolean(string='Direct Manager Notify',
                            help="Send Notification To The Employee's Direct Manager Only")
    department_manager_notify = fields.Boolean(string='Department Manager Notify',
                            help="Send Notification To The Department Manager For The Employee Only")

    employee_notify = fields.Boolean(string='Employee Notify',
                            help="Send Notification To The Employee Only")
    ceo_notify = fields.Boolean(string='CEO Manager',
                            help="Send Notification To The CEO Manager Only")

    hr_manager_notify = fields.Boolean(string='HR Manager',
                            help="Send Notification To The HR Manager Only")
    hr_email_notify = fields.Boolean(string='HR E-Mail',
                            help="Send Notification To The HR E-Mail Only")

    services_manager_id = fields.Boolean(string='Services Manager',
                            help="Send Notification To The Services Manager Only")

    it_manager_id = fields.Boolean(string='IT Manager',
                            help="Send Notification To The IT Manager Only")

    admin_manager_id = fields.Boolean(string='Admin Affairs Manager',
                            help="Send Notification To The Admin Affairs Manager Only")

    financial_manager_id = fields.Boolean(string='Financial Manager',
                            help="Send Notification To The Financial Manager Only")

    cyber_security_id = fields.Boolean(string='Cyber ​​Security',
                            help="Send Notification To The Cyber ​​Security Only")

    def has_access(self, user_id, record, mode='read'):
        try:
            record.with_user(user_id).check_access_rule(mode)
            return True
        except:
            return False
        return False

    def access_users(self, groups, record):
        users = []
        for group in groups:
            for user in group.users:
                if user.partner_id.email not in users and self.has_access(user_id=user.id, record=record, mode='read') and user.partner_id.email:
                    if self.hr_notifys:
                       """ TO HR Modules Notification Depend on (Employee Id) only"""
                       hr_mail = record.employee_id.sudo().company_id.hr_email
                       if self.direct_manager_notify :
                          if user.id == record.employee_id.sudo().parent_id.user_id.id:
                             users.append(user.partner_id.email)
                       if self.department_manager_notify:
                          if user.id == record.employee_id.sudo().coach_id.user_id.id:
                             users.append(user.partner_id.email)
                       if self.employee_notify:
                          if user.id == record.employee_id.sudo().user_id.id:
                             users.append(user.partner_id.email)
                       if self.ceo_notify:
                          if user.id == record.employee_id.sudo().company_id.general_supervisor_id.user_id.id:
                             users.append(user.partner_id.email)
                       if self.hr_manager_notify:
                          if user.id == record.employee_id.sudo().company_id.hr_manager_id.user_id.id:
                             users.append(user.partner_id.email)
                       if self.services_manager_id:
                          if user.id == record.employee_id.sudo().company_id.services_manager_id.user_id.id:
                             users.append(user.partner_id.email)
                       if self.it_manager_id:
                          if user.id == record.employee_id.sudo().company_id.it_manager_id.user_id.id:
                             users.append(user.partner_id.email)
                       if self.admin_manager_id:
                          if user.id == record.employee_id.sudo().company_id.admin_manager_id.user_id.id:
                             users.append(user.partner_id.email)
                       if self.financial_manager_id:
                          if user.id == record.employee_id.sudo().company_id.financial_manager_id.user_id.id:
                             users.append(user.partner_id.email)
                       if self.cyber_security_id:
                          if user.id == record.employee_id.sudo().company_id.cyber_security_id.user_id.id:
                             users.append(user.partner_id.email)
                       if self.hr_email_notify and hr_mail not in users:
                          users.append(hr_mail)
                    else:
                       users.append(user.partner_id.email)
        return ",".join(users)
     # todo start to add  method return access users ids list 
    def access_users_ids(self, groups, record):
        # partner_ids = set()
        processed_users = set()
        for group in groups:
            for user in group.users:
                if user.id not in processed_users and self.has_access(user_id=user.id, record=record, mode='read'):
                    if self.hr_notifys:
                       """ TO HR Modules Notification Depend on (Employee Id) only"""
                       if self.direct_manager_notify :
                          if user.id == record.employee_id.sudo().parent_id.user_id.id:
                             processed_users.add(user.id)
                       if self.department_manager_notify:
                          if user.id == record.employee_id.sudo().coach_id.user_id.id:
                             processed_users.add(user.id)
                       if self.employee_notify:
                          if user.id == record.employee_id.sudo().user_id.id:
                             processed_users.add(user.id)
                       if self.ceo_notify:
                          if user.id == record.employee_id.sudo().company_id.general_supervisor_id.user_id.id:
                             processed_users.add(user.id)
                       if self.hr_manager_notify:
                          if user.id == record.employee_id.sudo().company_id.hr_manager_id.user_id.id:
                             processed_users.add(user.id)
                       if self.services_manager_id:
                          if user.id == record.employee_id.sudo().company_id.services_manager_id.user_id.id:
                             processed_users.add(user.id)
                       if self.it_manager_id:
                          if user.id == record.employee_id.sudo().company_id.it_manager_id.user_id.id:
                             processed_users.add(user.id)
                       if self.admin_manager_id:
                          if user.id == record.employee_id.sudo().company_id.admin_manager_id.user_id.id:
                             processed_users.add(user.id)
                       if self.financial_manager_id:
                          if user.id == record.employee_id.sudo().company_id.financial_manager_id.user_id.id:
                             processed_users.add(user.id)
                       if self.cyber_security_id:
                          if user.id == record.employee_id.sudo().company_id.cyber_security_id.user_id.id:
                             processed_users.add(user.id)
                    # partner_ids.add(user.partner_id.id)
                    else:
                       processed_users.add(user.id)
        return list(processed_users)

    # def access_partner_ids(self, groups, record):
    #     partner_ids = []
    #     for group in groups:
    #         for user in group.users:
    #             if self.has_access(user_id = user.id, record=record, mode='read'):
    #                 partner_ids.append(user.partner_id.id)
    #     return partner_ids
    # todo end
    def get_notify_message(self,record):
        user_ids = self.access_users_ids(self.notify_to_groups_ids, record)
        today = datetime.today() 
        for user in user_ids:
             #record.activity_schedule('mail.mail_activity_todo', user_id=user,)
             data = {
                'res_id': record.id,
                'res_model_id': self.env['ir.model'].search([('model', '=', record._name)]).id,
                'user_id': user,
                'summary': _(self.template_id.name),
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'date_deadline': today
                }
             self.env['mail.activity'].create(data)

        """ TO HR Modules Notification Depend on (Employee Id) only,
            if not email Send TO HR Manager Mail"""
        if self.hr_notifys:
           if not user_ids and self.notify_to_groups_ids:
              hr_manager_user = record.employee_id.sudo().company_id.hr_manager_id.user_id.id
              #record.activity_schedule('mail.mail_activity_todo', user_id=hr_manager_user,)
              data = {
                'res_id': record.id,
                'res_model_id': self.env['ir.model'].search([('model', '=', record._name)]).id,
                'user_id': hr_manager_user,
                'summary': _(self.template_id.name),
                'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                'date_deadline': today
                }
              self.env['mail.activity'].create(data)

            # notification_ids = [(0, 0, {'res_partner_id': p,'notification_type': 'inbox'})]
            # self.env['mail.message'].sudo().create({
            #     'message_type': 'notification',
            #     'body': self.notify_note,
            #     'subject':self.notify_summary,
            #     'model': record._name,
            #     'res_id': record.id,
            #     'partner_ids': partner_ids,
            #     'notification_ids': notification_ids,
            # })
            #end notify method

    def get_mail_to(self, record):
        users = self.access_users(self.notify_to_groups_ids, record)
        if self.hr_notifys:
           """ TO HR Modules Notification Depend on (Employee Id) only,
               if not email Send TO HR Manager Mail"""
           if not users and self.notify_to_groups_ids:
              hr_manager_mail = record.employee_id.sudo().company_id.hr_manager_id.user_id.partner_id.email
              users = hr_manager_mail 
        return users

    def get_mail_cc(self, record):
        users = self.access_users(self.notify_cc_groups_ids, record)
        if self.hr_notifys:
           """ TO HR Modules Notification Depend on (Employee Id) only,
               If not Email CC Send to HR Mail"""
           if not users and self.notify_cc_groups_ids:
              hr_mail = record.employee_id.sudo().company_id.hr_email
              users = hr_mail
        return users


class ServerActions(models.Model):
    """ Add email option in server actions. """
    _inherit = 'ir.actions.server'

    # def _run_action_email(self, eval_context=None):
    #     print(self._context)
    #     print(eval_context)
    #     # TDE CLEANME: when going to new api with server action, remove action
    #     if not self.template_id or not self._context.get('active_id') or self._is_recompute():
    #         return False
    #     # Clean context from default_type to avoid making attachment
    #     # with wrong values in subsequent operations
    #     action_server_id = self.env['base.automation'].search([('action_server_id','=',self.id)])
    #     cleaned_ctx = dict(self.env.context)
    #     cleaned_ctx.pop('default_type', None)
    #     cleaned_ctx.pop('default_parent_id', None)
    #     template_values = {
    #             'email_to': action_server_id.get_mail_to(None),
    #             'email_cc': action_server_id.get_mail_cc(None),
    #         }
    #     self.template_id.write(template_values)
    #     self.template_id.with_context(cleaned_ctx).send_mail(self._context.get('active_id'), force_send=True,
    #                                                          raise_exception=False)
    #     return False
    @api.model
    def _run_action_email(self, eval_context=None):
        # add automated actions users from groups

        # if not action.template_id or not self._context.get('active_id'):
        #     return False
        if self._context.get('__action_done'):
            automations = self._context.get('__action_done')
            automation = list(automations.keys())[0]
            record = automations[automation]
            action = automation.action_server_id
            old_email_to = action.template_id.email_to
            old_email_cc = action.template_id.email_cc
            template_values = {
                'email_to': automation.get_mail_to(record),
                'email_cc': automation.get_mail_cc(record),
            }
            action.template_id.write(template_values)
            # super(ServerActions, self)._run_action_email(eval_context=eval_context)
            cleaned_ctx = dict(self.env.context)
            cleaned_ctx.pop('default_type', None)
            cleaned_ctx.pop('default_parent_id', None)
            action.template_id.with_context(cleaned_ctx).send_mail(record.id, force_send=True,
                notif_layout="system_notification.mail_notification_odex",
                                                                 raise_exception=False)
            old_template_values = {
                'email_to': old_email_to,
                'email_cc': old_email_cc,
            }
            action.template_id.write(old_template_values)
            if automation.send_notify:
                automation.get_notify_message(record)
            return False
        return super(ServerActions, self)._run_action_email(eval_context=eval_context)


class MailActivity(models.Model):
    _inherit = 'mail.activity'
    # copy function form odoo same name send other template (email_layout_xmlid) 
    def action_notify(self):
        if not self:
            return
        original_context = self.env.context
        body_template = self.env.ref('mail.message_activity_assigned')
        for activity in self:
            if activity.user_id.lang:
                # Send the notification in the assigned user's language
                self = self.with_context(lang=activity.user_id.lang)
                body_template = body_template.with_context(lang=activity.user_id.lang)
                activity = activity.with_context(lang=activity.user_id.lang)
            model_description = self.env['ir.model']._get(activity.res_model).display_name
            body = body_template._render(
                dict(
                    activity=activity,
                    model_description=model_description,
                    access_link=self.env['mail.thread']._notify_get_action_link('view', model=activity.res_model, res_id=activity.res_id),
                ),
                engine='ir.qweb',
                minimal_qcontext=True
            )
            record = self.env[activity.res_model].browse(activity.res_id)
            if activity.user_id:
                record.message_notify(
                    partner_ids=activity.user_id.partner_id.ids,
                    body=body,
                    subject=_('%(activity_name)s: %(summary)s assigned to you',
                        activity_name=activity.res_name,
                        summary=activity.summary or activity.activity_type_id.name),
                    record_name=activity.res_name,
                    model_description=model_description,
                    email_layout_xmlid='system_notification.mail_notification_odex',# change
                    #email_layout_xmlid='mail.mail_notification_light',
                )
            body_template = body_template.with_context(original_context)
            self = self.with_context(original_context)

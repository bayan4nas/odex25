# -*- coding: utf-8 -*-

from odoo import models, fields, api


class BaseAutomation(models.Model):
    _inherit = 'base.automation'
     # add new optine send notify
    send_notify = fields.Boolean(string='Send Notify')
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
                if self.has_access(user_id=user.id, record=record, mode='read') and user.partner_id.email:
                    users.append(user.partner_id.email)
        return ",".join(users)
     # todo start to add  method return access users ids list
    def access_users_ids(self, groups, record):
        # partner_ids = set()
        processed_users = set()
        for group in groups:
            for user in group.users:
                if user.id not in processed_users and self.has_access(user_id=user.id, record=record, mode='read'):
                    # partner_ids.add(user.partner_id.id)
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
        for user in user_ids:
             record.activity_schedule('mail.mail_activity_todo', user_id=user,)

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
    #         end notify method

    def get_mail_to(self, record):
        users = self.access_users(self.notify_to_groups_ids, record)
        return users

    def get_mail_cc(self, record):
        users = self.access_users(self.notify_cc_groups_ids, record)
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
                notif_layout="mail.mail_notification_light",
                                                                 raise_exception=False)
            old_template_values = {
                'email_to': old_email_to,
                'email_cc': old_email_cc,
            }
            action.template_id.write(old_template_values)
            if automation.send_notify:
                print('true send....')
                automation.get_notify_message(record)
            return False
        return super(ServerActions, self)._run_action_email(eval_context=eval_context)

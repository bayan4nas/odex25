# -*- coding: utf-8 -*-
from odoo import api, models, fields, _


class ForwardTransactionWizard(models.TransientModel):
    _name = 'forward.transaction.wizard'

    forward_type = fields.Selection(selection=[('unit','Internal Unit'), ('employee','Employee')],string="Forward Type",
                                    required=True)
    internal_unit = fields.Many2one('cm.entity', string='Internal Unit')
    employee = fields.Many2one('cm.entity', string='Employee')
    to_delegate = fields.Boolean(string='To Delegate?', related='employee.to_delegate')
    cc_ids = fields.Many2many(comodel_name='cm.entity', string='CC To')
    note = fields.Text(string="Notes")
    description = fields.Text(string="Description")
    date = fields.Date(string='Date', default=fields.Date.today)
    is_secret = fields.Boolean('Is Secret?')
    secret_reason = fields.Text(string="Secret Description")
    procedure_id = fields.Many2one(comodel_name='cm.procedure', string='Procedure')
    internal_transaction_id = fields.Many2one('internal.transaction', string='Internal')
    incoming_transaction_id = fields.Many2one('incoming.transaction', string='Outgoing')
    outgoing_transaction_id = fields.Many2one('outgoing.transaction', string='Incoming')
    forward_attachment_id = fields.Binary(attachment=True, string='Forward Attachment')
    filename = fields.Char()
    att_description = fields.Char(string='Attach Description')


    @api.onchange('internal_unit', 'forward_type')
    def _get_valid_employee_ids(self):
        for rec in self:
            domain = []
            if rec.forward_type == 'employee' and rec.internal_unit:
                domain = [('id', 'in', rec.env['cm.entity'].search([('type', '=', 'employee'), ('parent_id', '=', rec.internal_unit.id)]).ids)]
            rec.employee = False
            return {
                "domain": {
                    "employee": domain
                }
            }

    def action_forward(self):
        transaction = ''
        name = ''
        if self.to_delegate:
            self.employee = self.employee.delegate_employee_id.id
        to_id = self.employee.id
        if self.internal_transaction_id:
            transaction = self.internal_transaction_id
            name = 'internal_transaction_id'
        elif self.incoming_transaction_id:
            transaction = self.incoming_transaction_id
            name = 'incoming_transaction_id'
        elif self.outgoing_transaction_id:
            transaction = self.outgoing_transaction_id
            name = 'outgoing_transaction_id'
        forward_user_id = self.employee.user_id
        if self.forward_type != 'employee':
            forward_user_id = False
            to_id = self.internal_unit.id 
        transaction.forward_user_id = forward_user_id
        transaction.last_forwarded_user = self.env.uid
        if self.is_secret:
            transaction.secret_reason = self.secret_reason
            transaction.secret_forward_user = self.env['cm.entity'].search([('user_id', '=', forward_user_id.id)], limit=1)
        employee = transaction.current_employee()
        from_id = self.env['cm.entity'].search([('user_id', '=', self.env.uid)], limit=1)
        transaction.is_forward = True
        if self.forward_attachment_id:
            transaction.attachment_rule_ids.create({
                'file_save': self.forward_attachment_id,
                'name': transaction.id,
                'description': self.att_description,
                'attachment_filename': self.filename,
            })
        transaction.trace_ids.create({
            'action': 'forward',
            'to_id': to_id,
            'from_id': from_id.id,
            'procedure_id': self.procedure_id.id or False,
            'note': self.note,
            'cc_ids': [(6, 0, self.cc_ids.ids)],
            'name': transaction.id
        })
        if self.internal_transaction_id or self.incoming_transaction_id:
            transaction.action_send_forward()
        '''for notification partner in cc or forward user'''
        target = self.forward_type
        target_name = target == 'employee' and self.employee.name or self.internal_unit.name
        subj = _('Message Has been forwarded !')
        msg = _(u'{} &larr; {}').format(
            employee and employee.name or '#', target_name)
        msg = u'{}<br /><b>{}</b> {}.<br />{}'.format(msg,
                                                      _(u'Action Taken'), self.procedure_id.name,
                                                      u'<a href="%s" >رابط المعاملة</a> ' % (
                                                          transaction.get_url()))
        if name == 'internal_transaction_id' and transaction.current_entity_id :
            if transaction.current_entity_id.type == 'employee' :
                transaction.forward_user_ids = [(4, transaction.current_entity_id.user_id.id)]
            else  :
                transaction.forward_user_ids = [(4, s.user_id.id) for s in  transaction.current_entity_id.secretary_ids]
        transaction.sender_entity_id = transaction.current_entity_id.id
        # add mail notification
        partner_ids = []
        if self.forward_type == 'unit':
            forward_partner_id = self.internal_unit.secretary_id.user_id.partner_id.id or self.internal_unit.manager_id.user_id.partner_id.id
            partner_ids.append(forward_partner_id)
            transaction.current_entity_id = self.internal_unit.id
        elif self.forward_type == 'employee':
            partner_ids.append(self.employee.user_id.partner_id.id)
            transaction.current_entity_id = self.employee.id
        for partner in self.cc_ids:
            if partner.type == 'unit':
                partner_id = partner.secretary_id.user_id.partner_id.id or partner.manager_id.user_id.partner_id.id
                partner_ids.append(partner_id)
            elif partner.type == 'employee':
                partner_ids.append(partner.user_id.partner_id.id)
        transaction.state = 'send'
        user_id = transaction.env.user.id
        if user_id not in transaction.seen_user_ids.ids:
            transaction.seen_user_ids = [(6, 0, [user_id])]
        transaction.action_send_notification(subj, msg, partner_ids)
        if self.incoming_transaction_id:
            if transaction.state == 'draft':
                transaction.state = 'send'

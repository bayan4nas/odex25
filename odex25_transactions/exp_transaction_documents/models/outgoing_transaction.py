# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
from odoo.exceptions import ValidationError


class OutgoingTransaction(models.Model):
    _name = 'outgoing.transaction'
    _inherit = ['transaction.transaction', 'mail.thread']
    _description = 'outgoing Transaction'

    type_sender = fields.Selection(
        string='',
        selection=[('unit', 'Department'),
                   ('employee', 'Employee'),
                   ],
        required=False, default='unit')
    reason = fields.Text('Reason')
    last_sender_entity_id = fields.Many2one('cm.entity', compute="_compute_last_received_entity", store=True)
    last_received_entity_id = fields.Many2one('cm.entity', compute='_compute_last_received_entity', store=True)
    last_sender_label = fields.Char('From', compute="_compute_last_received_entity", store=True)

    transaction_type = fields.Selection([
        ('incoming', 'Incoming'),
        ('outgoing', 'Outgoing'),
    ], string='Type')
    attachment_rule_ids = fields.One2many('cm.attachment.rule', 'outgoing_transaction_id', string='Attaches')
    attachment_ids = fields.One2many('cm.attachment', 'outgoing_transaction_id', string='Attachments')
    trace_ids = fields.One2many('cm.transaction.trace', 'outgoing_transaction_id', string='Trace Log')
    is_partner = fields.Boolean()
    partner_id = fields.Many2one('res.partner')
    incoming_transaction_id = fields.Many2one('incoming.transaction', string='Related Incoming')
    # to_ids = fields.Many2one(comodel_name='cm.entity',string='Send To')
    # to_delegate = fields.Boolean(string='To Delegate?', related='to_ids.to_delegate')
    company_name = fields.Many2one('res.partner', string='Delivery Company')

    to_users = fields.Many2many(comodel_name='res.users', string="To Users", relation='your_out_to_users_rel',
                                column1='your_out_id', column2='user_id2', )

    tran_tag = fields.Many2many(comodel_name='transaction.tag', string='Tags')
    tran_tag_unit = fields.Many2many(comodel_name='transaction.tag', string='Business unit',
                                     relation='outgoing_tag_rel',
                                     column1='incoming_id'
                                     , column2='name')
    project_id = fields.Many2many('project.project')
    sale_order_id = fields.Many2one('sale.order', 'Proposal')
    to_name = fields.Char(string="Recipient")
    cc_ids = fields.Many2many(comodel_name='cm.entity', relation='outgoing_entity_cc_rel',
                              column1='outgoing_id', column2='entity_id', string='CC To')
    cc_users = fields.Many2many(comodel_name='res.users', string="CC Users", relation='your_com_to_users_rel',
                                column1='your_use_id', column2='user_id', store=True)

    processing_ids = fields.Many2many(comodel_name='outgoing.transaction', relation='transaction_outgoing_outgoing_rel',
                                      column1='transaction_id', column2='outgoing_id',
                                      string='Process Transactions outgoing')
    processing2_ids = fields.Many2many(comodel_name='incoming.transaction',
                                       relation='transaction_outgoing_incoming_rel',
                                       column1='transaction_id', column2='incoming_id',
                                       string='Process Transactions incoming')

    # processing_ids = fields.Many2many(comodel_name='transaction.transaction', relation='transaction_outgoing_rel',
    #                                   column1='transaction_id', column2='outgoing_id', string='Process Transactions')

    def _normalize_arabic_text(self, text):
        translation_map = str.maketrans({
            # Define a dictionary to replace different forms of characters
            'ه': 'ة',
            'إ': 'ا',  # Replace Alef with Hamza Below with Alef
            'أ': 'ا',  # Replace Alef with Hamza Above with Alef
            'آ': 'ا',  # Replace Alef with Madda Above with Alef
            'ى': 'ي',  # Replace Alef Maqsura with Ya
            'ئ': 'ي',
            'ؤ': 'و',

        })
        return text.translate(translation_map)

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        # Normalize the search arguments for 'name' field
        new_args = []
        for arg in args:
            if isinstance(arg, (list, tuple)) and arg[1] == 'ilike' and arg[0] in ('name', 'subject'):
                normalized_value = self._normalize_arabic_text(arg[2])
                new_args.append('|')
                new_args.append(arg)
                new_args.append((arg[0], 'ilike', normalized_value))
            else:
                new_args.append(arg)
        return super(OutgoingTransaction, self).search(new_args, offset=offset, limit=limit, order=order, count=count)

    @api.depends('trace_ids')
    def _compute_last_received_entity(self):
        sent = 'sent'
        for transaction in self:
            transaction.trace_create_ids('outgoing_transaction_id', transaction, sent)

            last_track = transaction.trace_ids.sorted('create_date', reverse=True)[:1]  # Get the last track
            print(last_track.to_id.name,'name')
            print(last_track.to_id,'nameaaaaaaaaaaaa')
            if last_track:
                transaction.last_received_entity_id = last_track.to_id.id
                transaction.last_sender_entity_id = last_track.from_id.id
                transaction.last_sender_label = last_track.from_label

            else:
                transaction.last_received_entity_id = False
                transaction.last_sender_entity_id = False
                transaction.last_sender_label = False

    @api.depends('attachment_rule_ids')
    def compute_attachment_num(self):
        for r in self:
            r.attachment_num = len(r.attachment_rule_ids)

    @api.model
    def get_url(self):
        url = u''
        action = self.env.ref(
            'exp_transaction_documents.outgoing_external_tran_action', False)
        Param = self.env['ir.config_parameter'].sudo()
        if action:
            return u'{}/web#id={}&action={}&model=outgoing.transaction'.format(
                Param.get_param('web.base.url', self.env.user.company_id.website), self.id, action.id)
        return url

    def fetch_sequence(self, data=None):
        """generate transaction sequence"""
        return self.env['ir.sequence'].next_by_code('cm.transaction.out') or _('New')

    ####################################################
    # Business methods
    ####################################################
    #
    #
    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise ValidationError(_('Cannot delete a sent transaction!'))
        return super(OutgoingTransaction, self).unlink()

    @api.onchange('type_sender')
    def _onchange_type_sender(self):
        self.ensure_one()
        if self.type_sender == 'unit' and self.to_ids and self.to_ids.type != 'unit':
            self.to_ids = False
            self.partner_id = False
        elif self.type_sender == 'employee' and self.to_ids and self.to_ids.type != 'employee':
            self.to_ids = False
            self.partner_id = False

    def action_draft(self):
        for record in self:
            res = super(OutgoingTransaction, self).action_draft()
            partner_ids = []
            if record.to_ids.type == 'unit':
                partner_ids.append(record.to_ids.secretary_id.user_id.partner_id.id)
                record.forward_user_id = record.to_ids.secretary_id.user_id.id
            elif record.to_ids.type == 'employee':
                partner_ids.append(record.to_ids.user_id.partner_id.id)
                record.forward_user_id = record.to_ids.user_id.id

            if record.to_user_have_leave:
                record.forward_user_id = record.receive_id.user_id.id
            subj = _('Message Has been send !')
            msg = _(u'{} &larr; {}').format(record.employee_id.name, record.to_ids.name)
            msg = u'{}<br /><b>{}</b> {}.<br />{}'.format(msg,
                                                          _(u'Action Taken'), record.procedure_id.name,
                                                          u'<a href="%s" >رابط المعاملة</a> ' % (
                                                              record.get_url()))

            self.action_send_notification(subj, msg, partner_ids)
            template = 'exp_transaction_documents.outgoing_notify_send_send_email'
            self.send_message(template=template)
            return res

    @api.depends('trace_ids')
    def _compute_replayed_entities(self):
        for transaction in self:
            existing_entity_ids = set(transaction.replayed_entity_ids.ids)  # Get already stored entity IDs
            new_entities = transaction.trace_ids.filtered(lambda t: t.action == 'reply').mapped('from_id.id')

            # Keep only unique values (combine existing and new)
            updated_entities = list(existing_entity_ids.union(set(new_entities)))

            # Update the Many2many field
            transaction.replayed_entity_ids = [(6, 0, updated_entities)] if updated_entities else [(5, 0, 0)]

    @api.depends('trace_ids')
    def _compute_forward_entities(self):
        for transaction in self:
            existing_entity_ids = set(transaction.forward_entity_ids.ids)  # Get already stored entity IDs
            new_entities = transaction.trace_ids.filtered(lambda t: t.action == 'forward').mapped('from_id.id')

            # Keep only unique values (combine existing and new)
            updated_entities = list(existing_entity_ids.union(set(new_entities)))

            # Update the Many2many field
            transaction.forward_entity_ids = [(6, 0, updated_entities)] if updated_entities else [(5, 0, 0)]

    def action_email(self):
        # todo#add email function here
        company_id = self.env.user.company_id
        if company_id.sms_active == True:
            test = company_id.send_sms("", "Test from odex!")
            test = test.text[:100].split("-")
            error = company_id.get_error_response(test[1])
        for rec in self:
            templates = 'exp_transaction_documents.out_email'
            template = self.env.ref(templates, False)
            emails = rec.partner_id.email if rec.is_partner else rec.to_ids.mapped('email')
            email_template = template.write(
                {'email_to': emails})
            template.with_context(lang=self.env.user.lang).send_mail(
                rec.id, force_send=True, raise_exception=False)

    def action_reject_outgoing(self):
        name = 'default_outgoing_transaction_id'
        return self.action_reject(name, self)

    def action_return_outgoing(self):
        name = 'default_outgoing_transaction_id'
        return self.action_return_tran(name, self)

    ####################################################
    # ORM Overrides methods
    ####################################################
    @api.model
    def create(self, vals):
        seq = self.fetch_sequence()
        if vals.get('preparation_id'):
            code = self.env['cm.entity'].sudo().browse(vals['preparation_id']).code
            x = seq.split('/')
            sequence = "%s/%s/%s" % (x[0], code, x[1])
            vals['name'] = sequence
        else:
            vals['name'] = seq
        # vals['ean13'] = self.env['odex.barcode'].code128('OT', vals['name'], 'TR')
        return super(OutgoingTransaction, self).create(vals)

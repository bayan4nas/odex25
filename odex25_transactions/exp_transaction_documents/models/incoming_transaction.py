# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
from odoo.exceptions import ValidationError
from datetime import datetime
from hijri_converter import convert, Hijri


class IncomingTransaction(models.Model):
    _name = 'incoming.transaction'
    _inherit = ['transaction.transaction', 'mail.thread']
    _description = 'incoming Transaction'

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
        return super(IncomingTransaction, self).search(new_args, offset=offset, limit=limit, order=order, count=count)

    # due_date = fields.Date(string='Deadline', compute='compute_due_date')
    from_id = fields.Many2one(comodel_name='cm.entity', string='Incoming From (External)')
    transaction_type = fields.Selection([
        ('incoming', 'Incoming'),
        ('outgoing', 'Outgoing'),
    ], string='Type')
    partner_id = fields.Many2one('res.partner', string='Partner', readonly=True,
                                 related='to_ids.secretary_id.partner_id')
    outgoing_transaction_id = fields.Many2one('outgoing.transaction', string='Related Outgoing')
    incoming_number = fields.Char(string='Incoming Number')
    incoming_date = fields.Date(string='Incoming Date', default=fields.Date.today)
    type_sender = fields.Selection(
        string='',
        selection=[('unit', 'Department'),
                   ('employee', 'Employee'),
                   ],
        required=False, default='unit')
    incoming_date_hijri = fields.Char(string='Incoming Date (Hijri)', compute='_compute_incoming_date_hijri')
    attachment_rule_ids = fields.One2many('cm.attachment.rule', 'incoming_transaction_id', string='Attaches')
    attachment_ids = fields.One2many('cm.attachment', 'incoming_transaction_id', string='Attachments')
    trace_ids = fields.One2many('cm.transaction.trace', 'incoming_transaction_id', string='Trace Log')
    # to_ids = fields.Many2one(comodel_name='cm.entity',string='Send To')
    # to_delegate = fields.Boolean(string='To Delegate?', related='to_ids.to_delegate')
    forward_entity_ids = fields.Many2many('cm.entity', 'incoming_trans_forward_entity_rel', 'transaction_id', 'user_id',
                                          compute="_compute_forward_entities", store=True)
    cc_ids = fields.Many2many(comodel_name='cm.entity', relation='incoming_entity_cc_rel',
                              column1='incoming_id', column2='entity_id', string='CC To', )

    tran_tag = fields.Many2many(comodel_name='transaction.tag', string='Tags')
    tran_tag_unit = fields.Many2many(comodel_name='transaction.tag', string='Business unit',
                                     relation='incoming_tag_rel',
                                     column1='incoming_id'
                                     , column2='name')
    project_id = fields.Many2many('project.project')
    sale_order_id = fields.Many2one('sale.order', 'Proposal')
    processing_ids = fields.Many2many(comodel_name='incoming.transaction', relation='transaction_incoming_incoming_rel',
                                      column1='transaction_id', column2='incoming_id',
                                      string='Process Transactions incoming')
    processing2_ids = fields.Many2many(comodel_name='outgoing.transaction',
                                       relation='transaction_incoming_outgoing_rel',
                                       column1='transaction_id', column2='outgoing_id',
                                       string='Process Transactions Outgoing')
    attachment_count = fields.Integer(compute='count_attachments')
    last_sender_entity_id = fields.Many2one('cm.entity', compute="_compute_last_received_entity", store=True)
    last_received_entity_id = fields.Many2one('cm.entity', compute='_compute_last_received_entity', store=True)
    last_sender_label = fields.Char('Last sender label', compute="_compute_last_received_entity", store=True)
    datas = fields.Binary(string="", related='send_attach.datas')
    replayed_entity_ids = fields.Many2many('cm.entity', compute="_compute_replayed_entities", store=True)

    @api.depends('trace_ids')
    def _compute_forward_entities(self):
        for transaction in self:
            existing_entity_ids = set(transaction.forward_entity_ids.ids)  # Get already stored entity IDs
            new_entities = transaction.trace_ids.filtered(lambda t: t.action == 'forward').mapped('from_id.id')

            # Keep only unique values (combine existing and new)
            updated_entities = list(existing_entity_ids.union(set(new_entities)))

            # Update the Many2many field
            transaction.forward_entity_ids = [(6, 0, updated_entities)] if updated_entities else [(5, 0, 0)]

    @api.depends('trace_ids')
    def _compute_replayed_entities(self):
        for transaction in self:
            existing_entity_ids = set(transaction.replayed_entity_ids.ids)  # Get already stored entity IDs
            new_entities = transaction.trace_ids.filtered(lambda t: t.action == 'reply').mapped('from_id.id')

            # Keep only unique values (combine existing and new)
            updated_entities = list(existing_entity_ids.union(set(new_entities)))

            # Update the Many2many field
            transaction.replayed_entity_ids = [(6, 0, updated_entities)] if updated_entities else [(5, 0, 0)]

    @api.onchange('type_sender')
    def _onchange_type_sender(self):
        self.ensure_one()
        if self.type_sender == 'unit' and self.to_ids and self.to_ids.type != 'unit':
            self.to_ids = False
            self.partner_id = False
        elif self.type_sender == 'employee' and self.to_ids and self.to_ids.type != 'employee':
            self.to_ids = False
            self.partner_id = False

    @api.depends('trace_ids')
    def _compute_last_received_entity(self):
        for transaction in self:
            last_track = transaction.trace_ids.sorted('create_date', reverse=True)[:1]  # Get the last track
            if last_track:
                transaction.last_received_entity_id = last_track.to_id.id
                transaction.last_sender_entity_id = last_track.from_id.id
                transaction.last_sender_label = last_track.from_label
                transaction.cm_subject = last_track.procedure_id
            else:
                transaction.last_received_entity_id = False
                transaction.last_sender_entity_id = False
                transaction.last_sender_label = False

    def count_attachments(self):
        obj_attachment = self.env['ir.attachment']
        for record in self:
            record.attachment_count = 0
            attachment_ids = obj_attachment.search(
                [('res_model', '=', 'incoming.transaction'), ('res_id', '=', record.id)])
            first_file = []
            if attachment_ids:
                first_file.append(attachment_ids[0].id)
                # print(first_file)
                # record.attachment_file = first_file
            record.attachment_count = len(attachment_ids)

    @api.model
    def get_url(self):
        url = u''
        action = self.env.ref(
            'exp_transaction_documents.forward_incoming_external_tran_action', False)
        Param = self.env['ir.config_parameter'].sudo()
        if action:
            return u'{}/web#id={}&action={}&model=incoming.transaction'.format(
                Param.get_param('web.base.url', self.env.user.company_id.website), self.id, action.id)
        return url

    @api.depends('incoming_date')
    def _compute_incoming_date_hijri(self):
        for rec in self:
            if rec.incoming_date:
                gregorian_date = fields.Date.from_string(rec.incoming_date)
                hijri_date = convert.Gregorian(gregorian_date.year, gregorian_date.month, gregorian_date.day).to_hijri()
                rec.incoming_date_hijri = hijri_date
            else:
                rec.incoming_date_hijri = ''

    @api.depends('attachment_rule_ids')
    def compute_attachment_num(self):
        for r in self:
            r.attachment_num = len(r.attachment_rule_ids)

    def fetch_sequence(self):
        '''generate transaction sequence'''
        return self.env['ir.sequence'].next_by_code('cm.transaction.in') or _('New')

    def action_draft(self):
        sent = 'sent'
        for record in self:
            record.trace_create_ids('incoming_transaction_id', record, sent)
            res = super(IncomingTransaction, self).action_draft()
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
            template = 'exp_transaction_documents.incoming_notify_send_send_email'
            self.send_message(template=template)
            return res

    def action_send_forward(self):
        template = 'exp_transaction_documents.incoming_notify_send_send_email'
        self.send_message(template=template)

    def action_reply_internal(self):
        name = 'default_incoming_transaction_id'
        return self.action_reply_tran(name, self)

    def action_forward_incoming(self):
        name = 'default_incoming_transaction_id'
        return self.action_forward_tran(name, self)

    def action_archive_incoming(self):
        name = 'default_incoming_transaction_id'
        return self.action_archive_tran(name, self)

    ####################################################
    # ORM Overrides methods
    ####################################################
    @api.model
    def create(self, vals):
        seq = self.fetch_sequence()
        if vals['preparation_id']:
            code = self.env['cm.entity'].browse(vals['preparation_id']).code
            x = seq.split('/')
            sequence = "%s/%s/%s" % (x[0], code, x[1])
            vals['name'] = sequence
        else:
            vals['name'] = seq
        vals['ean13'] = self.env['odex.barcode'].code128('IN', vals['name'], 'TR')
        return super(IncomingTransaction, self).create(vals)
    #
    #
    # def unlink(self):
    #     if self.env.uid != 1:
    #         raise ValidationError(_("You can not delete transaction....."))
    #     return super(IncomingTransaction, self).unlink()

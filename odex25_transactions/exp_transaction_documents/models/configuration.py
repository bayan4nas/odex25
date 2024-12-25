# -*- coding: utf-8 -*-
from odoo import models, api, fields, _
import base64
from odoo.exceptions import ValidationError,UserError
TRACE_ACTIONS = [
    ('forward', _('Forwarded')),
    ('receive', _('Received')),
    ('archive', _('Archived')),
    ('approve', _('Unit Manager Approved')),
    ('ceo_approve', _('CEO Approved')),
    ('sent', _('Sent')),
    ('return', _('Returned')),
    ('action', _('Action Taken')),
    ('refuse', _('Refused')),
    ('reply', _('Replied')),
    ('waite', _('Waiting Approve')),
    ('reopen', _('Reopened')),
]


class SubjectType(models.Model):
    _name = 'cm.subject.type'
    _order = 'sequence'

    name = fields.Char(string='Transaction Type')
    sequence = fields.Integer(string='Sequence', default=5)
    second_approval = fields.Boolean(string='Second Approval ?',
                                     help='Check if this transaction type need a second (CEO) Approval.', default=True)
    transaction_need_approve = fields.Boolean(string="Transaction need approve")
    tran_tag = fields.Many2many(comodel_name='transaction.tag', string='Tags')


class ImportantDegree(models.Model):
    _name = 'cm.transaction.important'

    name = fields.Char(string='Important Degree')
    rank = fields.Integer(string='Transaction Rank')


class Procedure(models.Model):
    _name = 'cm.procedure'

    name = fields.Char(string='Procedure Name')


class AttachmentType(models.Model):
    _name = 'cm.attachment.type'

    sequence = fields.Integer(string='Sequence', default=1)
    name = fields.Char(string='Name')


class Attachment(models.Model):
    _name = 'cm.attachment'

    name = fields.Char(string='Description')
    num_page = fields.Integer(string='No. Pages')
    type_id = fields.Many2one('cm.attachment.type', string='Attachment type')
    incoming_transaction_id = fields.Many2one(comodel_name='incoming.transaction', string='Incoming Transaction')
    internal_transaction_id = fields.Many2one(comodel_name='internal.transaction', string='Internal Transaction')
    outgoing_transaction_id = fields.Many2one(comodel_name='outgoing.transaction', string='Outgoing Transaction')


class ArchiveType(models.Model):
    _name = 'cm.archive.type'

    name = fields.Char(string='Archive Type')


class AttachmentRule(models.Model):
    _name = 'cm.attachment.rule'

    def _default_employee_id(self):
        user = self.env.user
        em = self.env['cm.entity'].search([('user_id', '=', user.id)], limit=1)
        return len(em) and em or self.env['cm.entity']

    name = fields.Char()
    employee_id = fields.Many2one(comodel_name='cm.entity', string='Created By',
                                  default=lambda self: self._default_employee_id(), readonly="True")
    entity_id = fields.Many2one(comodel_name='cm.entity', string='Unit Responsible', related='internal_transaction_id.preparation_id.manager_id',
                                store=True)
    file_save = fields.Many2many('ir.attachment', String="Save File")
    external_drive_link = fields.Text('External Drive Link')
    attachment_filename = fields.Char(string="Attachment Filename")
    incoming_transaction_id = fields.Many2one(comodel_name='incoming.transaction', string='Incoming Transaction')
    internal_transaction_id = fields.Many2one(comodel_name='internal.transaction', string='Internal Transaction')
    outgoing_transaction_id = fields.Many2one(comodel_name='outgoing.transaction', string='Outgoing Transaction')
    date = fields.Datetime(string='Date', default=fields.Datetime.now)
    description = fields.Char(string='Description')
    signed = fields.Boolean(string='Signed',readonly=True)

    def action_signature(self):
        for rec in self:
            x = self.env['letters.letters'].search([('internal_transaction_id','=',rec.internal_transaction_id.id)],limit=1)
            return {
                'type': 'ir.actions.act_window',
                'name': 'Preferences',
                'res_model': 'res.users',
                'view_mode': 'form',
                'view_id': self.env.ref('base.view_users_form_simple_modif').id,
                'target': 'new',
                'context': {
                'default_id': self.env.user.id,
                'default_letter_id': x.id ,
                'default_attachment_id': rec.id,
            },
            'res_id': self.env.user.id,
            }


    # @api.constrains('file_save')
    # def _check_attachment_size(self):
    #     max_size = 4 * 1024 * 1024  # 4 MB
    #     for record in self:
    #         if record.file_save:
    #             file_size = len(base64.b64decode(record.file_save))
    #             if file_size > max_size:
    #                 raise ValidationError(_('Attachment %s exceeds the maximum allowed size of 4 MB.') % record.attachment_filename)
    
    # @api.onchange('file_save')
    # def _onchange_file_save(self):
    #     max_size = 4 * 1024 * 1024  # 4 MB
    #     for record in self:
    #         if record.file_save:
    #             file_size = len(base64.b64decode(record.file_save))
    #             if file_size > max_size:
    #                 record.file_save = False
    #                 raise UserError(_('Attachment %s exceeds the maximum allowed size of 4 MB.') % record.attachment_filename)

class TransactionTrace(models.Model):
    _name = 'cm.transaction.trace'
    _description = 'Transaction Trace'
    _order = 'date desc'

    action = fields.Selection(string='Action', selection=TRACE_ACTIONS, default='forward')
    incoming_transaction_id = fields.Many2one(comodel_name='incoming.transaction', string='Incoming Transaction')
    internal_transaction_id = fields.Many2one(comodel_name='internal.transaction', string='Internal Transaction')
    outgoing_transaction_id = fields.Many2one(comodel_name='outgoing.transaction', string='Outgoing Transaction')
    date = fields.Datetime(string='Date', default=fields.Datetime.now)
    from_id = fields.Many2one(comodel_name='cm.entity', string='From')
    to_id = fields.Many2one(comodel_name='cm.entity', string='To')
    procedure_id = fields.Many2one(comodel_name='cm.procedure', string='Action Taken')
    note = fields.Char(string='Notes')
    archive_type_id = fields.Many2one(comodel_name='cm.archive.type', string='Archive Type')
    cc_ids = fields.Many2many('cm.entity', string='CC To')


class ProjectType(models.Model):
    _name = "project.type"

    name = fields.Char(string='Name')
    sequence = fields.Integer(string='Sequence', default=1)


class TransactionCategory(models.Model):
    _name = 'transaction.tag'

    name = fields.Char("Name")

# -*- coding: utf-8 -*-
import base64
from odoo import api, fields, models
from hijri_converter import convert
import datetime


class Letters(models.Model):
    _name = "letters.letters"

    name = fields.Char(string="Name")
    unite = fields.Many2one('cm.entity', string="Unite")
    letter_template = fields.Many2one('letters.template', string='Template')
    date = fields.Date(string="Date")
    hijir_date = fields.Char(string="Hijir Date", compute='compute_hijri')
    content = fields.Html(string="Content")
    signature = fields.Binary("Signature image",compute='compute_img',store=True)
    is_sign = fields.Boolean(string='Is Sign',readonly=True)
    new_signature = fields.Binary("Signature image",readonly=True)
    transaction_type = fields.Selection([('internal', 'Internal'), ('outgoing', 'Outgoing'),
                                         ('incoming', 'Incoming')], default='internal', string='Transaction Type')
    incoming_transaction_id = fields.Many2one(comodel_name='incoming.transaction', string='Incoming Transaction')
    internal_transaction_id = fields.Many2one(comodel_name='internal.transaction', string='Internal Transaction')
    outgoing_transaction_id = fields.Many2one(comodel_name='outgoing.transaction', string='Outgoing Transaction')
    attachment_generated = fields.Boolean()
    signed_user_id = fields.Many2one('res.users')


    @api.depends('transaction_type','name')
    def compute_img(self):
        employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
        if employee_id:
            entity  = self.env['cm.entity'].search([('type','=','employee'),('employee_id', '=',employee_id.id)], limit=1)
            for rec in self:
                rec.signature = entity.image

    @api.onchange('transaction_type')
    def set_value_false(self):
        if self.transaction_type == 'internal':
            self.incoming_transaction_id = ''
            self.outgoing_transaction_id = ''
        elif self.transaction_type == 'outgoing':
            self.incoming_transaction_id = ''
            self.internal_transaction_id = ''
        elif self.transaction_type == 'incoming':
            self.internal_transaction_id = ''
            self.outgoing_transaction_id = ''
        elif not self.transaction_type:
            self.incoming_transaction_id = ''
            self.internal_transaction_id = ''
            self.outgoing_transaction_id = ''

    @api.depends('date')
    def compute_hijri(self):
        for rec in self:
            if rec.date:
                date = datetime.datetime.strptime(str(rec.date), '%Y-%m-%d')
                year = date.year
                day = date.day
                month = date.month
                hijri_date = convert.Gregorian(year, month, day).to_hijri()
                rec.hijir_date = hijri_date

            else:
                rec.hijir_date = False

    @api.onchange('letter_template')
    def get_content(self):
        for rec in self:
            final_content = rec.letter_template.introduction + rec.letter_template.content + rec.letter_template.conclusion
            if final_content:
                final_content = final_content.replace('line-height', '')
                rec.content = final_content

    def action_generate_attachment(self):
        """ this method called from button action in view xml """
        # generate pdf from report, use report's id as reference
        REPORT_ID = 'exp_transation_letters.report_letter_action_report'
        pdf = self.env.ref(REPORT_ID)._render_qweb_pdf(self.ids)
        # pdf result is a list
        b64_pdf = base64.b64encode(pdf[0])
        res_id = ''
        field_name = 'internal_transaction_id'
        if self.transaction_type == 'internal':
            res_id = self.internal_transaction_id.id
            field_name = 'internal_transaction_id'
        elif self.transaction_type == "outgoing":
            res_id = self.outgoing_transaction_id.id
            field_name = 'outgoing_transaction_id'
        elif self.transaction_type == "incoming":
            res_id = self.incoming_transaction_id.id
            field_name = 'incoming_transaction_id'
        file_exists = self.env['cm.attachment.rule'].search([(field_name, '=', res_id),('created_from_system','=',True)])
        if file_exists:
            file_exists.unlink()
        ATTACHMENT_NAME = "Letter"
        attach_id = self.env['ir.attachment'].create({
            'name': ATTACHMENT_NAME + '.pdf',
            'type': 'binary',
            'datas': b64_pdf,
            'res_model': 'cm.attachment.rule',
            'store_fname': ATTACHMENT_NAME,
            'mimetype': 'application/pdf'
        })
        self.attachment_generated = True
        return self.env['cm.attachment.rule'].sudo().create({
            'employee_id': self.unite.id,
            'entity_id': self.unite.id,
            'file_save': [(6, 0, attach_id.ids)],
            'attachment_filename': ATTACHMENT_NAME,
            field_name: res_id,
            'date': datetime.datetime.now(),
            'description': self.name,
            'created_from_system': True,
            # 'signed' : True if self.is_sign else False
        })

    def write(self, values):
        if values.get('content'):
            final_content = values.get('content')
            values['content'] = final_content.replace('line-height', '')
        return super(Letters, self).write(values)


class LettersTemp(models.Model):
    _name = "letters.template"

    name = fields.Char(string="Name")
    unite = fields.Many2one('cm.entity', string="Unite")
    introduction = fields.Html(string='Introduction')
    conclusion = fields.Html(string="Conclusion")
    content = fields.Html(string="Content")
    is_favorite = fields.Selection([
        ('0', 'not'),
        ('1', 'Favorite'),
    ], size=1, string="Favorite")

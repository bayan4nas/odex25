# -*- coding: utf-8 -*-
from odoo import models, api, _
from collections import defaultdict
from odoo.exceptions import AccessError,UserError
import base64
import io
from PyPDF2 import PdfFileReader, PdfFileWriter
from PIL import Image
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader


class IrAttachment(models.Model):
    _inherit = "ir.attachment"

    @api.model
    def merge_signature_to_pdf(self, data):
        attachment = self.browse(int(data['pdf_attachment_id']))
        pdf_bytes = base64.b64decode(attachment.datas)
        pdf_reader = PdfFileReader(io.BytesIO(pdf_bytes))
        pdf_writer = PdfFileWriter()
        sig_bytes = base64.b64decode(data['signature_base64'])
        sig_img = Image.open(io.BytesIO(sig_bytes)).convert("RGBA")

        page_number = int(data.get('page_number', 1)) - 1
        page = pdf_reader.getPage(page_number)
        page_width = float(page.mediaBox.getWidth())
        page_height = float(page.mediaBox.getHeight())

        left = float(data['left']) / data['container_width'] * page_width
        top = float(data['top']) / data['container_height'] * page_height
        width = float(data['width']) / data['container_width'] * page_width
        height = float(data['height']) / data['container_height'] * page_height

        bg = Image.new("RGBA", (int(page_width), int(page_height)), (255, 255, 255, 0))
        sig_img = sig_img.resize((int(width), int(height)))
        bg.paste(sig_img, (int(left), int(top)), sig_img)

        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=(page_width, page_height))
        can.drawImage(ImageReader(bg), 0, 0, width=page_width, height=page_height, mask='auto')
        can.save()
        packet.seek(0)

        bg_pdf = PdfFileReader(packet)

        for i in range(pdf_reader.numPages):
            original_page = pdf_reader.getPage(i)
            if i == page_number:
                original_page.mergePage(bg_pdf.getPage(0))
            pdf_writer.addPage(original_page)

        output_stream = io.BytesIO()
        pdf_writer.write(output_stream)
        output_stream.seek(0)

        new_pdf_base64 = base64.b64encode(output_stream.read()).decode('utf-8')

        new_attachment = self.create({
            'name': '_signed.pdf',
            'datas': new_pdf_base64,
            'mimetype': 'application/pdf',
            'type': 'binary',
            'public': True,
        })

        record_id = int(data.get('record_id'))  # تأكد أن الـ record_id معطى في data من الجافا سكريبت
        if record_id:
            rule = self.env['cm.attachment.rule'].sudo().browse(record_id)
            if rule.exists():
                rule.write({
                    'file_save': [(6, 0, [new_attachment.id])],
                    'signed': True,
                    'signed_user_id': self.env.user.id,
                })

        url = f'/web/content/{new_attachment.id}?download=true'
        return {
            'download_url': url,
            'attachment_id': new_attachment.id,
        }

    # override
    @api.model
    def check(self, mode, values=None):
        """ Restricts the access to an ir.attachment, according to referred mode """
        if self.env.is_superuser():
            return True
        # Always require an internal user (aka, employee) to access to a attachment
        if not (self.env.is_admin() or self.env.user.has_group('base.group_user')):
            raise AccessError(
                _("Sorry, you are not allowed to access this document."))
        # collect the records to check (by model)
        model_ids = defaultdict(set)            # {model_name: set(ids)}
        if self:
            # DLE P173: `test_01_portal_attachment`
            self.env['ir.attachment'].flush(['res_model', 'res_id', 'create_uid', 'public', 'res_field'])
            self._cr.execute('SELECT res_model, res_id, create_uid, public, res_field FROM ir_attachment WHERE id IN %s', [tuple(self.ids)])
            for res_model, res_id, create_uid, public, res_field in self._cr.fetchall():
                if public and mode == 'read':
                    continue
                if not (res_model and res_id):
                    continue
                model_ids[res_model].add(res_id)
        if values and values.get('res_model') and values.get('res_id'):
            model_ids[values['res_model']].add(values['res_id'])

        # check access rights on the records
        for res_model, res_ids in model_ids.items():
            # ignore attachments that are not attached to a resource anymore
            # when checking access rights (resource was deleted but attachment
            # was not)
            if res_model not in self.env:
                continue
            if res_model == 'res.users' and len(res_ids) == 1 and self.env.uid == list(res_ids)[0]:
                # by default a user cannot write on itself, despite the list of writeable fields
                # e.g. in the case of a user inserting an image into his image signature
                # we need to bypass this check which would needlessly throw us away
                continue
            records = self.env[res_model].browse(res_ids).exists()
            # For related models, check if we can write to the model, as unlinking
            # and creating attachments can be seen as an update to the model
            access_mode = 'write' if mode in ('create', 'unlink') else mode
            records.check_access_rights(access_mode)
            records.check_access_rule(access_mode)

    @api.model
    def read_as_sudo(self, domain=None, fields=None):
        return self.sudo().search_read(domain, fields)

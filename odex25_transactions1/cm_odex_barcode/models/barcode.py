# -*- coding: utf-8 -*-

# import sys
#
# # reload(sys)
# # sys.setdefaultencoding("utf-8")
import base64
import os
from odoo.exceptions import ValidationError


# import barcode as barcode
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont
from io import BytesIO
from pathlib import Path
from odoo.modules.module import get_module_resource


from lxml import etree

import arabic_reshaper
from bidi.algorithm import get_display
from odoo import models, api, fields
from odoo.tools.translate import _


# from odoo.osv.orm import setup_modifiers



class Transaction(models.Model):
    _inherit = 'transaction.transaction'

    binary_barcode = fields.Binary(string='Barcode', attachment=True)

    @api.constrains('ean13', 'name', 'transaction_date', 'type','subject')
    def binary_compute_constraint(self):
        font_path = os.path.join(os.path.dirname(__file__), 'img', 'amiri-regular.ttf')
        font_size = 22

        img = Image.new("RGBA", (500, 420), "white")
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype(font_path, font_size)

        def draw_text(draw, text, position, font, alignment="left"):
            text_size = draw.textsize(text, font=font)

            if alignment == "right":
                position = (position[0] - text_size[0], position[1])
            elif alignment == "center":
                position = (position[0] - text_size[0] / 2, position[1])

            draw.text(position, text, "black", font=font)

        draw_text(draw, " رقم المعاملة : " + (self.name or ''), (10, 20), font)
        draw_text(draw, " تاريخ المعاملة الهجري : " + (self.transaction_date_hijri or '').replace('-', '/'), (10, 60), font)
        draw_text(draw, " تاريخ المعاملة الميلادي : " + (str(self.transaction_date) if self.transaction_date else '').replace('-', '/'), (10, 100), font)
        draw_text(draw, "  الموضوع : " + (str(self.subject) if self.subject else ''), (120, 140), font)        


        # Generate barcode
        barcode = self.env['ir.actions.report'].barcode('Code11', self.name, width=250, height=100, humanreadable=0)
        barcode_buffer = BytesIO(barcode)
        barcode_image_file = Image.open(barcode_buffer)
        img.paste(barcode_image_file, (20, 180))

        # Save image to binary field
        buffered = BytesIO()
        img.save(buffered, format="png")
        img_str = base64.b64encode(buffered.getvalue())
        self.binary_barcode = img_str

class AttachmentInherit(models.Model):
    _inherit = 'ir.attachment'

    # @api.constrains('vals_list')
    # def create(self, vals_list):
    #     print("***********")
    #     res = super(AttachmentInherit, self).create(vals_list)
    #     print(res.mimetype)
    #     if res.mimetype == 'text/html':
    #         raise ValidationError(_('You cannot inset a html File'))
    #
    #     return res

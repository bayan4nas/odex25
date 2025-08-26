# your_module/models/models.py

from odoo import models, fields, api


class Watermark(models.AbstractModel):
    _name = 'watermark.model'

    @api.model
    def get_watermark_data(self):
        user_name = self.env.user.name
        current_date = fields.Date.today()
        return {
            'user_name': user_name,
            'current_date': current_date,
        }

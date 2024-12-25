from odoo import fields, models, api


class Company(models.Model):
    _inherit = 'res.company'

    attachment_scop = fields.Binary(string='Application brochure',)
    day = fields.Integer(string='Day')
    month = fields.Integer(string='Month')
    year = fields.Integer(string='Year')
    # @api.onchange('name')
    # def get_attachment(self):
    #     attach = self.env['competitive.purchase.attachment']
    #     print(attach.attachment_scop, 'attachment_scop')
    #     self.attachment_scop = attach.attachment_scop

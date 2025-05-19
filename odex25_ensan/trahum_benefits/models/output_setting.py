from odoo import models, fields, api

class OutputSetting(models.Model):
    _name = 'benefits.output'
    _description = 'Output Settings'
    _order = 'name asc'

    name = fields.Char(string='Output Name', required=True)
    output_type = fields.Selection([
        ('financial', 'Financial'),
        ('card_voucher', 'Card or Voucher'),
        ('in_kind', 'In-Kind Materials'),
        ('coordination', 'Coordination with a Third Party'),
        ('other', 'Other')
    ], string='Output Type', required=True)
    
    # Financial fields
    amount = fields.Float(string='Amount')
    max_limit = fields.Float(string='Maximum Limit')
    min_limit = fields.Float(string='Minimum Limit')
    related_to_people = fields.Boolean(string='Related to Number of People?')
    max_people = fields.Integer(string='Maximum Number of People')
    amount_per_person = fields.Float(string='Amount per Person')
    active = fields.Boolean(string='Active', default=True)
    description = fields.Text(string="Description")

    @api.onchange('output_type')
    def _onchange_output_type(self):
        if self.output_type != 'financial':
            self.amount = 0
            self.max_limit = 0
            self.min_limit = 0
            self.related_to_people = False
            self.max_people = 0
            self.amount_per_person = 0
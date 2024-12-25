# -*- coding: utf-8 -*-


from odoo import models, fields, api, exceptions, tools, _

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Add new fields
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    commission_percentage = fields.Float(string='Commission Percentage', help="The commission percentage.",config_parameter="property_management.commission_percentage")
    commission_account_id = fields.Many2one('account.account', string='Commission Account', help="The account used to record commissions.",config_parameter="property_management.commission_account_id")
    collecting_company_id = fields.Many2one('res.partner', string='Collecting Company', help="The company responsible for collecting the commission.",config_parameter='property_management.collecting_company_id')
    
class RentType(models.Model):
    _name = 'rent.type'
    _description = 'Rent Type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "id desc"

    active = fields.Boolean(default=True)
    name = fields.Char(string="Name")
    months = fields.Char(string="Months Between Payment")
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.user.company_id)

    _sql_constraints = [
        ('name_months', 'unique(name,months)', _('Name and months numbers must be unique.')),
    ]

from odoo.exceptions import UserError  , ValidationError
from odoo import api, fields, models, _


class DonationsItems(models.Model):
    _name = "donations.items"
    _description = "Donation Items"

    name = fields.Char(string="Donation Name")
    donation_type = fields.Selection([('donation', 'Donation'),('waqf', 'Waqf'),('sponsorship', 'Sponsorship'),], string='Donation Type')
    branch_custom_id = fields.Many2one('branch.settings', string="Branch")
    show_donation_item = fields.Boolean(string='Show Donation Item')
    fixed_value = fields.Boolean(string='Is Fixed Value?')
    fixed_donation_amount = fields.Float(string='Donation Amount')
    account_id = fields.Many2one('account.account', string="Account",domain="[('user_type_id.id','=',13)]")

class PointsOfSaleCustom(models.Model):
    _name = "points.of.sale.custom"
    _description = "Points Of Sale Custom"

    name = fields.Char(string="Sequence/Point Name",readonly=True)
    department_name = fields.Selection([('men', 'Men'),('women', 'Women')], string='Department Name')
    branch_custom_ids = fields.Many2many('branch.settings',relation='points_sale_branch_settings_rel',column1='points_sale_id', column2='branch_id',string="Branch")
    journal_id = fields.Many2one('account.journal', string="Journal",domain="[('type','=','bank')]")

    @api.model
    def create(self, vals):
        res = super(PointsOfSaleCustom, self).create(vals)
        if not res.name or res.name == _('New'):
            res.name = self.env['ir.sequence'].sudo().next_by_code('point.of.sale.sequence') or _('New')
        return res

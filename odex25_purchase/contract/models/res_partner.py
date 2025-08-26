# Copyright 2017 Carlos Dauden <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError
import re


class ResPartner(models.Model):
    _inherit = 'res.partner'

    sale_contract_count = fields.Integer(string='Sale Contracts',compute='_compute_contract_count',)
    purchase_contract_count = fields.Integer(string='Purchase Contracts', compute='_compute_contract_count')
    contract_ids = fields.One2many(comodel_name='contract.contract', inverse='partner_id', string="Contracts")
    ref = fields.Char(string='Vendor NO', index=True)
    executive_manager = fields.Char(string='Executive Manager')
    commercial_register = fields.Char(string="Commercial Register")
    specialist = fields.Char('Specialist')
    appointed = fields.Char('Appointed')
    app_email = fields.Char('Appointed Email')
    #
    # @api.constrains('ref')
    # def _check_ref_is_ten_digits(self):
    #     for record in self:
    #         if record.ref and not re.fullmatch(r'\d{10}', record.ref):
    #             raise ValidationError(_("Reference must contain exactly 10 digits"))

    def _compute_contract_count(self):
        contract_model = self.env['contract.contract']
        fetch_data = contract_model.read_group([
            ('partner_id', 'child_of', self.ids)],
            ['partner_id', 'contract_type'], ['partner_id', 'contract_type'],
            lazy=False)
        result = [[data['partner_id'][0], data['contract_type'],
                   data['__count']] for data in fetch_data]
        for partner in self:
            partner_child_ids = partner.child_ids.ids + partner.ids
            partner.sale_contract_count = sum([
                r[2] for r in result
                if r[0] in partner_child_ids and r[1] == 'sale'])
            partner.purchase_contract_count = sum([
                r[2] for r in result
                if r[0] in partner_child_ids and r[1] == 'purchase'])

    def act_show_contract(self):
        """ This opens contract view
            @return: the contract view
        """
        self.ensure_one()
        contract_type = self._context.get('contract_type')
        res = self._get_act_window_contract_xml(contract_type)
        res.update(context=dict(self.env.context, search_default_partner_id=self.id, default_partner_id=self.id,
                                default_pricelist_id=self.property_product_pricelist.id))
        return res

    def _get_act_window_contract_xml(self, contract_type):
        if contract_type == 'purchase':
            return self.env['ir.actions.act_window'].for_xml_id('contract', 'action_supplier_contract')
        else:
            return self.env['ir.actions.act_window'].for_xml_id('contract', 'action_customer_contract')

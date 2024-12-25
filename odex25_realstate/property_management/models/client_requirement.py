# -*- coding: utf-8 -*-

from odoo import models, fields, api, _


class ReClientRequirement(models.Model):
    _inherit = "re.clients.requirement"

    action_type = fields.Selection(selection_add=[('rent', 'Rent')])


class ReClientRequirementProperty(models.Model):
    _inherit = "re.clients.requirement.property"

    rental_contract_id = fields.Many2one('rental.contract', string="Rental Contract")


    def create_contract_request(self):
        vals = {}
        rental_obj = self.env['rental.contract']
        for record in self:
            if record.state != 'register':
                raise exceptions.ValidationError(_("Please first Register Your Request"
                                                   "Then You can Proceed"))
            name = 'Contract From Client Request:' + str(record.request_id.name)
            vals = {
                'name': name,
                'rent_method': self.search_type,
                'property_id': record.property_id and record.property_id.id or False,
                'state': 'draft',
                'date': date.today(),
                'rent_amount': record.price,
                'original_rent_amount': record.price,
                'unit_ids': [(6, 0, record.unit_id.ids)] or False,
                'partner_id': record.request_id.partner_id and record.request_id.partner_id.id or False,
            }
            rent_contract = rental_obj.create(vals)
            if rent_contract:
                # rent_contract.action_submit()
                record.rental_contract_id = rent_contract.id
                record.flag = True
        return True

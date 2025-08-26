# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
from lxml import etree
import json


class AccountInvoice(models.Model):
    _inherit = 'account.move'

    # todo start
    def _domain_get_partner(self):
        default_move_type = self._context.get('default_move_type')
        if default_move_type in ['in_receipt', 'in_invoice']:
            return [('user_ids', '=', False), ('is_company', '=', True)]

    partner_id = fields.Many2one('res.partner', readonly=True, tracking=True,
                                 states={'draft': [('readonly', False)]},
                                 check_company=True,
                                 string='Partner', change_default=True, ondelete='restrict', domain=lambda self: self._domain_get_partner())
    # todo end

    state = fields.Selection(
        selection=[
            ("draft", "Assistant Accountant"),
            ("budget_management", "Budget Management"),
            ("accounting_department", "Accounting Department"),
            ("posted", "Posted"),
            ("cancel", "Cancelled"),
        ],
    )
    state_in = fields.Selection(related="state",tracking=False)
    state_in_receipt = fields.Selection(selection=[
        ("draft", "Assistant Accountant"),
        ("budget_management", "Budget Management"),
        ("accounting_department", "Accounting Department"),
        ("posted", "Posted"),
        ("cancel", "Cancelled"),],related="state",tracking=False)

    def accounting_department(self):
        # Check budget availability for each  line
        for line in self.invoice_line_ids:  # Assuming `payment_line_ids` relates to 'account.payment.line'
            if not line.name or not line.account_id or line.quantity <= 0 or line.price_unit <= 0:
                raise ValidationError(_("Empty or incomplete lines are not allowed. Please fill all required fields in the line items."))
            if not self.is_commite_expenses and(not line.item_budget_id or line.remaining_item_budget < line.price_subtotal) :
                raise ValidationError(
                    _("Insufficient budget for the line with item budget %s") % line.item_budget_id.name)
        # Proceed with the normal budget management logic if no validation error is raised
        self.state = "accounting_department"

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = super(AccountInvoice, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                       submenu=submenu)
        doc = etree.XML(res['arch'])
        if view_type == 'form':
            # todo start
            for node in doc.xpath("//button[@name='accounting_department']"):
                modifiers = json.loads(node.get("modifiers"))
                modifiers['invisible'] = [
                    '|',
                    '|',
                    ('move_type', 'in', ('out_invoice')),
                    ('state', 'not in', ['draft']),
                    ('move_type', 'in', ('in_receipt')),
                    ('state', 'not in', ['budget_management']),
                ]

                node.set("modifiers", json.dumps(modifiers))
            #     todo end

            #     todo start
            for node in doc.xpath("//field"):
                if node.get('modifiers'):
                    modifiers = json.loads(node.get("modifiers"))
                    if 'readonly' not in modifiers:
                        modifiers['readonly'] = [('state', 'in',['posted'])]
                    else:
                        if type(modifiers['readonly']) != bool:
                            modifiers['readonly'].insert(0, '|')
                            modifiers['readonly'].append(('state', 'in',['posted']))
                    node.set("modifiers", json.dumps(modifiers))
            #     todo end

            #     todo start
            for node in doc.xpath("//field[@name='invoice_line_ids']"):
                modifiers = json.loads(node.get("modifiers"))
                modifiers['readonly'].append(('state', 'in',['posted','accounting_department']))
                node.set("modifiers", json.dumps(modifiers))
            #     todo end
            res['arch'] = etree.tostring(doc)
        return res

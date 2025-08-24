from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    item_budget_id = fields.Many2one(related='request_id.item_budget_id')

    def action_view_contract(self):
        formview_ref = self.env.ref('odex25_contract_saip.inherit_contract_contract_supplier_form_view', False)
        treeview_ref = self.env.ref('contract.contract_contract_tree_view', False)
        return {
            'name': _('Contract'),
            'domain': [('purchase_id', '=', self.id),('contract_type', '=', 'purchase')],
            'view_mode': 'tree,form',
            'res_model': 'contract.contract',
            'view_id': False,
            'views': [(treeview_ref and treeview_ref.id or False, 'tree'),
                      (formview_ref and formview_ref.id or False, 'form')],
            'type': 'ir.actions.act_window',
        }


class PurchaseRequest(models.Model):
    _inherit = 'purchase.order.line'

    item_budget_id = fields.Many2one(related='order_id.item_budget_id')
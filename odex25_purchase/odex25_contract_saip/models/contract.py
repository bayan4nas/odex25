from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ContractInherit(models.Model):
    _inherit = 'contract.contract'

    award_date = fields.Date(string="Award Date")

    contract_copy = fields.Many2many("ir.attachment", "contract_copy_rel", "contract_id", "attachment_id",
                                     string="Contract Copy", states={'to_confirm': [('required', True)]}, copy=False)
    final_warranty = fields.Many2many("ir.attachment", "final_warranty_rel", "warranty_id", "attachment_id",
                                      string="Final Warranty", states={'to_confirm': [('required', True)]}, copy=False)
    additional_documents = fields.Many2many("ir.attachment", "additional_documents_rel", "additional_id",
                                            "attachment_id", string="Additional Documents",
                                            states={'to_confirm': [('required', True)]}, copy=False)

    state = fields.Selection(selection_add=[('new', 'Draft (Contact New)'),
                                            ('contract_management', 'Contract Managment'),
                                            ('budget_management', 'Budget Managment'),
                                            ("wait_budget", "Pending Budget Approve"),
                                            ('EDPC', 'Executive Director Of Procurement And Contracts'),
                                            ('budget_approve', 'Executive Vice President of Corporate Resources'),
                                            ('general_supervisor', 'Chief Procurement Executive'),
                                            ('in_progress', 'In progress'),
                                            ('suspended', 'Suspended'),
                                            ('closed', 'Closed'),
                                            ('cancel', 'Cancel'),
                                            ], default="new", tracking=True)

    is_remaining_amount_zero = fields.Boolean(string="Is Remaining Amount Zero?", compute="_compute_is_remaining_amount_zero")
    state_history = fields.Text(string="State History", default='[]')
    ref = fields.Char(related='partner_id.ref', string='Contractor NO')
    note = fields.Text(string='Note', default=False)
    old_state = fields.Char(string="old_state")
    check = fields.Boolean(string='Check')
    department_name = fields.Char(related='department_id.name')



    def action_open_return_state_wizard(self):
        return {
            "type": "ir.actions.act_window",
            "name": _("Open Return State Wizard"),
            "res_model": "return.state.wiz",
            "view_mode": "form",
            "target": "new",
            "context": {"default_contract_id": self.id},
        }

    def solve_note(self):
        self.note = False
        # self.check = False
        self.state = self.old_state or self.state

    @api.depends('remaining_amount')
    def _compute_is_remaining_amount_zero(self):
        for record in self:
            record.is_remaining_amount_zero = record.remaining_amount == 0

    def contract_management(self):
        self.write({'state': 'budget_management'})
    # ;To be change latter when install budget; #
    def sent_to_budget_management(self):
        self.write({'state': 'EDPC'})

    def set_in_progress_state(self):
        self.write({'state': 'in_progress'})

    def in_progress_state(self):
        with_tax_amount = self.with_tax_amount
        if with_tax_amount < self.company_id.direct_purchase:
            self.set_in_progress_state()
        else:
            self.write({'state': 'budget_approve'})

    def in_budget_approve(self):
        with_tax_amount = self.with_tax_amount
        if with_tax_amount < self.company_id.chief_executive_officer:
            self.set_in_progress_state()
        else:
            self.write({'state': 'general_supervisor'})

    def in_general_supervisor(self):
        self.set_in_progress_state()

    def confirmed_state(self):
        for contract in self:
            contract._validate_contract()
            contract._mark_contract_confirmed()

    def _validate_contract(self):
        for contract in self:
            if not contract.request_id:
                raise ValidationError(_("The contract is not linked with purchase request"))
            if not contract.date_start:
                raise ValidationError(_('Please Enter Contract Start Date!!'))
            if contract.type_of_contraction == 'contract' and contract.installment_count == 0:
                raise ValidationError(_("Please enter the installments!"))
            total_amount = sum(contract.get_related_instalment().mapped('total_amount'))
            if total_amount != contract.with_tax_amount:
                raise ValidationError(_("Installment you have scheduled is not equal to the contract amount"))
            if not (contract.contract_copy and contract.final_warranty and contract.additional_documents):
                raise ValidationError(_("You must attach Contract Copy and Final Warranty and Additional Documents attachment"))

    def _mark_contract_confirmed(self):
        for contract in self:
            contract.write({'state': 'contract_management'})
            installments = self.env["line.contract.installment"].search([("contract_id", "=", contract.id)])
            for rec in installments:
                rec.write({'state': 'confirmed'})



    def EDPC_state(self):
        if not self.date_start:
            raise ValidationError(_('Please Enter Contract Start Date!!'))
        if self.type_of_contraction == 'contract' and self.installment_count == 0:
            raise ValidationError(_("Please enter the installments!"))
        self.write({'state': 'EDPC'})

    def cancel_state(self):
        if self.state in ['new', 'contract_management']:
            if self.purchase_id:
                self.purchase_id.button_cancel()
        self.write({"state": "cancel"})
        return super(ContractInherit, self).cancel_state()

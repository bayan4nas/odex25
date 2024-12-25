from odoo import fields, models, api, _
from stdnum.au.acn import to_abn


class PaymentOrders(models.Model):
    _name = 'payment.orders'
    _description = "Payment Orders"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Code", copy=False, readonly=True, default=lambda x: _('New'))
    ref_num = fields.Char(string='Ref. Number')
    payment_order_date = fields.Datetime(string="Payment Order Date",default=fields.Datetime.now)
    accountant_id = fields.Many2one('res.users',string='Accountant')
    payment_order_description = fields.Char(string='Payment Order Description')
    service_requests_ids = fields.One2many('service.request', 'payment_order_id', string ='Service Requests')
    total_moves = fields.Integer(string="Total Move Lines", compute='_get_total_moves')
    state = fields.Selection(string='Status', selection=[('draft', 'Draft'),('accountant_approve', 'accountant Approve'),('department_manager_approve', 'Department Manager Approve')
        ,('accounting_approve', 'Accounting Approve'),('general_manager_approve', 'General Manager Approve'),('refused', 'Refused')],default = 'draft',tracking=True)

    @api.model
    def create(self, vals):
        res = super(PaymentOrders, self).create(vals)
        if not res.name or res.name == _('New'):
            res.name = self.env['ir.sequence'].sudo().next_by_code('payment.orders.sequence') or _('New')
        return res

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        if self.env.user and self.env.user.id and self.env.user.has_group("odex_benefit.group_benefit_payment_accountant_accept"):
            args += [('accountant_id', '=', self.env.user.id)]
        return super(PaymentOrders, self).search(args, offset, limit, order, count)

    def _get_total_moves(self):
        for rec in self:
            rec.total_moves = self.env['account.move'].search_count([
                ('payment_order_id', '=', rec.id), ('move_type', '!=', 'in_invoice')])

    def action_accountant_approve(self):
        for rec in self:
            rec.state = 'accountant_approve'

    def action_department_manager_approve(self):
        for rec in self:
            rec.state = 'department_manager_approve'

    def action_accounting_approve(self):
        for rec in self:
            rec.state = 'accounting_approve'

    def action_general_manager_approve(self):
        for rec in self:
            rec.state = 'general_manager_approve'
            x = self.env['account.move'].create(
                {
                    'ref': f'{rec.payment_order_description}/{rec.ref_num}',
                    'journal_id': self.env["family.validation.setting"].search([], limit=1).journal_id.id,
                    'payment_order_id': rec.id,
                    'line_ids' : rec.get_lines()
                }
            )
    def action_refuse(self):
        for rec in self:
            rec.state = 'refused'

    def action_open_related_move_records(self):
        """ Opens a tree view with related records filtered by a dynamic domain """
        moves = self.env['account.move'].search([
            ('payment_order_id', '=', self.id), ('move_type', '!=', 'in_invoice')
        ]).ids
        return {
            'name': _('Moves'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', moves)],
        }
    def get_lines(self):
        lines = []
        total_credit = 0
        for request in self.service_requests_ids:
            lines.append(
                {
                    'account_id' : request.account_id.id,
                    'partner_id' : request.family_id.partner_id.id,
                    # 'branch_id' : request.branch_custom_id.id,
                    'analytic_account_id': request.branch_custom_id.branch.analytic_account_id.id,
                    'debit' : request.aid_amount,
                    'name': f'{"Family code"}{request.family_id.code}-{request.description}-{request.payment_order_id.name}-{request.payment_order_id.ref_num}',
                }
            )
            total_credit += request.aid_amount
        lines.append({
            'account_id': self.env["family.validation.setting"].search([], limit=1).account_id.id,
            'name': f'{self.name}-{self.ref_num}',
            'credit' : total_credit,
        })
        return [(0, 0, line) for line in lines]
    # def create_entry(self, journal_id, lines):
    #     """Create an account move entry"""
    #     move_vals = {
    #         'journal_id': journal_id,
    #         'date': self.date,
    #         'ref': self.name,
    #         'family_confirm_id': self.id,
    #         'benefit_family_ids': [(6, 0, self.family_ids.ids)],
    #         'line_ids': lines,
    #     }
    #     move_id = self.env['account.move'].create(move_vals)
    #     move_id.action_post()
    #     return True
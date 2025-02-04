from datetime import date, datetime
from odoo.exceptions import ValidationError
from odoo import api, fields, models, _


class InitialEvaluationWizard(models.TransientModel):
    _name = 'initial.evaluation.wizard'
    _description = 'initial Evaluation Wizard'

    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    purchase_requisition = fields.Many2many(comodel_name='purchase.requisition', string='Purchase Agreement')
    committee_member = fields.Many2one(comodel_name='res.user', string='Committee Member')
    move_ids = fields.Many2many('purchase.order', string='Orders')
    today = fields.Date(string='Your string', default=lambda self: fields.Date.today())

    def action_create_search(self):
        self.move_ids = False
        if not self.start_date or not self.end_date or self.purchase_requisition or self.committee_member:
            raise ValidationError(_('You Should Select Parameters'))
        domain = []
        purchase_requisition = self.purchase_requisition
        if purchase_requisition:
            domain += [("requisition_id", "in", purchase_requisition.ids)]
        if self.committee_member:
            domain += [("committee_members", "in", self.committee_member.ids)]

        start_date = self.start_date
        if start_date:
            domain += [('create_date', '>=', start_date)]
        if not start_date:
            start_date = datetime(2010, 1, 1, 10, 0, 0, 0)

        end_date = self.end_date
        if end_date:
            domain += [('create_date', '<=', end_date)]
        if not end_date:
            end_date = datetime(2100, 1, 1, 10, 0, 0, 0)

        self.move_ids = self.env['purchase.order'].search(domain)
        print('move_lines >>>>>>>>>>>', self.move_ids.mapped('name'))

        if not self.move_ids:
            raise ValidationError(_('There is No Data to present'))
        # return self.move_ids
    
    def action_create_search_html(self):
        self.action_create_search()
        return self.env.ref('odex25_evaluation_eriteria.initial_evaluation_view_action').report_action(self)

    def action_create_search_pdf(self):
        self.action_create_search()
        return self.env.ref('odex25_evaluation_eriteria.initial_evaluation_pdf_action').report_action(self)

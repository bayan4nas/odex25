from odoo import fields, models, api, _
from odoo.exceptions import UserError


class FamilyComplaints(models.Model):
    _name = 'family.complaints'
    _rec_name = 'complaints_reason'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    complaints_date = fields.Datetime(string="Complaints Date",default=fields.Datetime.now)
    family_id = fields.Many2one('grant.benefit',string='Family',domain="['|','|',('state','=','second_approve'),('state','=','temporarily_suspended'),('state','=','suspended_first_approve')]")
    researcher_id = fields.Many2one("committees.line", string="Researcher",related="family_id.researcher_id")
    branch_custom_id = fields.Many2one('branch.settings', string="Branch",related='family_id.branch_custom_id')
    complaints_reason = fields.Char(string="Complaints Reason")
    message = fields.Text(string="Message")
    complaints_category_ids = fields.Many2many('complaints.category',relation="family_complaints_category_rel",
                     column1="family_complaints",
                     column2="category",
                     string="Complaints Categories")
    priority = fields.Selection( [ ('0', 'Normal'),('1', 'Low'),('2', 'High'),('3', 'Very High'),('4', 'Very Very High'),('5', 'Danger')], string='Priority')
    state = fields.Selection([('draft', 'Draft'),('receiving_complaint', 'Receiving the complaint'),('review_complaint', 'Review Complaint'),
                              ('work_in_complaint', 'Work in complaint'),('complaint_done', 'Complaint Done'),('refuse', 'Refuse')],
                             default='draft',tracking=True)

    def unlink(self):
        for order in self:
            if order.state not in ['draft']:
                raise UserError(_('You cannot delete this record'))
        return super(FamilyComplaints, self).unlink()


    def action_receiving_complaint(self):
        for rec in self:
            rec.state = 'receiving_complaint'

    def action_review_complaint(self):
        for rec in self:
            rec.state = 'review_complaint'

    def action_work_in_complaint(self):
        for rec in self:
            rec.state = 'work_in_complaint'

    def action_done(self):
        for rec in self:
            rec.state = 'complaint_done'

    def action_refuse(self):
        for rec in self:
            rec.state = 'refuse'


from odoo import models, fields, api,_
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
class MembershipCancellationRequest(models.Model):
    _name = 'membership.cancellation.request'
    _description = 'Membership Cancellation Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'member_id'

    membership_id = fields.Many2one('dev.membership', string='Membership',required=True)
    member_id = fields.Many2one('res.partner', string='Member',related='membership_id.partner_id',store=True, required=True)
    membership_type_id = fields.Many2one('product.product',related='membership_id.product_id',store=True, string='Membership Type', required=True)
    cancel_reason = fields.Many2one('cancellation.reason',string='Cancellation Reason', required=True)
    request_date = fields.Datetime(string='Request Date', default=fields.Datetime.now)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Status', default='draft', track_visibility='onchange')

    def action_approve(self):
        for rec in self:
            # Convert request_date to a date if it's a datetime
            request_date = rec.request_date.date() if isinstance(rec.request_date, datetime) else rec.request_date
            # Check if the request date is before the membership end date
            if request_date < rec.membership_id.partner_id.memebership_end_date:
                # Update the membership end date to the request date
                rec.membership_id.partner_id.memebership_end_date = request_date
            rec.membership_id.request_date = request_date
            rec.state = 'approved'
            rec.membership_id.state = 'cancel'
            rec.membership_id.partner_id.check_active_membership()

    def action_reject(self):
        for rec in self:
            rec.state = 'rejected'
    def unlink(self):
        for record in self:
            if record.state != 'draft':
                raise UserError(_("Requests can only be deleted if they are in the draft state."))
        return super(MembershipCancellationRequest, self).unlink()

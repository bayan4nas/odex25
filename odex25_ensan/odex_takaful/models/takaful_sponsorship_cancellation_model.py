# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo import SUPERUSER_ID


class SponsorshipStopReason(models.Model):
    _name = "sponsorship.reason.stop"
    _description = "Sponsorship Stop Reason"
    _order = 'sequence'

    sequence = fields.Integer(help="Determine the display order", index=True,
                              string='Sequence')
    name = fields.Char(string='Reason', required=True)

class SponsorshipCancellation(models.Model):
    _name = 'sponsorship.cancellation'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = "Sponsorship Cancellation"
    _rec_name = "code"

    sponsorship_id = fields.Many2one("takaful.sponsorship", string="Sponsorship")
    code = fields.Char(string="Sponsorship Number", related="sponsorship_id.code",store=True)
    sponsor_id = fields.Many2one(string="The Sponsor", related="sponsorship_id.sponsor_id",store=True)
    create_date = fields.Date(string='Create Date', readonly=True, default=fields.Date.today)
    confirm_date = fields.Date(string='Confirm Date', readonly=True)
    cancel_type = fields.Selection([
        ('user', 'Manually'),
        ('sys', 'Automatically'),
        ], string='Cancellation Type', default="user", readonly=True)
    cancel_user_id = fields.Many2one('res.users', 'Cancelled By', readonly=True)
    confirm_user_id = fields.Many2one('res.users', 'Confirmed By', readonly=True)
    reason_id = fields.Many2one('sponsorship.reason.stop', string='Cancellation Reason')
    note = fields.Text(string='Comment')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('cancel', 'Cancelled'),
    ], string='state', default="draft")


    # @api.multi
    def do_cancel_action(self):
        """Confirm cancellation for Sponsorship"""
        for rec in self:
            if rec.sponsorship_id:
                rec.confirm_user_id = self.env.uid or SUPERUSER_ID
                rec.confirm_date = fields.Date.today()
                rec.state = "cancel"

                # Send SMS and Email Notifications
                canceled_template = self.env['takaful.message.template'].sudo().search(
                    [('template_name', '=', 'sponsorship_canceled')], limit=1)
           
                subject = canceled_template.title
                message = canceled_template.body
                partner_id = rec.sponsor_id.partner_id
                user_id = self.env['res.users'].sudo().search([('partner_id', '=', partner_id.id)], limit=1)
    
                push = self.env['takaful.push.notification'].sudo().create({
                    'user_id': user_id.id,   
                    'title': subject,    
                    'body': message,         
                })

                push.sudo().send_sms_notification()
                push.sudo().send_email_notification()

                month_count = 0
                residual_amount = 0
          
                # Get other open invoices
                open_invoices = self.env['account.move'].sudo().search([('state', '=', 'open'), ('operation_id', '=', rec.sponsorship_id.id), ('operation_type',  '=', 'sponsorship')])
                for inv in open_invoices:
                    # Get residual amount
                    month_count += 1
                    residual_amount += inv.residual_company_signed
                    # Enable Removing for journal_id
                    if inv.journal_id:
                        inv.journal_id.sudo().write({"update_posted": True,})

                    inv.sudo().action_cancel()
   
                rec.sponsorship_id.state = "canceled"
                rec.sponsorship_id.cancel_reason_id = self.id

                # Moving the arrears
                if month_count >0 and rec.sponsorship_id.sponsorship_type =='person':
                    arrears_id = self.env['sponsorship.benefit.arrears'].sudo().create({
                        'sponsorship_id': rec.sponsorship_id.id, 
                        'benefit_id': rec.sponsorship_id.benefit_id.id, 
                        'sponsor_id': rec.sponsorship_id.sponsor_id.id, 
                        'arrears_month_number': month_count,      
                        'arrears_total': residual_amount,  
                    })
                elif month_count >0 and rec.sponsorship_id.sponsorship_type =='group':
                    for ben in rec.sponsorship_id.benefit_ids:
                        arrears_id = self.env['sponsorship.benefit.arrears'].sudo().create({
                            'sponsorship_id': rec.sponsorship_id.id, 
                            'benefit_id': ben.id, 
                            'sponsor_id': rec.sponsorship_id.sponsor_id.id, 
                            'arrears_month_number': month_count,      
                            'arrears_total': rec.sponsorship_id.load_amount * month_count,  
                        })




                

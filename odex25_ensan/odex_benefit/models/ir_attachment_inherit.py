from odoo import fields, models, api, _


class BenefitAttachment(models.Model):

    _inherit = 'ir.attachment'

    benefit_id = fields.Many2one('grant.benefit',string="Benefit")
    member_id = fields.Many2one('family.member',string="Member")
    expiration_date = fields.Date(string='Expiration date')
    attach_status = fields.Selection(selection=[
        ('valid', 'Valid'),
        ('expired', 'Expired'),
    ], string='Attach Status',compute = "get_status",store=True)
    allow_days = fields.Integer(compute='get_allow_days',string='Allow Days')
    attach_id = fields.Many2one('attachments.settings', string="Attach",domain=[('attach_type', '=', 'member_attach')])
    hobbies_id = fields.Many2one('attachments.settings', string="Hobby",domain=[('attach_type', '=', 'hobbies_attach')])
    diseases_id = fields.Many2one('attachments.settings', string="Diseases",domain=[('attach_type', '=', 'diseases_attach')])
    disabilities_id = fields.Many2one('attachments.settings', string="Disabilities",domain=[('attach_type', '=', 'disabilities_attach')])
    hobby_attach = fields.Binary(attachment=True, string="Hobby Attach")
    # fields to management required and delete records in benefit attachment
    is_required = fields.Boolean(string='Is Required?')
    is_default = fields.Boolean(string='Is Default?')

    def action_preview_attachment(self):
        # Custom function to open the preview
        return {
            'type': 'ir.actions.act_url',
            'url': f'/browse/document/{self.id}',
            'target': 'new',  # Opens in a new tab
        }

    @api.depends('expiration_date')
    def get_status(self):
        for rec in self:
            today = fields.Date.today()
            if rec.expiration_date:
                if rec.expiration_date and rec.expiration_date > today:
                    rec.attach_status = 'valid'
                else:
                    rec.attach_status = 'expired'
            else:
                rec.attach_status = ''

    @api.depends('attach_status')
    def get_allow_days(self):
        for rec in self:
            today = fields.Date.today()
            if rec.attach_status == 'expired' and rec.expiration_date:
                difference =  today - rec.expiration_date
                days = difference.days
                rec.allow_days = days
            else:
                rec.allow_days = 0

    @api.onchange('hobbies_id')
    def onchange_hobbies_id(self):
        for rec in self:
            if rec.hobbies_id:
                rec.name = rec.hobbies_id.name

    @api.onchange('diseases_id')
    def onchange_diseases_id(self):
        for rec in self:
            if rec.diseases_id:
                rec.name = rec.diseases_id.name

    @api.onchange('disabilities_id')
    def onchange_disabilities_id(self):
        for rec in self:
            if rec.disabilities_id:
                rec.name = rec.disabilities_id.name


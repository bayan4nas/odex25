from odoo import fields, models ,api

class MemberHobbies(models.Model):
    _name = 'member.hobbies'

    name = fields.Char(string="Name")
    member_id = fields.Many2one('family.member',string="Member")
    hobbies_id = fields.Many2one('hobbies.settings',string="Hobby")
    hobby_attach = fields.Binary(attachment=True,string="Hobby Attach")
    expiration_date = fields.Date(string='Expiration date')
    attach_status = fields.Selection(selection=[
        ('valid', 'Valid'),
        ('expired', 'Expired'),
    ], string='Attach Status', compute="get_status", store=True)
    # fields to management required and delete records in benefit attachment
    is_required = fields.Boolean(string='Is Required?')
    is_default = fields.Boolean(string='Is Default?')

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



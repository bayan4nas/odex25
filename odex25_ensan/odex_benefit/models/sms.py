from odoo import models, fields, _


class SmsConfiguration(models.Model):
    _name = 'benefit.sms.configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char("name")
    case_text = fields.Text("case Text", tracking=True)
    state = fields.Selection([
        ('edit_info', 'Edit Information'),
        ('complete_info', 'Complete Information'),
        ('waiting_approve', 'Waiting Approved'),
        ('approve', 'Approved'),
        ('add_family', 'add Family'),
        ('first_refusal', 'First Refusal'),
        ('refused', 'Refused'),
        ('black_list', 'Black List'),
        ('approve_family', 'Approve Family'),
        ('zkat', 'zkat'),
        ('adha', 'adha'),
        ('loans', 'loans'),
    ])

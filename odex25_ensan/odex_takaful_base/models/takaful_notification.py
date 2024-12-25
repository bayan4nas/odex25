
#  This part for creating Takaful notifications
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class TakafulMessageType(models.Model):
    _name = 'takaful.message.type'
    _inherit = ['mail.thread']
    _description = "This is related to message types of notifications for Takaful Settings"

    name = fields.Char(
        string='Title', 
        help='Abbreviated title for the chosen tool type',
        required=True
    )
    tool_type = fields.Selection([
        ('sms', 'SMS'),
        ('app', 'Application'),
        ('email', 'Email')],
        string='Tool Type',
        required=True,
        tracking=True
    )

class TakafulNotification(models.Model):
    _name = 'takaful.notification'
    _inherit = ['mail.thread']
    _description = "Notifications for Takaful Settings"
    # _rec_name = 'name'

    duration = fields.Integer(string='Duration in Days', help='Please enter duration as days')
    notification_type = fields.Selection([
        ('before_finish', 'Before Finish'),
        ('before_cancel', 'Before Cancel'),
        ],
        string='Notification Type',
        default='before_finish',
        tracking=True
    )
   
    message_type_ids = fields.Many2many(
        'takaful.message.type',
        string='Message Type',
        required=True
    )

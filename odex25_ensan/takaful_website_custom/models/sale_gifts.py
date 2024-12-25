#-*- coding: utf-8 -*-
from odoo import models, fields



class SaleGifts(models.Model):
    _name = "sale.order.gifts"

    reciever_name = fields.Char("Reciever Name")
    reciever_phone = fields.Char('Reciever Phone')
    reciever_mail = fields.Char('Reciever Mail')
    sender_name = fields.Char('Sender Name')
    sale_order_id = fields.Many2one('sale.order')

class SaleOrderInherit(models.Model):
    _inherit = 'sale.order'

    sale_gifts_id = fields.Many2one('sale.order.gifts')
# -*- coding: utf-8 -*-

from odoo.exceptions import UserError  , ValidationError
from odoo import api, fields, models, _

import logging

_logger = logging.getLogger(__name__)


class TakafulContribution(models.Model):
    _name = "takaful.contribution"
    _description = "Financial Contribution"

    name = fields.Char(string="Operation Name")
    sponsor_id = fields.Many2one(
        'takaful.sponsor',
        string='The Sponsor',
        ondelete='set null'
    )
    need_id = fields.Many2one('benefits.needs')
    benefit_id = fields.Many2one(
        'grant.benefit',
        string='Beneficiary',
        ondelete='set null'
    )
    benefit_ids = fields.Many2many(
        'grant.benefit',
        string='Beneficiaries'
    )
    benefit_type = fields.Selection([
        ('orphan', 'Orphans'),
        ('widow', 'Widows'),
        ('general', 'General')],
        string='Beneficiaries Type',
        compute='_compute_benefit_type_values',
        related=False,
        readonly=True,
    )
    operation_type = fields.Selection([
        ('contribution', 'Needs Contribution'),
        ('gift', 'Financial Gift')],
        string='Operation Type',
    )
    amount = fields.Float(string="Amount")
    note = fields.Text(string='Note/Message')
    date = fields.Datetime(string="Date", default=fields.Datetime.now)
    entry_id = fields.Many2one('account.move', string="Entry")
    is_confirmed = fields.Boolean(default=False)

    def _compute_benefit_type_values(self):
        for rec in self:
            b_type = []
            if rec.benefit_ids:
                for i in rec.benefit_ids:
                    b_type.append(i.benefit_type)
            if rec.benefit_id:
                b_type.append(rec.benefit_id.benefit_type)
            if 'orphan' in b_type and 'widow' not in b_type:
                rec.benefit_type = 'orphan'
            if 'widow' in b_type and 'orphan' not in b_type:
                rec.benefit_type = 'widow'
            if 'widow' in b_type and 'orphan' in b_type:
                rec.benefit_type = 'general'
            if b_type == []:
                rec.benefit_type = ''

    def create_entry(self):
        sudoConf = self.env['ir.config_parameter'].sudo()
        journal_id = sudoConf.get_param('odex_takaful_base.kafala_journal_id', default=False)   
        if not journal_id:
            # Raise an error
            raise ValidationError(
                _(u'No Journal for Sponsorships, Please configure it'))

        need_inv = self.env['needs.payment.line'].sudo().create({
            "need_id" : self.need_id.id,
            "invoice_id" : inv.id,
            })
        
        product_id = self.env['product.product'].search([('default_code', '=', 'financial_gift')], limit=1)
        partner_id = self.sponsor_id.partner_id
        
        product_id.sudo().write({
            "list_price": self.amount,
            })

        # Do your staf ..
        this_products_line = [[0, 0, {'product_id': product_id.id,
                               'tax_id': False,
                               }]
                            ]

        so_id = self.env['sale.order'].create({
            'partner_id': partner_id.id,
            'partner_invoice_id': partner_id.id,
            'partner_shipping_id': partner_id.id,
            'client_order_ref': u'مساهمة مالية',
            'note': u'مساهمة مالية لصالح:' + '\n' + (self.benefit_id.name if self.benefit_id else ""),
            'order_line': this_products_line
        })

        # Invoicing
        so_id.action_confirm()
        inv_id = so_id.action_invoice_create()
        inv = self.env['account.move'].browse(inv_id)
        inv.journal_id = int(journal_id)

        move_name = u'مساهمة مالية بالأمر %s' % inv.origin
        ctx = self.env.context.copy()
        ctx.update({'sponsorship' : { 
                        'name': move_name,
                        'ref': inv.origin,
                        }
                    })
        inv.with_context(ctx).action_invoice_open()

        self.entry_id = inv.move_id.id



# -*- coding: utf-8 -*-
from odoo import api, fields, models

class AccountMove(models.Model):

    _inherit = 'account.move'

    attach_no = fields.Integer(compute='get_attachments')
    res_id = fields.Integer()
    res_model = fields.Char()

    def get_attachments(self):
        # Check if multiple records are passed, and handle them in a loop
        if len(self) > 1:
            action = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
            action['domain'] = [
                ('res_model', '=', 'account.move'),
                ('res_id', 'in', self.ids), 
            ]
            
            # Update attachment count for all records (if necessary)
            for record in self:
                related_ids = record.ids
                related_models = 'account.move'
    
                if record.res_id and record.res_model:
                    related_ids = record.ids + [record.res_id]
                    related_models = ['account.move', record.res_model]
                    action['domain'] = [
                        ('res_model', 'in', related_models),
                        ('res_id', 'in', related_ids), 
                    ]
                
                # Context for creating new attachments for each record
                action['context'] = "{'default_res_model': '%s','default_res_id': %d}" % (record._name, record.id)
                
                # Update attachment count for each record
                record.attach_no = self.env['ir.attachment'].search_count([
                    ('res_model', 'in', related_models),
                    ('res_id', 'in', related_ids)
                ])
    
            return action
    
        # If only one record is passed, use the original logic
        self.ensure_one()
    
        action = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
        action['domain'] = [
            ('res_model', '=', 'account.move'),
            ('res_id', 'in', self.ids), 
        ]
        domain = [
            ('res_model', '=', 'account.move'),
            ('res_id', 'in', self.ids), 
        ]
        related_ids = self.ids
        related_models = 'account.move'
    
        if self.res_id and self.res_model:
            related_ids = self.ids + [self.res_id]
            related_models = ['account.move', self.res_model]
            action['domain'] = [
                ('res_model', 'in', related_models),
                ('res_id', 'in', related_ids), 
            ]
            domain = [
                ('res_model', 'in', related_models),
                ('res_id', 'in', related_ids), 
            ]
    
        # Context for creating new attachments
        action['context'] = "{'default_res_model': '%s','default_res_id': %d}" % (self._name, self.id)
        
        # Update attachment count for smart button
        self.attach_no = self.env['ir.attachment'].search_count(domain)
    
        return action


    # def get_attachments(self):
    #     self.ensure_one()

    #     action = self.env['ir.actions.act_window']._for_xml_id('base.action_attachment')
    #     action['domain'] = [
    #         ('res_model', '=', 'account.move'),
    #         ('res_id', 'in',self.ids), ]
    #     domain = [
    #         ('res_model', '=', 'account.move'),
    #         ('res_id', 'in', self.ids), ]
    #     related_ids = self.ids
    #     related_models = 'account.move'

    #     if self.res_id and self.res_model:
    #         related_ids = self.ids + [self.res_id]
    #         related_models = ['account.move', self.res_model]
    #         action['domain'] = [
    #             ('res_model', 'in', related_models),
    #             ('res_id', 'in', related_ids), ]
    #         domain = [
    #             ('res_model', 'in', related_models),
    #             ('res_id', 'in', related_ids), ]

    #     # Context for creating new attachments
    #     action['context'] = "{'default_res_model': '%s','default_res_id': %d}" % (self._name, self.id)
    #     # Update attachment count for smart button


    #     self.attach_no = self.env['ir.attachment'].search_count(domain)

    #     return action


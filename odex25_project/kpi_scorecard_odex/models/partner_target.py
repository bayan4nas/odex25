from odoo import fields, models, api


class PartnerTarget(models.Model):
    _name = 'partner.target'
    kbi_line_id = fields.Many2one(comodel_name='kpi.scorecard.line')
    partner_id = fields.Many2one(comodel_name='res.partner')
    planned_value = fields.Float()
    target_value=fields.Float(related='kbi_line_id.target_value')
    actual_value=fields.Float(related='kbi_line_id.actual_value')


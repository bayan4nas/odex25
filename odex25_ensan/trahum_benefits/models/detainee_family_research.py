from odoo import models, fields, api, _
from random import randint
import logging

from odoo.exceptions import  ValidationError
class DetaineeFamilyResearch(models.Model):
    _inherit = 'detainee.family.research'
    name = fields.Char(string="Name", copy=False, default=lambda x: _('New'))

    family_head_relation_id = fields.Many2one('family.member.relation',
        related="benefit_id.benefit_breadwinner_ids.relation_id",
        string='Relation ',
        readonly=True
    )
    family_marital_status_id = fields.Many2one('family.member.maritalstatus',related="benefit_id.benefit_breadwinner_ids.member_name.marital_status_id", string='Marital Status')
    detainee_name = fields.Char(
         related='benefit_id.detainee_file_id.name', string="Detainee",
    )
    detainee_id = fields.Many2one(
        'detainee.file', related='benefit_id.detainee_file_id', string="Detainee",
    )
    detainee_issues_ids = fields.One2many(
        'issues.information',
        'detainee_id',
        string="Detainee Issues",
        related="benefit_id.detainee_file_id.issues_ids",
        readonly=True
    )
    service_cats = fields.Many2many(
        'benefits.service',
        string='Service Cat.',
        domain=lambda self: self._get_service_domain()
    )
    period_text = fields.Char(
        related="benefit_id.detainee_file_id.period_text",
        string="Sentence Duration",
        readonly=True
    )

    prison_id = fields.Many2one(
        'res.prison',
        related="benefit_id.detainee_file_id.prison_id",
        string="Prison Name",
        readonly=True
    )

    city = fields.Many2one(
        "res.country.city",
        related="benefit_id.city",
        string="City",
        readonly=True
    )

    district = fields.Many2one(
        'res.district',
        related="benefit_id.district_name",
        string="District"
    )

    dest_name = fields.Char(
        related="benefit_id.benefit_breadwinner_ids.member_name.dest_name",
        string="Workplace",
        readonly=True
    )

    work_type_id = fields.Many2one(
        'work.type',
        related="benefit_id.benefit_breadwinner_ids.member_name.work_type_id",
        string="Work Type",
        readonly=True
    )

    @api.model
    def _get_service_domain(self):
        services = self.env['benefits.service'].search([
            ('beneficiary_categories.group_guest', '=', True),
            ('active', '=', True),
        ])
        return [('id', 'in', services.ids)]
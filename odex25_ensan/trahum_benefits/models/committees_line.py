from odoo import models, fields, api, _


class Committees(models.Model):
    _inherit = 'committees.line'

    period_text = fields.Char(related="detainee_id.period_text", string="Rent Period", readonly=True)
    prison_id = fields.Many2one('res.prison',related="detainee_id.prison_id", string="Prison Name", readonly=True)
    marital_status_id = fields.Many2one('family.member.maritalstatus',related="detainee_id.detainee_id.marital_status_id", string='Marital Status')
    # education_ids = fields.One2many('family.profile.learn', 'detainee_id', string='Education History')
    detainee_education_ids = fields.One2many(
        'family.profile.learn',
        compute="_compute_detainee_education",
        string="تعليم النزيل",
        readonly=True
    )
    detainee_issues_ids = fields.One2many(
        'issues.information',
        'detainee_id',
        string="Detainee Issues",
        related="detainee_id.issues_ids",
        readonly=True
    )
    work_type_id = fields.Many2one(
        'work.type',
        string="Workplace"
    )
    city = fields.Many2one("res.country.city", related="family_id.city", string="City", readonly=True)
    district = fields.Many2one('res.district',related="family_id.district_name", string="District")
    family_head_relation_id = fields.Many2one('family.member.relation',
        related="family_id.benefit_breadwinner_ids.relation_id",
        string='Relation ',
        readonly=True
    )
    service_cats = fields.Many2many(
        'benefits.service',
        string='Service Cat.',
        domain=lambda self: self._get_service_domain()
    )

    @api.model
    def _get_service_domain(self):
        services = self.env['benefits.service'].search([
            ('beneficiary_categories.group_guest', '=', True),
            ('active', '=', True),
        ])
        return [('id', 'in', services.ids)]
    @api.depends('detainee_id')
    def _compute_detainee_education(self):
        for rec in self:
            if rec.detainee_id and rec.detainee_id.detainee_id:
                rec.detainee_education_ids = rec.detainee_id.detainee_id.education_ids
            else:
                rec.detainee_education_ids = False
    # @api.depends('detainee_id')
    # def _compute_detainee_issues(self):
    #     for rec in self:
    #         rec.detainee_issues_ids = rec.detainee_id.issues_ids
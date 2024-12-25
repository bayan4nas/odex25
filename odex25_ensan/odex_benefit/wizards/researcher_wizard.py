# -*- coding: utf-8 -*-

from odoo import models, fields,api,_
from datetime import date

class ReasearcherMemberWizard(models.TransientModel):
    _name = 'researcher.member.wizard'

    def _default_member(self):
        return self._context.get('active_id')

    # selector = fields.Selection([
    #     ('researcher', 'Researcher'),
    #     ('researcher_team', 'Researcher Team'),
    # ], string='Selector' ,default="researcher")
    # researcher_id = fields.Many2one("hr.employee", string="Researcher")
    researcher_team = fields.Many2one("committees.line", string="Researcher Team")
    member_id = fields.Many2one("family.member", string="Member",default=_default_member)

    def submit_member(self):
        for rec in self:
            rec.member_id.state_a = "complete_info"
            # rec.member.researcher_id = rec.researcher_team.id
            # self.env['visit.location'].create({
            #     'benefit_id': rec._id.id,
            #     'visit_date': date.today(),
            #     'visit_types': 1,
            #     'contact_type': 'email',
            #     # 'selector': rec.selector,
            #     # 'researcher_id': rec.researcher_id.id,
            #     'researcher_team': rec.researcher_team.id,
            #     'state': 'draft'
            # })
class ReasearcherFamilyWizard(models.TransientModel):
    _name = 'researcher.family.wizard'

    def _default_benefit(self):
        return self._context.get('active_id')

    # selector = fields.Selection([
    #     ('researcher', 'Researcher'),
    #     ('researcher_team', 'Researcher Team'),
    # ], string='Selector' ,default="researcher")
    # researcher_id = fields.Many2one("hr.employee", string="Researcher")
    researcher_team = fields.Many2one("committees.line", string="Researcher Team",domain="[('branch_custom_id', '=',branch_custom_id)]")
    benefit_id = fields.Many2one("grant.benefit", string="Benefit",default=_default_benefit)
    branch_custom_id = fields.Many2one("branch.settings", string="Department",related="benefit_id.branch_custom_id")

    def submit_family(self):
        for rec in self:
            rec.benefit_id.state = "complete_info"
            rec.benefit_id.researcher_id = rec.researcher_team.id
            self.env['visit.location'].create({
                'benefit_id': rec.benefit_id.id,
                'visit_date': date.today(),
                'visit_types': 1,
                'contact_type': 'email',
                # 'selector': rec.selector,
                # 'researcher_id': rec.researcher_id.id,
                'researcher_team': rec.researcher_team.id,
                'state':'draft'
            })

    def send_visit_date_email(self):
        template = self.env.ref('odex_benefit.visit_date_email', False)
        if not template:
            return
        template.with_context(lang=self.env.user.lang).send_mail(self.id, force_send=True, raise_exception=False)

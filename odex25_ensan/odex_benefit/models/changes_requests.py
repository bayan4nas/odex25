from odoo import fields, models, api, _


class ChangesRequests(models.Model):
    _name = 'changes.requests'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Changes Requests'

    name = fields.Char()
    change_type = fields.Selection(
        string='Change Type',
        selection=[
            ('transfer_family_from_research_to_another_research', 'Transfer Family From Research To Another Research'),
            ('transfer_family_from_branch_to_another_branch', 'Transfer Family From Branch To Another Branch'),
            ('transfer_research_from_branch_to_another_branch', 'Transfer Research From Branch To Another Branch')],default="transfer_family_from_research_to_another_research")
    benefit_id = fields.Many2one("grant.benefit", string='Family')
    researcher_id = fields.Many2one("committees.line",compute="get_researcher_id",string='Researcher Team',store=True)
    branch_custom_id = fields.Many2one("branch.settings",compute="get_branch_id",string='Branch',store=True)
    new_branch_id = fields.Many2one("branch.settings",string='New Branch')
    new_researcher_id = fields.Many2one("committees.line", domain ="['&',('branch_custom_id','=',branch_custom_id),('id','!=',researcher_id)]",string='New Researcher Team')
    new_branch_researcher = fields.Many2one("committees.line", domain ="[('branch_custom_id','=',new_branch_id)]",string='New Researcher Team')
    execution_date = fields.Datetime(string="Transfer Execution Date")
    state = fields.Selection(
        string='State',
        selection=[
            ('draft', 'Draft'),
            ('approval_of_department_head', 'Approval of department head'),
            ('approval_of_branch_manager', 'Approval of branch manager')]
    ,default = 'draft')
    team_type = fields.Selection(
        string='Team Type',
        selection=[
            ('male', 'Male'),
            ('female', 'Female'),
            ('both', 'Both')])
    gender_researcher_id = fields.Many2one("committees.line",domain ="[('type','=',team_type)]",string='Researcher Team')
    is_whole_team = fields.Boolean(string='Is Whole Team?')
    researcher_branch_id = fields.Many2one("branch.settings",compute = "get_researcher_branch_id", store = True,string='Branch')
    new_gender_researcher_id = fields.Many2one("committees.line",domain ="['&',('branch_custom_id','=',researcher_branch_id),('id','!=',gender_researcher_id)]",string='Alternative Researcher Team for family')
    new_gender_researcher_one = fields.Many2one("committees.line",domain ="[('branch_custom_id','=',new_branch_id)]",string='Alternative Researcher Team for researcher')
    researcher_ids = fields.Many2many("hr.employee", string="Researcher",readonly=False)

    @api.onchange('gender_researcher_id')
    def item_researcher_ids_onchange(self):
        return {'domain': {'researcher_ids': [('id', 'in', self.gender_researcher_id.employee_id.ids)]}}
    @api.depends("benefit_id")
    def get_researcher_id(self):
        for rec in self:
            rec.researcher_id = rec.benefit_id.researcher_id
    @api.depends("benefit_id")
    def get_branch_id(self):
        for rec in self:
            rec.branch_custom_id = rec.benefit_id.branch_custom_id
    @api.depends("gender_researcher_id")
    def get_researcher_branch_id(self):
        for rec in self:
            rec.researcher_branch_id = rec.gender_researcher_id.branch_custom_id

    def approval_of_department_head_c1(self):
        for rec in self:
            rec.state = 'approval_of_department_head'

    def approval_of_branch_manager_c1(self):
        for rec in self:
            rec.state = 'approval_of_branch_manager'
            rec.benefit_id.researcher_id = rec.new_researcher_id
        message = "Your family has been transferred to another researcher team %s"% (self.new_researcher_id.name)
        mail = self.env['mail.mail'].create({
            'body_html': message,
            'subject': "transferred to another researcher team",
            'email_to': self.benefit_id.email,
        })
        mail.send()

    def approval_of_department_head_c2(self):
        for rec in self:
            rec.state = 'approval_of_department_head'

    def approval_of_branch_manager_c2(self):
        for rec in self:
            rec.state = 'approval_of_branch_manager'
            rec.benefit_id.branch_custom_id = rec.new_branch_id
            rec.benefit_id.researcher_id = rec.new_branch_researcher
        message = "Your family has been transferred to another branch %s" % (self.new_branch_id.name)
        mail = self.env['mail.mail'].create({
            'body_html': message,
            'subject': "Transferred to another branch",
            'email_to': self.benefit_id.email,
        })
        mail.send()
    def approval_of_department_head_c3(self):
        for rec in self:
            rec.state = 'approval_of_department_head'

    def approval_of_branch_manager_c3(self):
        obj = self.env["grant.benefit"].search([])
        for rec in self:
            rec.state = 'approval_of_branch_manager'
            rec.gender_researcher_id.branch_custom_id = rec.new_branch_id
            for item in obj.filtered(lambda r: r.researcher_id == rec.gender_researcher_id):
                item.researcher_id = rec.new_gender_researcher_id
            if rec.is_whole_team == False:
                for employee in rec.gender_researcher_id.employee_id:
                    for i in rec.researcher_ids:
                        if employee.id == i.id:
                           rec.gender_researcher_id.sudo().write({'employee_id':[(3,employee.id)]})
                           rec.new_gender_researcher_one.sudo().write({'employee_id':[(4,employee.id)]})

        message = "Your family has been transferred to another branch %s" % (self.new_branch_id.name)
        mail = self.env['mail.mail'].create({
            'body_html': message,
            'subject': "Transferred to another branch",
            'email_to': self.benefit_id.email,
        })
        mail.send()
        # for rec in self.benefit_id.researcher_id.employee_id:
        #     rec.benefit_id.researcher_id
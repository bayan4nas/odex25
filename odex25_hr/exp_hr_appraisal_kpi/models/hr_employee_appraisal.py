from odoo import models, fields, _, api, exceptions
from odoo.exceptions import UserError
from lxml import etree
import logging
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class EmployeeAppraisal(models.Model):
    _inherit = 'hr.employee.appraisal'
    name = fields.Char(string="Number", readonly=True, copy=False)
    employee_id = fields.Many2one('hr.employee', 'Employee', tracking=True, required=True)

    work_state = fields.Selection([('work', _('In work')),
                                   ('Secondment', _('Secondment')),
                                   ('legation', _('Legation')),
                                   ('depute', _('Deputation')),
                                   ('consultation', _('Consultation')),
                                   ('emission', _('Emission')),
                                   # ('delegate', _('Delegation')),
                                   ('training', _('Training')),
                                   ('others', _('others'))], 'Work Status', compute='_compute_work_state',
                                  default='work')

    manager_id = fields.Many2one('hr.employee')
    appraisal_id = fields.Many2one('hr.employee.appraisal', readonly=True)
    coach_id = fields.Many2one(related='employee_id.coach_id')
    emp_no = fields.Char(related='employee_id.emp_no', readonly=True)
    department_id = fields.Many2one('hr.department', 'Department')
    executive_id = fields.Many2one('hr.department', string='Executive Management')
    job_id = fields.Many2one('hr.job', string='Job Title')
    year_id = fields.Many2one('kpi.period', 'Appraisal Year', required=True)
    appraisal_percentage_id = fields.Many2one('job.class.apprisal', 'Job Category')
    appraisal_stage_id = fields.Many2one('goals.stages', 'Appraisal Stage')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    goal_ids = fields.One2many('years.employee.goals', 'employee_apprisal_id', ondelete='cascade', string='Goals',
                               copy=True)
    refused_goal_id = fields.Many2one('years.employee.goals', string="Refused Goal", readonly=True,tracking=1)
    refused_skill_id = fields.Many2one('skill.item.employee.table', string="Refused Skill", readonly=True,tracking=1)

    skill_ids = fields.One2many('skill.item.employee.table', 'employee_apprisal_id', ondelete='cascade',
                                string='Skills', copy=True)
    exceptional_performance_ids = fields.One2many('exceptional.performance.appraisal.line', 'employee_apprisal_id',
                                                  ondelete='cascade',
                                                  string='Exceptional Performance')
    development_plan_ids = fields.One2many('development.plan', 'employee_apprisal_id', ondelete='cascade',
                                           string='Development Plan', copy=True)
    goals_mark = fields.Float(string='Goals Appraisal Mark', compute='_compute_goals_mark', tracking=True)
    skill_mark = fields.Float(string='Skills Appraisal Mark', compute='_compute_skills_mark', tracking=True)
    total_score = fields.Float(string='Total Mark', readonly=True, compute='_compute_total_score', tracking=True)
    employee_strengths = fields.Text('Employee Strengths')
    employee_development_points = fields.Text('Employee Development Points')
    employee_comment = fields.Text('Employee Comment')
    dmanager_comment = fields.Text('Direct Manager Comment')
    executive_director_comment = fields.Text('Executive Director Comment')
    performance_officer_comment = fields.Text('Performance Officer Comment')
    performance_manager_comment = fields.Text('Performance Manager Comment')

    employee_comment_mid = fields.Text("Employee Comment")
    employee_comment_last = fields.Text("Employee Comment")
    dmanager_comment_mid = fields.Text("Direct Manager Comment")
    dmanager_comment_last = fields.Text("Direct Manager Comment")
    executive_director_comment_mid = fields.Text("Executive Director Comment")
    executive_director_comment_last = fields.Text("Executive Director Comment")
    executive_director_comment_mid = fields.Text("Executive Director Comment")
    executive_director_comment_last = fields.Text("Executive Director Comment")
    performance_manager_comment_mid = fields.Text("Performance Manager Comment")
    performance_manager_comment_last = fields.Text("Performance Manager Comment")
    performance_officer_comment_mid = fields.Text('Performance Officer Comment')
    performance_officer_comment_last = fields.Text('Performance Officer Comment')
    state = fields.Selection([
        ("draft", "Draft"), ("wait_direct_manager", "Waiting Direct Manager"),
        ("wait_employee", "Wait Employee"),
        ("wait_dept_manager", "Waiting Department Manager"),
        ("wait_performance_officer", "Waiting Performance Officer"),
        ("wait_hr_manager", "Waiting Human Resources Manager"),
        ("wait_services_manager", "Waiting Head of Shared Services"),
        ("wait_gm", "Waiting Secretary General"),
        ("closed", "Approved"), ('refused', 'Cancel'), ('cancel', 'Cancelled')
    ], default='draft', tracking=True)
    # group_appraisal_manager
    # group_appraisal_employee
    objection_state = fields.Selection([
        ("draft", "Draft"), ("wait_employee", "Wait Employee"),
        ("wait_performance_officer", "Waiting Performance Officer"),
        ("closed", "Approved"), ('refused', 'Refused')
    ], default='draft', tracking=True)

    type = fields.Selection([
        ("appraisal", "Appraisal"), ("objection", "Objection"),
        ("correction", "Correction"),
        ("exp_performance", "Exceptional performance")
    ], default='appraisal', tracking=True)
    cancel_reason = fields.Text(string="Cancel Reason", tracking=True, readonly=True)
    can_see_appraisal_result = fields.Boolean(compute="_compute_can_see_appraisal_result",
                                              string="Can See Appraisal Result", store=False)
    is_appraisal_employee = fields.Boolean(compute="_compute_is_appraisal_employee")
    is_direct_manager = fields.Boolean(compute="_compute_is_direct_manager")
    is_executive_director = fields.Boolean(compute="_compute_is_executive_director")
    is_last_stage = fields.Boolean(string="Is Last Stage", compute="_compute_is_last_stage", store=True)
    is_first_stage = fields.Boolean(string="Is Last Stage", compute="_compute_is_first_stage", store=True)
    exceptional_performance = fields.Boolean('Exceptional Performance', compute='_compute_exceptional_performance')

    objection_count = fields.Integer('# Objection Requests',
                                     compute='_compute_requests_count', compute_sudo=True)
    correction_count = fields.Integer('# KPI Correction Requests',
                                      compute='_compute_requests_count', compute_sudo=True)
    exp_performance_count = fields.Integer('# Exceptional Performance Requests',
                                           help='Number of groups that apply to the current user',
                                           compute='_compute_requests_count', compute_sudo=True)
    meeting_done = fields.Selection([('yes', 'Yes'), ('no', 'No'), ],
                                    string="Has the meeting with the employee been held and goals discussed for the year?")

    apprisal_result_display = fields.Char(string="Appraisal Result", store=False)

    def action_approve_dept_manager(self):
        self.state = 'wait_performance_officer'

    def read(self, fields=None, load='_classic_read'):
        for rec in self:
            if rec.is_first_stage:
                rec.apprisal_result_display = _("In the Performance and Development Planning Stage")

                new = self.env['appraisal.result'].create({'name': rec.apprisal_result_display})
                rec.appraisal_result = new.id
            if not rec.is_last_stage and not rec.is_first_stage:
                new = self.env['appraisal.result'].create({'name': (_("هذه المرحلة مخصصة للتغذية الراجعة"))})
                rec.appraisal_result = new.id

        return super(EmployeeAppraisal, self).read(fields, load=load)

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        user = self.env.user
        if not (user.has_group("exp_hr_appraisal.group_appraisal_manager") or user.has_group(
                "exp_hr_appraisal.group_appraisal_employee")):
            args = args + [('state', '!=', 'refused')]
        return super(EmployeeAppraisal, self).search(args, offset=offset, limit=limit, order=order, count=count)

    def action_open_cancel_wizard(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'appraisal.cancel.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self.id},
        }

    def send_to_direct_manager(self):
        for rec in self:
            rec.state = "wait_direct_manager"

    def _compute_work_state(self):

        for rec in self:
            rec.work_state = False
            if rec.employee_id:
                rec.work_state = rec.employee_id.work_state

    @api.depends('appraisal_id')
    def _compute_requests_count(self):
        for rec in self:
            rec.objection_count = self.search_count([('appraisal_id', '=', rec.id), ('type', '=', 'objection')])
            rec.correction_count = self.search_count([('appraisal_id', '=', rec.id), ('type', '=', 'correction')])
            rec.exp_performance_count = self.search_count(
                [('appraisal_id', '=', rec.id), ('type', '=', 'exp_performance')])

    @api.depends('appraisal_result')
    def _compute_exceptional_performance(self):
        for rec in self:
            if rec.appraisal_result and rec.appraisal_result.exceptional_performance:
                rec.exceptional_performance = True
            else:
                rec.exceptional_performance = False

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):

        result = super(EmployeeAppraisal, self).fields_view_get(view_id=view_id, view_type=view_type, toolbar=toolbar,
                                                                submenu=submenu)
        doc = etree.XML(result['arch'])
        for node in doc.xpath("//field[@name='total_score']"):
            node.set('attrs', "{'invisible': ['|', ('is_last_stage','=',False),('can_see_appraisal_result','=',False)]}")
            result['arch'] = etree.tostring(doc, encoding='unicode')
        for node in doc.xpath("//field[@name='appraisal_stage_id']"):
            node.set("attrs", "{'readonly': [('state','!=','draft')]}")
            result['arch'] = etree.tostring(doc, encoding='unicode')
        for node in doc.xpath("//field[@name='year_id']"):
            node.set("attrs", "{'readonly': [('state','!=','draft')]}")
            result['arch'] = etree.tostring(doc, encoding='unicode')

        if view_type == 'form' and self.env.context.get('default_type', 'appraisal') == 'objection':
            result['arch'] = self._apply_objection_state(result['arch'], view_type=view_type)
        if view_type == 'form' and self.env.context.get('default_type', 'appraisal') == 'exp_performance':
            result['arch'] = self._apply_exp_performance_state(result['arch'], view_type=view_type)
        if view_type == 'form' and self.env.context.get('default_type', 'appraisal') == 'correction':
            result['arch'] = self._apply_correction_state(result['arch'], view_type=view_type)

        return result

    @api.onchange('appraisal_stage_id','employee_id')
    def _onchange_appraisal_stage_id(self):
            print('ON...............................')
            employees_with_appraisal = self.env['hr.employee.appraisal'].search([('is_first_stage', '=', True) ]).mapped('employee_id').ids
            print('employees_with_appraisal = ',employees_with_appraisal)
            return {
                'domain': {
                    'employee_id': [('id', 'not in', employees_with_appraisal)]
                }
            }

    @api.constrains('employee_id', 'appraisal_stage_id')
    def _check_unique_employee_stage(self):
        for rec in self:
            if rec.employee_id and rec.appraisal_stage_id:
                duplicate = self.search([
                    ('employee_id', '=', rec.employee_id.id),
                    ('appraisal_stage_id', '=', rec.appraisal_stage_id.id),
                    ('id', '!=', rec.id),
                ], limit=1)
                if duplicate:
                    pass
                    # raise ValidationError(_('This employee already has an appraisal in the same stage.'))

    @api.model
    def _apply_objection_state(self, view_arch, view_type='form'):
        doc = etree.XML(view_arch)
        for node in doc.xpath("//field[@name='state']"):
            node.set('statusbar_visible', "draft,wait_performance_officer,closed,refused")

        return etree.tostring(doc, encoding='unicode')

    @api.model
    def _apply_exp_performance_state(self, view_arch, view_type='form'):
        doc = etree.XML(view_arch)
        for node in doc.xpath("//field[@name='state']"):
            node.set('statusbar_visible',
                     "draft,wait_dept_manager,wait_performance_officer,wait_hr_manager,wait_services_manager,wait_gm,closed,refused")
        return etree.tostring(doc, encoding='unicode')

    @api.model
    def _apply_correction_state(self, view_arch, view_type='form'):
        doc = etree.XML(view_arch)
        for node in doc.xpath("//field[@name='state']"):
            node.set('statusbar_visible',
                     "draft,wait_dept_manager,wait_performance_officer,wait_hr_manager,closed,refused")
        return etree.tostring(doc, encoding='unicode')

    @api.depends('appraisal_stage_id')
    def _compute_is_last_stage(self):
        for item in self:
            last_stage_record = self.env['goals.stages'].search([
                ('period_id', '=', item.appraisal_stage_id.period_id.id)
            ], order="sequence desc", limit=1)
            item.is_last_stage = item.appraisal_stage_id.id == last_stage_record.id if last_stage_record else False

    @api.depends('appraisal_stage_id')
    def _compute_is_first_stage(self):
        for item in self:
            first_stage_record = self.env['goals.stages'].search([
                ('period_id', '=', item.appraisal_stage_id.period_id.id)
            ], order="sequence ASC", limit=1)
            item.is_first_stage = item.appraisal_stage_id.id == first_stage_record.id if first_stage_record else False

    @api.depends('employee_id', 'state')
    def _compute_can_see_appraisal_result(self):
        for record in self:
            user = self.env.user
            if user.has_group('exp_hr_appraisal.group_appraisal_manager') or user.has_group(
                    'exp_hr_appraisal.group_appraisal_employee') \
                    or user.has_group('exp_hr_appraisal.group_kpi_executive_director'):
                record.can_see_appraisal_result = True
                continue
            if record.state == 'closed' and user.employee_id == record.employee_id:
                record.can_see_appraisal_result = True
                continue
            if record.state not in ['draft', 'wait_employee'] and record.employee_id.parent_id == user.employee_id:
                record.can_see_appraisal_result = True
                continue
            record.can_see_appraisal_result = False

    def _compute_is_appraisal_employee(self):
        for record in self:
            user = self.env.user
            # Check if the user is an administrator
            if user.has_group('base.group_system'):
                record.is_appraisal_employee = True
            else:
                is_employee = record.employee_id.user_id == user
                record.is_appraisal_employee = is_employee

    def _compute_is_direct_manager(self):
        direct_manager_group = self.env.ref("hr_base.group_division_manager")
        for record in self:
            user = self.env.user
            if user.has_group('base.group_system'):
                record.is_direct_manager = True
            else:
                is_manager = record.sudo().employee_id.parent_id.user_id == user
                is_employee = record.employee_id.user_id == user
                in_manager_group = direct_manager_group in user.groups_id
                record.is_direct_manager = is_manager and not (is_employee and in_manager_group)

    def _compute_is_executive_director(self):
        executive_director_group = self.env.ref("exp_hr_appraisal.group_kpi_executive_director")
        for record in self:
            user = self.env.user
            if user.has_group('base.group_system'):
                record.is_executive_director = True
            else:
                is_manager = record.sudo().employee_id.parent_id.parent_id.user_id == user
                is_employee = record.employee_id.user_id == user
                in_manager_group = executive_director_group in user.groups_id
                record.is_executive_director = is_manager and not (is_employee and in_manager_group)

    def performance_officer_email_message(self, group=None, user=None):
        template = self.env.ref('exp_hr_appraisal_kpi.email_template_appraisal_request_performance_officer')
        if group:
            users = group.users.filtered(lambda u: u.partner_id.email)
            for partner in users.mapped('partner_id'):
                try:
                    if template:
                        template.with_context(recipient_name=partner.name).sudo().send_mail(
                            self.id,
                            force_send=True,
                            email_values={'email_to': partner.email, 'partner_ids': [partner.id]})
                except Exception as e:
                    _logger.error(f"Failed to send email: {e}")

    def send_manager_notification(self):
        Mail = self.env['mail.template']
        template = self.env.ref('exp_hr_appraisal_kpi.email_template_appraisal_request_manager')
        for record in self:
            if record.employee_id:
                try:
                    self.flush()
                    Mail.browse(template.id).send_mail(record.id, force_send=True)
                except Exception as e:
                    _logger.error(f"SMTP Error: {str(e)} - Retrying...")
                    self.env.cr.rollback()  # Rollback any uncommitted transactions
                    Mail.browse(template.id).send_mail(record.id, force_send=True)  # Retry

    def send_executive_director_notification(self):
        Mail = self.env['mail.template']
        template = self.env.ref('exp_hr_appraisal_kpi.email_template_appraisal_request_executive_director')
        for record in self:
            try:
                if record.employee_id:
                    self.flush()
                    Mail.browse(template.id).send_mail(record.id, force_send=True)
            except Exception as e:
                _logger.error(f"SMTP Error: {str(e)} - Retrying...")
                self.env.cr.rollback()  # Rollback any uncommitted transactions
                Mail.browse(template.id).send_mail(record.id, force_send=True)  # Retry

    def sent_appraisal_to_employee(self):
        user = self.env.user
        if not self.development_plan_ids:
            raise ValidationError(_("You must add at least one Development Plan."))
        if not self.goal_ids:
            raise ValidationError(_("You must add at least one Goal."))
        if not self.skill_ids:
            raise ValidationError(_("You must add at least one Skill."))
        for goal in self.goal_ids:
            if goal.weight == 0:
                raise ValidationError(
                    _("Direct Manager: Weight for goals cannot be 0%%. Please assign a valid percentage."))
        for skill in self.skill_ids:
            if skill.skill_weight == 0:
                raise ValidationError(
                    _("Direct Manager: Weight for skills cannot be 0%%. Please assign a valid percentage."))

        is_direct_manager = self.employee_id.parent_id.user_id == user
        in_allowed_group = (user.has_group('exp_hr_appraisal.group_appraisal_manager') or user.has_group(
            'exp_hr_appraisal.group_appraisal_employee'))

        if not (is_direct_manager or in_allowed_group):
            raise UserError(
                _("You cannot move this evaluation to this stage unless you are the employee's direct manager."))
        for record in self:
            if not record.year_id:
                raise exceptions.ValidationError(_("Please select an Appraisal Year before submitting."))

            num_goals = len(record.goal_ids)
            min_no_goals, max_no_goals = record.appraisal_percentage_id.min_no_goals, record.appraisal_percentage_id.max_no_goals
            min_goal_weight, max_goal_weight = record.appraisal_percentage_id.min_goal_weight, record.appraisal_percentage_id.max_goal_weight

            if not (min_no_goals <= num_goals <= max_no_goals):
                raise exceptions.ValidationError(_(
                    "The number of goals must be between %(min)d and %(max)d. You currently have %(current)d goals."
                ) % {'min': min_no_goals, 'max': max_no_goals, 'current': num_goals})

            if any(not (min_goal_weight <= goal.weight <= max_goal_weight) for goal in record.goal_ids):
                pass
                # raise exceptions.ValidationError(_("Each goal's weight must be between %(min)d and %(max)d.")
                #                                  % {'min': min_goal_weight, 'max': max_goal_weight})

            if sum(goal.weight for goal in record.goal_ids) != 100:
                raise exceptions.ValidationError(_("Total goal weight must be exactly 100."))

            if sum(skill.skill_weight for skill in record.skill_ids) != 100:
                raise exceptions.ValidationError(_("Total skill weight must be exactly 100."))

            for rec in record.appraisal_percentage_id.skill_percentage_ids:
                if sum(skill.skill_weight for skill in record.skill_ids if
                       skill.skill_type_id in rec.skill_type_ids) != rec.skill_percentage:
                    name = ''
                    for typ in rec.skill_type_ids:
                        name = name + "-" + typ.name
                    raise exceptions.Warning(
                        _('percentage of  "%s" must be "%s" ') % (name, rec.skill_percentage))
            template = self.env.ref('exp_hr_appraisal_kpi.email_template_appraisal_request_employee')
            try:
                template.send_mail(record.id, force_send=True)  # force_send=True sends the email immediately
            except Exception as e:
                _logger.error(f"Failed to send email: {e}")
            record.state = 'wait_employee'

    def re_send_to_employee(self):
        self.state = 'wait_employee'

    def send_to_executive_director(self):
        for record in self.goal_ids:
            if not record.done or record.done == 0:
                raise exceptions.ValidationError(_("The manager's rating must be entered before submitting"))
        for record in self.skill_ids:
            if not record.mark or record.mark == 0:
                raise exceptions.ValidationError(_("The manager's rating must be entered before submitting"))
        self.send_executive_director_notification()
        self.state = 'wait_executive_director'

    def send_to_dmanager(self):
        self.state = 'wait_dept_manager'

    def send_to_performance_officer(self):
        if self.manager_id.parent_id.user_id != self.env.user:
            raise ValidationError(_("You are not the direct manager of this employee, so you cannot proceed."))
        self.state = 'wait_performance_officer'

    def send_hr_manager(self):
        self.state = 'wait_hr_manager'

    def send_services_manager(self):
        self.state = 'wait_services_manager'

    def send_to_gm(self):
        self.state = 'wait_gm'

    def objection_request(self):
        self.ensure_one()
        objection_request = self.copy({
            'appraisal_id': self.id,
            'appraisal_date': fields.Date.today(),
            'state': 'draft',
            'type': 'objection'})
        action = self.env['ir.actions.actions']._for_xml_id('exp_hr_appraisal_kpi.hr_objection_action')
        action['domain'] = [('id', '=', objection_request.id), ('type', '=', 'objection')]
        return action

    def kpi_correction_request(self):
        self.ensure_one()
        objection_request = self.copy({
            'appraisal_id': self.id,
            'appraisal_date': fields.Date.today(),
            'state': 'draft',
            'type': 'correction'})
        action = self.env['ir.actions.actions']._for_xml_id('exp_hr_appraisal_kpi.hr_correction_action')
        action['domain'] = [('id', '=', objection_request.id), ('type', '=', 'correction')]
        return action

    def exceptional_performance_request(self):
        self.ensure_one()
        objection_request = self.copy({
            'appraisal_id': self.id,
            'appraisal_date': fields.Date.today(),
            'state': 'draft',
            'type': 'exp_performance'})
        if self.appraisal_result.template_id:
            for line in self.appraisal_result.template_id.exceptional_performance_ids:
                record = self.env['exceptional.performance.appraisal.line'].create({
                    'name': line.name,
                    'employee_apprisal_id': objection_request.id,
                    'standard_id': line.standard_id.id, })
        action = self.env['ir.actions.actions']._for_xml_id('exp_hr_appraisal_kpi.hr_exp_performance_action')
        action['domain'] = [('id', '=', objection_request.id), ('type', '=', 'exp_performance')]
        return action

    def action_show_objection_request(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id('exp_hr_appraisal_kpi.hr_objection_action')
        action['domain'] = [('appraisal_id', '=', self.id), ('type', '=', 'objection')]
        return action

    def action_show_correction_request(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id('exp_hr_appraisal_kpi.hr_correction_action')
        action['domain'] = [('appraisal_id', '=', self.id), ('type', '=', 'correction')]
        return action

    def action_show_exp_performance_request(self):
        self.ensure_one()
        action = self.env['ir.actions.actions']._for_xml_id('exp_hr_appraisal_kpi.hr_exp_performance_action')
        action['domain'] = [('appraisal_id', '=', self.id), ('type', '=', 'exp_performance')]
        return action

    def approve(self):
        GoalStages = self.env['goals.stages']
        YearsEmployeeGoals = self.env['years.employee.goals']
        EmployeeSkills = self.env['skill.item.employee.table']
        MailTemplate = self.env['mail.template']
        template = self.env.ref('exp_hr_appraisal_kpi.email_template_appraisal_result', raise_if_not_found=False)

        for item in self:
            if item.type == 'appraisal':
                stage = item.appraisal_stage_id
                if stage:
                    last_stage = GoalStages.search(
                        [('period_id', '=', stage.period_id.id)],
                        order="sequence desc", limit=1
                    )

                    if stage.id == last_stage.id:
                        contract = item.employee_id.contract_id
                        if not contract:
                            raise UserError(
                                'There is no contract for employee "%s" to update appraisal result ' %
                                item.employee_id.name
                            )
                        if item.appraisal_result:
                            contract.appraisal_result_id = item.appraisal_result

                if item.is_last_stage and item.employee_id and template:
                    template.sudo().send_mail(item.id, force_send=True)

            elif item.type == 'objection':

                for goal in item.goal_ids:
                    if goal.approved > 0 and goal.approved != goal.done:
                        appraisal_goal = YearsEmployeeGoals.search([
                            ('employee_apprisal_id', '=', item.appraisal_id.id),
                            ('kpi_id', '=', goal.kpi_id.id)
                        ], limit=1)
                        if appraisal_goal:
                            appraisal_goal.write({'done': goal.approved})

                for skill in item.skill_ids:
                    if skill.approved and skill.approved != skill.mark:
                        appraisal_skill = EmployeeSkills.search([
                            ('employee_apprisal_id', '=', item.appraisal_id.id),
                            ('skill_id', '=', skill.skill_id.id)
                        ], limit=1)
                        if appraisal_skill:
                            appraisal_skill.write({'mark': skill.approved})

            item.state = 'closed'

    def refused(self):
        if self.state == 'wait_employee':
            return {
                'name': (_("Refuse Appraisal")),
                'type': 'ir.actions.act_window',
                'res_model': 'appraisal.refuse.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_appraisal_id': self.id},
            }
        else:
            self.state = 'refused'



    _sql_constraints = [
        ('appraisal', 'UNIQUE (id)', 'Employee Appraisal must be unique per Employee, Year, and Stage !')
    ]

    @api.constrains('employee_id', 'year_id')
    def check_unique_employee_year_period_goals(self):
        for record in self:
            if record.type == 'appraisal' and self.search_count([
                ('employee_id', '=', record.employee_id.id),
                ('year_id', '=', record.year_id.id),
                ('appraisal_stage_id', '=', record.appraisal_stage_id.id),
                ('type', '=', 'appraisal'),
                ('id', '!=', record.id),
            ]) > 0:
                raise exceptions.ValidationError(_("Employee Appraisal must be unique per Employee, Year, and Stage !"))

    @api.constrains('appraisal_date', 'year_id')
    def _check_appraisal_date_within_year(self):
        for record in self:
            if record.appraisal_date and record.year_id:
                if not (record.year_id.date_start <= record.appraisal_date <= record.year_id.date_end):
                    raise exceptions.ValidationError(
                        _("The appraisal date must be within the selected year period: %s to %s") %
                        (record.year_id.date_start, record.year_id.date_end))

    @api.onchange('year_id', 'appraisal_date')
    def onchange_period(self):
        if self.year_id:
            appraisal_stage = self.env['goals.stages'].search([
                ('period_id', '=', self.year_id.id),
                ('start_date', '<=', self.appraisal_date),
                ('end_date', '>=', self.appraisal_date)
            ], limit=1)
            if appraisal_stage:
                self.appraisal_stage_id = appraisal_stage.id
        else:
            self.appraisal_stage_id = False

    @api.onchange('employee_id')
    def onchange_emp_job(self):
        for rec in self:
            rec.job_id = rec.employee_id.job_id.id
            rec.manager_id = rec.employee_id.parent_id
            rec.department_id = rec.employee_id.department_id.id
            rec.executive_id = rec.department_id.parent_id

    @api.onchange('job_id', 'employee_id')
    def onchange_emp(self):
        if self.job_id:
            appraisal_percentage = self.env['job.class.apprisal'].search([
                ('job_ids', 'in', self.job_id.id)], limit=1)
            self.appraisal_percentage_id = appraisal_percentage

        self.skill_ids = [(5, 0, 0)]
        item_lines = []
        for line in self.job_id.item_job_ids:
            line_item = {
                'item_id': line.item_id.id if line.item_id else False,
                'name': line.name,
                'skill_id': line.skill_id.id,
                'target': line.level,
                'skill_type_id': line.skill_type_id.id if line.skill_type_id else False
            }
            item_lines.append((0, 0, line_item))
        self.skill_ids = item_lines

    @api.depends('goal_ids', 'goal_ids.kpi_result')
    def _compute_goals_mark(self):
        for record in self:
            total_mark = 0.0
            for kpi in record.goal_ids:
                total_mark += kpi.kpi_result
            record.goals_mark = total_mark

    @api.depends('skill_ids', 'skill_ids.skill_result')
    def _compute_skills_mark(self):
        for record in self:
            total_mark = 0.0
            for skill in record.skill_ids:
                total_mark += skill.skill_result
            record.skill_mark = total_mark

    @api.depends('goal_ids.kpi_result', 'appraisal_percentage_id')
    def _compute_total_score(self):
        appraisal_result_list = []
        for rec in self:
            skill_mark_percentage = rec.skill_mark * rec.appraisal_percentage_id.percentage_skills
            goal_mark_percentage = rec.goals_mark * rec.appraisal_percentage_id.percentage_kpi
            rec.total_score = skill_mark_percentage + goal_mark_percentage
            if rec.goals_mark == 100:
                for kpi in rec.goal_ids:
                    rec.total_score += kpi.exceeds
            appraisal_result = self.env['appraisal.result'].search([
                ('result_from', '<', rec.total_score),
                ('result_to', '>=', rec.total_score)])
            if rec.total_score and len(appraisal_result) > 1:
                for line in appraisal_result:
                    appraisal_result_list.append(line.name)
                raise exceptions.Warning(
                    _('Please check appraisal result configuration , there is more than result for '
                      'percentage %s  are %s ') % (
                        round(rec.total_score, 2), appraisal_result_list))
            else:
                rec.appraisal_result = appraisal_result.id

    def unlink(self):
        for appraisal in self:
            appraisal.goal_ids.unlink()
            appraisal.skill_ids.unlink()
        return super(EmployeeAppraisal, self).unlink()

    @api.model
    def create(self, vals):
        # Get year (last 2 digits)
        year_prefix = fields.Date.today().strftime('%y')

        if vals.get("is_first_stage"):
            vals["name"] = self.env["ir.sequence"].next_by_code("appraisal.plan.seq") or "/"
        elif vals.get("is_last_stage"):
            vals["name"] = self.env["ir.sequence"].next_by_code("appraisal.final.seq") or "/"
        else:
            vals["name"] = self.env["ir.sequence"].next_by_code("appraisal.mid.seq") or "/"
        # Add year prefix manually if not already in the sequence
        return super(EmployeeAppraisal, self).create(vals)

    def draft(self):
        for item in self:
            if item.employee_id.contract_id.appraisal_result_id:
                item.employee_id.contract_id.appraisal_result_id = False

            if item.state == 'wait_dept_manager':
                item.state = 'wait_direct_manager'
            else:
                item.state = 'draft'


class SkillItems(models.Model):
    _name = 'skill.item.employee.table'

    sequence = fields.Integer(string="Sequence", default=1, compute='_compute_sequences')
    employee_apprisal_id = fields.Many2one(comodel_name='hr.employee.appraisal')
    item_id = fields.Many2one(comodel_name='item.item', string='Item')
    skill_type_id = fields.Many2one('skill.type')
    skill_id = fields.Many2one('skill.skill', string='Skill')
    name = fields.Text(related='skill_id.description', readonly=False, string='Description')
    state = fields.Selection(related='employee_apprisal_id.state')
    is_last_stage = fields.Boolean(related='employee_apprisal_id.is_last_stage')
    is_direct_manager = fields.Boolean(related='employee_apprisal_id.is_direct_manager')
    is_appraisal_employee = fields.Boolean(related='employee_apprisal_id.is_appraisal_employee')
    can_see_appraisal_result = fields.Boolean(related='employee_apprisal_id.can_see_appraisal_result')
    self_assessment = fields.Selection([('1', '1'), ('2', '2'), ('3', '3')], string='Self Assessment')
    approved = fields.Selection([('1', '1'), ('2', '2'), ('3', '3')], string='Approved')
    mark = fields.Selection([('1', '1'), ('2', '2'), ('3', '3')], string='SCurrent Skill Apprisal')
    apprisal_start_year = fields.Selection([('0', '0'), ('1', '1'), ('2', '2'), ('3', '3')], default='0',
                                           string='Start Year Skill Apprisal')
    target = fields.Selection([('1', '1'), ('2', '2'), ('3', '3')], string='Target')
    level_id = fields.Many2one('skill.level', string='Target')
    skill_weight = fields.Integer(string="Weight")
    skill_result = fields.Float(string='Result', compute="_compute_skill_result",
                                store=True, help="Calculated as (sum of marks / number of items) * skill weight")
    remarks = fields.Text(string="Apprisal Remarks")
    comments = fields.Text(string="General Comments")
    appraiser_comments = fields.Selection([
        ('achieved', 'Achieved The Target"'),
        ('remedied', 'Below target can be remedied'),
        ('below', 'Below Target')], string='Appraiser Comments')

    def _compute_sequences(self):
        # Reorder skills
        for idx, line in enumerate(self.employee_apprisal_id.skill_ids, start=1):
            line.sequence = idx

    def unlink(self):
        for rec in self:
            if rec.employee_apprisal_id.state == "wait_direct_manager":
                raise ValidationError(_("You cannot delete a record in This state."))

    @api.onchange('skill_type_id')
    def _onchange_skill_type(self):
        domain = {}
        if self.skill_type_id:
            # ALL SKILLS as same type
            domain['skill_id'] = [('skill_type_id', '=', self.skill_type_id.id)]
            if self.employee_apprisal_id:
                used_skills = self.employee_apprisal_id.skill_ids.filtered(
                    lambda r: r.skill_type_id == self.skill_type_id
                ).mapped('skill_id').ids
                domain['skill_id'].append(('id', 'not in', used_skills))

        return {'domain': domain}

    @api.depends('mark', 'skill_weight', 'target')
    def _compute_skill_result(self):
        for record in self:
            result = 0.0
            if record.target:
                result = float(record.mark) * record.skill_weight / float(record.target)
            record.skill_result = min(round(result, 0), record.skill_weight)

    @api.onchange('skill_id')
    def _onchange_skill_id(self):
        if self.skill_id:
            skill_items = self.env['skill.item'].search([('skill_id', '=', self.skill_id.id)])
            item_ids = skill_items.mapped('item_id').ids
            return {'domain': {'item_id': [('id', 'in', item_ids)]}}
        return {'domain': {'item_id': []}}

    # def unlink(self):
    #     for record in self:
    #         if record.is_appraisal_employee:
    #             raise exceptions.ValidationError(_("Sorry, you are not allowed to delete skills"))
    #     return super(SkillItems, self).unlink()


class DevelopmentMethods(models.Model):
    _name = 'development.methods'

    name = fields.Char(string='Name')
    description = fields.Text(string='Description')


class DevelopmentPlan(models.Model):
    _name = 'development.plan'

    sequence = fields.Integer(compute='_compute_sequences', string="Sequence", default=1)
    employee_apprisal_id = fields.Many2one(comodel_name='hr.employee.appraisal')
    name = fields.Text(related='development_method_id.description', string='Description')
    development_method_id = fields.Many2one('development.methods', string='Development Methods', required=True)
    needs = fields.Selection([('yes', 'Yes'), ('no', 'No')], string='Needs', default='no', required=True)
    suggestions = fields.Text(string='Suggestions')

    def _compute_sequences(self):
        # Reorder goals
        # Reorder development plans
        for idx, line in enumerate(self.employee_apprisal_id.development_plan_ids, start=1):
            line.sequence = idx

    @api.onchange('development_method_id')
    def _onchange_development_method_id(self):
        selected_development_method_id = self.employee_apprisal_id.development_plan_ids.mapped(
            'development_method_id.id')
        return {'domain': {'development_method_id': [('id', 'not in', selected_development_method_id)]}}


class ExceptionalPerformanceTemplate(models.Model):
    _name = 'exceptional.performance.template'

    name = fields.Char(string='Name')
    description = fields.Text(string='Description')
    exceptional_performance_ids = fields.One2many('exceptional.performance.template.line', 'template_id',
                                                  ondelete='cascade',
                                                  string='Exceptional Performance', copy=True)


class ExceptionalPerformanceStandards(models.Model):
    _name = 'exceptional.performance.standards'

    name = fields.Char(string='Name')


class ExceptionalPerformanceTemplateLine(models.Model):
    _name = 'exceptional.performance.template.line'

    name = fields.Char(string='Supporting Questions')
    template_id = fields.Many2one(comodel_name='exceptional.performance.template')
    standard_id = fields.Many2one(comodel_name='exceptional.performance.standards')


class ExceptionalPerformanceAppraisal(models.Model):
    _name = 'exceptional.performance.appraisal.line'

    name = fields.Char(string='Supporting Questions')
    description = fields.Text(string='Direct Manager Visuals')
    employee_apprisal_id = fields.Many2one(comodel_name='hr.employee.appraisal')
    standard_id = fields.Many2one(comodel_name='exceptional.performance.standards')


class AppraisalResult(models.Model):
    _inherit = 'appraisal.result'

    exceptional_performance = fields.Boolean(string="Exceptional Performance")
    template_id = fields.Many2one(comodel_name='exceptional.performance.template')


class YearsEmployeeGoals(models.Model):
    _inherit = "years.employee.goals"

    sequence = fields.Integer(compute='_compute_sequences', string="Sequence", default=1)

    def _compute_sequences(self):
        # rder goals
        for idx, line in enumerate(self.employee_apprisal_id.goal_ids, start=1):
            line.sequence = idx

    def unlink(self):
        for rec in self:
            if rec.employee_apprisal_id.state == "wait_direct_manager":
                raise ValidationError(_("You cannot delete a record in This state."))


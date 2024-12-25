import werkzeug

from odoo.exceptions import AccessDenied
from odoo import api, models, fields, SUPERUSER_ID

import logging

_logger = logging.getLogger(__name__)

from ..validator import validator


class Users(models.Model):
    _inherit = "res.users"

    access_token_ids = fields.One2many(
        string="Access Tokens",
        comodel_name="jwt_provider.access_token",
        inverse_name="user_id",
    )

    avatar = fields.Char(compute="_compute_avatar")
    # is_verified = fields.Boolean("Verified" , default=False)

    @classmethod
    def _login(cls, db, login, password, user_agent_env):
        user_id = super(Users, cls)._login(
            db, login, password, user_agent_env=user_agent_env
        )
        if user_id:
            return user_id
        uid = validator.verify(password)
        return uid

    @api.model
    def check_credentials(self, password):
        try:
            super(Users, self).check_credentials(password)
        except AccessDenied:
            # verify password as token
            if not validator.verify(password):
                raise

    @api.depends("image_1024")
    def _compute_avatar(self):
        base = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        for u in self:
            # u.avatar = werkzeug.urls.url_join(base, "rest_api/web/avatar/%d" % u.id)
            u.avatar = werkzeug.urls.url_join(base, "api/content/res.users/%d/image_1920" % u.id)
            if u.employee_id and u.employee_id.image_1920:
                u.avatar = werkzeug.urls.url_join(base, "/api/content?model=hr.employee&id=%d&field=image_1920&unique=" % u.employee_id.id)
    # @api.multi
    def to_dict(self, single=False):
        res = []
        for u in self:
            d = u.read(["email", "name", "avatar", "mobile", "phone", "partner_id"])[0]
            d["user_id"] = self.id
            d["partner_id"] = self.partner_id.id
            d["lang"] = self.partner_id.lang
            groups = self.user_groups()
            d["groups"] = groups
            employee = (
                self.env["hr.employee"]
                .sudo()
                .search([("user_id", "=", self.id)], limit=1)
            )
            attendance_status = validator.get_attendance_check(employee)
            d["job"] = employee.job_id.name if employee and employee.job_id else None
            d["employe_id"] = employee.id if employee and employee.id else None
            d["attendance_status"] = attendance_status if attendance_status else None
            d['is_approve'] = 'group_division_manager' in d.get('groups',[])
            res.append(d)

        return res[0] if single else res

    def user_groups(self):
        groups = []
        if self.has_group("base.group_user"):
            groups.append("group_user")
        if self.has_group("hr_base.group_division_manager"):
            groups.append("group_division_manager")
        if self.has_group("hr.group_hr_manager"):
            groups.append("group_hr_manager")
        if self.has_group("hr_base.group_executive_manager"):
            groups.append("group_executive_manager")
        if self.has_group("hr_loans_salary_advance.group_loan_user"):
            groups.append("group_loan_user")
        if self.has_group("hr_base.group_general_manager"):
            groups.append("group_general_manager")
        if self.has_group("hr_base.group_account_manager"):
            groups.append("group_account_manager")
        if self.has_group("hr.group_hr_user"):
            groups.append("group_hr_user")
        if self.has_group("hr_timesheet.group_timesheet_manager"):
            groups.append("group_timesheet_manager")
        if self.has_group("hr_holidays.group_hr_holidays_user"):
            groups.append("group_hr_holidays_user")
        if self.has_group("hr_base.group_department_manager"):
            groups.append("group_department_manager")

        return groups


    @api.model
    def create(self, vals):
        res = super(Users, self).create(vals)
        if 'password' in vals or vals.get('active') is False:
            self._invalidate_tokens(res)
        return res

    def write(self, vals):
        result = super(Users, self).write(vals)
        if 'password' in vals or 'active' in vals and not vals['active']:
            self._invalidate_tokens(self)
        return result

    def _invalidate_tokens(self, users):
        token_model = self.env['jwt_provider.access_token']
        for user in users:
            token_model.search([('user_id', '=', user.id)]).unlink()

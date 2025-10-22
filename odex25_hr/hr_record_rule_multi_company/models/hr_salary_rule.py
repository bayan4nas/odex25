from odoo import models, fields, api

class HrSalary(models.Model):
    _inherit = 'hr.salary.rule'
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
        readonly=True

    )
    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        if not self.env.su:
            user_company_ids = self.env.user.company_ids.ids
            company_domain = [('company_id', 'in', user_company_ids)]
            args = args + company_domain
        return super(HrSalary, self).search(args, offset=offset, limit=limit, order=order, count=count)

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):

        if not self.env.context.get('skip_company_check'):
            company_domain = [('company_id', 'in', self.env.user.company_ids.ids)]
            domain = (domain or []) + company_domain

        return super(HrSalary, self).search_read(
            domain, fields, offset, limit, order
        )
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        if not self.env.su:
            user_company_ids = self.env.user.company_ids.ids
            args = args + [('company_id', 'in', user_company_ids)]
        return super(HrSalary, self).name_search(name=name, args=args, operator=operator, limit=limit)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        if not self.env.su:
            user_company_ids = self.env.user.company_ids.ids
            company_domain = [('company_id', 'in', user_company_ids)]
            domain = domain + company_domain
        return super(HrSalary, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby, lazy=lazy)
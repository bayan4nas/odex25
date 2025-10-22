from odoo import models, fields, api


class HrEmp(models.Model):
    _inherit = 'hr.employee'

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
        readonly=True
    )

    def _get_active_company_domain(self):
        if self.env.su:
            return []

        active_company_ids = self.env.context.get('allowed_company_ids', [])
        if not active_company_ids:
            active_company_ids = self.env.companies.ids

        return [('company_id', 'in', active_company_ids)]

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        company_domain = self._get_active_company_domain()
        if company_domain:
            args = args + company_domain
        return super(HrEmp, self).search(args, offset=offset, limit=limit, order=order, count=count)

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        if not self.env.context.get('skip_company_check'):
            company_domain = self._get_active_company_domain()
            if company_domain:
                domain = (domain or []) + company_domain

        return super(HrEmp, self).search_read(
            domain, fields, offset, limit, order
        )

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        company_domain = self._get_active_company_domain()
        if company_domain:
            args = args + company_domain
        return super(HrEmp, self).name_search(name=name, args=args, operator=operator, limit=limit)

    @api.model
    def read_group(self, domain, fields, groupby, offset=0, limit=None, orderby=False, lazy=True):
        company_domain = self._get_active_company_domain()
        if company_domain:
            domain = domain + company_domain
        return super(HrEmp, self).read_group(domain, fields, groupby, offset=offset, limit=limit, orderby=orderby,
                                             lazy=lazy)

    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        company_domain = self._get_active_company_domain()
        if company_domain:
            args = args + company_domain
        return super(HrEmp, self)._search(args, offset=offset, limit=limit, order=order, count=count,
                                          access_rights_uid=access_rights_uid)

    @api.model
    def web_search_read(self, domain=None, fields=None, offset=0, limit=None, order=None):
        company_domain = self._get_active_company_domain()
        if company_domain:
            domain = (domain or []) + company_domain
        return super(HrEmp, self).web_search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order)

    @api.model
    def name_create(self, name):
        return super(HrEmp, self).name_create(name)

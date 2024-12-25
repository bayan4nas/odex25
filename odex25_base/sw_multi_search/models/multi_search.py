# -*- coding: utf-8 -*-

import logging
_logger = logging.getLogger(__name__)

from odoo.osv import expression
from odoo.osv.query import Query
from odoo.models import BaseModel, api
from odoo import models


class Base(models.AbstractModel):
    _inherit = 'base'
    
    @api.model
    def _search(self, args, offset=0, limit=None, order=None, count=False, access_rights_uid=None):
        new_args = []
        for domain in args:
            if len(domain) == 3 and type(domain[2]) is str and  domain[2].startswith('{') and domain[2].endswith('}'):
                field, op, val = domain
                lop = (op.startswith('!') or op.startswith('not')) and '&' or '|'
                val = val[1:-1]
                new_domain = []
                for v in val.split():
                    new_domain.extend([lop, (field, op, v)])
                new_domain and new_domain.pop(-2)
                new_args.extend(new_domain)
            else:
                new_args.append(domain)
        return super(Base, self)._search(new_args, offset, limit, order, count, access_rights_uid)


# # TODO: ameliorer avec NULL
@api.model
def _where_calc(self, domain, active_test=True):
    """Computes the WHERE clause needed to implement an OpenERP domain.
    :param domain: the domain to compute
    :type domain: list
    :param active_test: whether the default filtering of records with ``active``
                        field set to ``False`` should be applied.
    :return: the query expressing the given domain as provided in domain
    :rtype: osv.query.Query
    """
    if 'active' in self._fields and active_test and self._context.get('active_test', True):
        if not any(item[0] == 'active' for item in domain):
            domain = [('active', '=', 1)] + domain
    self.env.cr.execute("SELECT id FROM ir_module_module WHERE name='sw_multi_search' and state='installed' limit 1")
    is_multi_search_installed = self.env.cr.fetchone()
    if domain:
        modified_domain = []
        for domain_tuple in domain:
            flag = False
            if not is_multi_search_installed:
                modified_domain.append(domain_tuple)
                continue
            if type(domain_tuple) in (list, tuple):
                if domain_tuple[2]:
                    filter_value_str = u" ".join(str(domain_tuple[2]).replace('\\', '_').split())
                    if filter_value_str[-1] == '%':
                        filter_value_str = filter_value_str[:-1]
                        flag = True
                    if filter_value_str.startswith('{') and filter_value_str.endswith('}'):
                        _logger.info('Parsing the domain filter value for multi-search condition ')
                        try:
                            filter_value = [x.strip() for x in filter_value_str.replace('{', '').replace('}', '').split()]
                            if type(filter_value) in (list, tuple):
                                custom_domain_filter_tuples = []
                                values_count = len(filter_value)
                                iteration = 0
                                for val in filter_value:
                                    iteration += 1
                                    if iteration < values_count:
                                        custom_domain_filter_tuples.append('|')
                                    if not flag:
                                        custom_domain_filter_tuples.append((domain_tuple[0], domain_tuple[1], str(val)))
                                    else:
                                        custom_domain_filter_tuples.append((domain_tuple[0], domain_tuple[1], str(val) + '%'))
                                modified_domain.extend(custom_domain_filter_tuples)
                                continue
                        except:
                            _logger.error('Error occured while enhancing the supplied domain filter') 
            modified_domain.append(domain_tuple)
        e = expression.expression(modified_domain, self)
        tables = e.get_tables()
        q = e.query
        return q
    else:
        return Query(self.env.cr, self._table, self._table_query)
 
# BaseModel._where_calc = _where_calc
     

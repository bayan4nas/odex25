from lib2to3.fixes.fix_input import context

from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.osv.expression import TERM_OPERATORS_NEGATION
from odoo.tools import ormcache

TYPE2FIELD = {
    'char': 'value_text',
    'float': 'value_float',
    'boolean': 'value_integer',
    'integer': 'value_integer',
    'text': 'value_text',
    'binary': 'value_binary',
    'many2one': 'value_reference',
    'date': 'value_datetime',
    'datetime': 'value_datetime',
    'selection': 'value_text',
}

TYPE2CLEAN = {
    'boolean': bool,
    'integer': lambda val: val or False,
    'float': lambda val: val or False,
    'char': lambda val: val or False,
    'text': lambda val: val or False,
    'selection': lambda val: val or False,
    'binary': lambda val: val or False,
    'date': lambda val: val.date() if val else False,
    'datetime': lambda val: val or False,
}
class PropertyInherit(models.Model):
    _inherit = 'ir.property'
    _description = 'Company Property'

    @api.model
    def _get_multi(self, name, model, ids):
        """ Read the property field `name` for the records of model `model` with
            the given `ids`, and return a dictionary mapping `ids` to their
            corresponding value.
        """
        if not ids:
            return {}

        field = self.env[model]._fields[name]
        field_id = self.env['ir.model.fields']._get(model, name).id
        context_company= self.env.context.get('company_id') if self.env.context.get('company_id') else False
        company_id = self.env.company.id or context_company
        if field.type == 'many2one':
            comodel = self.env[field.comodel_name]
            model_pos = len(model) + 2
            value_pos = len(comodel._name) + 2
            # retrieve values: both p.res_id and p.value_reference are formatted
            # as "<rec._name>,<rec.id>"; the purpose of the LEFT JOIN is to
            # return the value id if it exists, NULL otherwise
            query = """
                   SELECT substr(p.res_id, %s)::integer, r.id
                   FROM ir_property p
                   LEFT JOIN {} r ON substr(p.value_reference, %s)::integer=r.id
                   WHERE p.fields_id=%s
                       AND (p.company_id=%s OR p.company_id IS NULL)
                       AND (p.res_id IN %s OR p.res_id IS NULL)
                   ORDER BY p.company_id NULLS FIRST
               """.format(comodel._table)
            params = [model_pos, value_pos, field_id, company_id]
            clean = comodel.browse

        elif field.type in TYPE2FIELD:
            model_pos = len(model) + 2
            # retrieve values: p.res_id is formatted as "<rec._name>,<rec.id>"
            query = """
                   SELECT substr(p.res_id, %s)::integer, p.{}
                   FROM ir_property p
                   WHERE p.fields_id=%s
                       AND (p.company_id=%s OR p.company_id IS NULL)
                       AND (p.res_id IN %s OR p.res_id IS NULL)
                   ORDER BY p.company_id NULLS FIRST
               """.format(TYPE2FIELD[field.type])
            params = [model_pos, field_id, company_id]
            clean = TYPE2CLEAN[field.type]

        else:
            return dict.fromkeys(ids, False)

        # retrieve values
        cr = self.env.cr
        result = {}
        refs = {"%s,%s" % (model, id) for id in ids}
        for sub_refs in cr.split_for_in_conditions(refs):
            cr.execute(query, params + [sub_refs])
            result.update(cr.fetchall())

        # determine all values and format them
        default = result.get(None, None)
        return {
            id: clean(result.get(id, default))
            for id in ids
        }
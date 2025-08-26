from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PurchaseRequestReport(models.AbstractModel):
    _name = 'report.odex25_budget_saip.report_budget_operation'

    def find_key_by_value(self, input_dict, search_value):
        for key, value in input_dict.items():
            if value == search_value:
                return key
        return False

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['budget.operations'].browse(docids)
        for record in docs:
            if record.type != 'transfer':
                raise ValidationError(_("Sorry, you cannot print the report for budget transfer"))
        val = {}
        vals = {}
        for doc_rec in docs:
            val[str(doc_rec.id)] = False
            for msg in doc_rec.sudo().message_ids:
                for tracking in msg.tracking_value_ids:
                    dict_ar = dict(doc_rec.with_context({'lang': 'ar_001'}).fields_get(allfields=[tracking.field.name])[
                                       tracking.field.name]['selection'])
                    dict_en = dict(doc_rec.with_context({'lang': 'EN'}).fields_get(allfields=[tracking.field.name])[
                                       tracking.field.name]['selection'])
                    ar_v = self.find_key_by_value(dict_ar,
                                                  tracking.old_value_char)  # [(k,v) for k, v in dict_ar.items() if v == tracking.old_value_char]
                    en_v = self.find_key_by_value(dict_en,
                                                  tracking.old_value_char)  # [(k,v) for k, v in dict_en.items() if v == tracking.old_value_char]

                    if ar_v:
                        vals[ar_v] = {}
                        vals[ar_v]['value'] = tracking
                        val[str(doc_rec.id)] = vals
                    elif en_v:
                        vals[en_v] = {}
                        vals[en_v]['value'] = tracking
                        val[str(doc_rec.id)] = vals

        return {
            'doc_ids': docids,
            'doc_model': 'budget.operations',
            'docs': docs,
            'data': data,
            'workflow': val,

        }

# -*- coding: utf-8 -*-

import io
import base64
import matplotlib.pyplot as plt
from odoo import api, fields, models, tools, _
from odoo.exceptions import ValidationError, UserError

from datetime import datetime, timedelta, date
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import arabic_reshaper
from bidi.algorithm import get_display
import io
import base64
import matplotlib.pyplot as plt


class BenefitREP(models.AbstractModel):
    _name = 'report.odex_benefit.template_generate_benefit_report_pdf'

    @api.model
    def _get_report_values(self, docids, data=None):
        benefits = data['benefits']
        needs = data['needs']
        family = data['family']
        rooms = data['rooms']
        length = data['length']
        header = data['header']
        ar_headers = data['ar_headers']
        f_data = []
        benefits = self.env['grant.benefit'].sudo().search([('id', 'in', benefits)])
        benefits_need_ids = self.env['benefits.needs'].sudo().search([('id', 'in', needs)])
        family_need_ids = self.env['benefit.family'].sudo().search([('id', 'in', family)])
        housing_room_ids = self.env['housing.rooms.members'].sudo().search([('id', 'in', rooms)])
        result = benefits if benefits else benefits_need_ids if benefits_need_ids else family_need_ids if family_need_ids else housing_room_ids
        for i in result:
            test = []
            for x in header:
                z = i[x]
                if type(z).__name__ not in ['str', 'int', 'date', 'bool', 'float']:
                    z = z.name
                if type(z).__name__ == 'float':
                    z = round(z, 2)
                if z == True:  # TODO
                    z = 'نعم'
                if z == 'false':  # TODO
                    z = 'لا'
                if z == 'male':  # TODO
                    z = 'ذكر'
                if z == 'female':  # TODO
                    z = 'أنثى'
                test.append(z)
            f_data.append(test)
        age_from, age_to = ' / ', ' / '
        if data['age_from'] and data['age_to']:
            age_from = data['age_from']
            age_to = data['age_to']
        name = data['name']
        return {
            'name': name,
            'date_from': age_from,
            'age_to': age_to,
            'docs': header,
            'record': data,
            'data': f_data,
            'data_len': len(f_data),
            'header': header,
            'ar_headers': ar_headers,
            'benefits': benefits,
            'length': length,
        }

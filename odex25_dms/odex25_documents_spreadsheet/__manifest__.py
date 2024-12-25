# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "Odex25 Documents Spreadsheet",
    'version': '1.0',
    'category': 'Odex25-DMS/Odex25-DMS',
    'summary': 'Odex25 Documents Spreadsheet',
    'description': 'Odex25 Documents Spreadsheet',
    'depends': ['dms'],
    'data': [
        'data/documents_data.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/assets.xml',
        'views/documents_views.xml',
        'wizard/save_spreadsheet_template.xml',
    ],
    'qweb': [
        'static/src/xml/*.xml',
    ],
    'application': False,
    'installable': True,
    'auto_install': True,
}

# -*- coding: utf-8 -*-
{
    'name': "Odex25 Nnadi Fleet Custom",

    'summary': """
        add new field relational employee in fleet vehicle model""",

    'description': """
    add new field relational employee in fleet vehicle model    """,
    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','fleet'],

    # always loaded.....
    'data': [
        'views/views.xml',
    ],
}

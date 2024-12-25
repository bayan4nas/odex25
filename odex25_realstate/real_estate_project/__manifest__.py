# -*- coding: utf-8 -*-
{
    'name': "Project Real Estate",

    'summary': """Project Real Estate""",

    'description': """ """,

    'author': "",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/12.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Odex25-Realstate/Odex25-Realstate',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['project_management_custom','real_estate'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
    ],

    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
    'installable': True,
    'application': True,

}

# -*- coding: utf-8 -*-
{
    'name': "employee_requets_ext",

    'summary': """
        Extend hr contract""",

    'description': """
        Long description of module's purpose
    """,

    # 'author': "My Company",
    # 'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'hr_contract', 'exp_payroll_custom', 'employee_requests'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/hr_contract_ext_views.xml',
        'views/employee_requests_ext_templates.xml',
        'views/other_request_ext.xml',
    ],

}

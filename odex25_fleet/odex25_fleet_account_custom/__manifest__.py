# -*- coding: utf-8 -*-
{
    'name': "odex25_fleet_account_custom",

    'summary': """ Customize Integration between fleet and account""",

    'description': """
        Customize Integration between fleet and account by separate them with boolean field in setting
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['fleet','odex_fleet'],

    # always loaded
    'data': [
        'security/security_view.xml',
         'views/fleet_views.xml'
         ],
    # only loaded in demonstration mode
    # 'demo': [
    #     # 'demo/demo.xml',
    # ],
}
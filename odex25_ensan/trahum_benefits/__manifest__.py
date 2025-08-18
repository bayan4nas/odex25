# -*- coding: utf-8 -*-
{
    'name': "Trahum Benefits",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','odex_benefit'],

    # always loaded
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/family_views.xml',
        'views/grant_views.xml',
        'views/menuitems.xml',
        'views/res_prison.xml',
        'views/identity_proof.xml',
        'wizards/cancel_request.xml',
        'views/service_classification_views.xml',
        'views/service_setting_views.xml',
        'views/output_setting_views.xml',
        'views/service_request_views.xml', 
        'views/case_info.xml',
        'views/res_district.xml',
        'views/disability_type.xml',
        'views/job_title.xml',
        'views/attach_type.xml',
        'views/beneficiary_paths.xml',

        'views/res_config_settings_view.xml',
        'views/family_need_category_view.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

# -*- coding: utf-8 -*-
##############################################################################
#
#    (Odex - Extending the base module).
#    Copyright (C) 2017 Expert Co. Ltd. (<http://exp-sa.com>).
#
##############################################################################
{
    'name': 'Odex - Base Module',
    'version': '1.0',
    'author': 'Expert Co. Ltd.',
    'category': 'Odex25-base/Odex-Base25',
    'description': """
Odex - Extending the base module
=================================
Extending the Odoo's base module by adding a cross-apps models e.g. `res.country.city`.
any new module should depend in this module so that developer can reuse it.
    """,
    'website': 'http://www.exp-sa.com',
    'depends':
        ['odex25_web', 'hide_login_db_selection', 'web_hijri_datepicker', 'base_custom_filter',
         'ps_dynamic_report', 'auditlog', 'auto_logout_idle_user_odoo', 'web_environment_ribbon', 'sw_multi_search',
         'odex25_website', 'system_notification',
         'odoo_dynamic_workflow', 'dynamic_reject_workflow', 'report_xlsx', 'send_report_by_email','fims_general_search_tree_view','quick_language_selection','base_search_custom_field_filter','odex25_apps_features'],


    'data': ['data/category.xml'],
    'qweb': [
    ],
    'installable': True,
    'auto_install': False,
}

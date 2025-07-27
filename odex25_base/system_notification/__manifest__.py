# -*- coding: utf-8 -*-
{
    'name': "System Notification",

    'summary': """""",

    'description': """
    """,
    'category' : 'Odex25-base',

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list

    # any module necessary for this one to work correctly
    'depends': ['base_automation','mail'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
        'views/group_state_notification.xml',
        'data/mail_data.xml',
    ],

}

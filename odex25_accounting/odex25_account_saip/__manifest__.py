# -*- coding: utf-8 -*-
{
    'name': "odex25 Account Saip",
    'version': '14.0.0',
    'category': 'Odex25 Accounting/Accounting',
    'author': "Expert Co. Ltd.",
    'website': "http://www.exp-sa.com",
    'summary': "Advanced Features for Account Management",
    'description': """
            Contains advanced features for Account management
    """,
    'depends': ['account'],

    'data': [
        'security/res_groups.xml',
        'views/account_payments_payable_inhert.xml',
        'views/account_move_inherit.xml',
        'views/res_config_settings.xml',
    ],
    'application': True
}

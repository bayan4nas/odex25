# -*- coding: utf-8 -*-

{
    'name': 'Odex Takaful Core Management',
    'version': '1',
    'license': 'GPL-3',
    'category': 'Odex25-Takaful/Odex25-Takaful',
    'summary': 'Takaful  Management',
    'description': """
        Takaful Mangement
    """,
    'author': 'Expert co.Ltd',
    'website': 'exp-sa.com',
    'depends': ['mail', 'base', 'account'],
    'data': [
        # 'security/ir.model.access.csv',
        'views/res_city_view.xml',
        'views/config_view.xml',
        'views/bank_transfer_payment_view.xml',
        'views/takaful_account_move_view.xml',
        'views/menus_and_actions.xml',
    ],
    # 'installable': True,
    # 'application': True,
}
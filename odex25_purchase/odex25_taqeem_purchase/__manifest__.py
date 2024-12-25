# -*- coding: utf-8 -*-
{
    'name': 'Taqeem Purchase custom',
    'version': '1.1',
    'summary': 'Adding new Functionality on the Purchase Requests',
    'sequence': -1,
    'category':'Odex25-Purchase/Odex25-Purchase',
    'description': """
        Adding new Functionalities in Purchase Requests
    """,
    'data': [
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/purchase_less_thirty_view.xml',
        'views/res_partner.xml',
        'views/direct_purchase.xml',
        'views/res_config_setting.xml',
        'views/res_company.xml',
        'views/competitive_purchase_attachment.xml',
        'views/competitve_purchase.xml',
        'views/account_analytic_account_views.xml',
    ],
    'depends': ['purchase', 'governmental_purchase', 'purchase_requisition_custom'],
    # 'account_budget_custom', exp_budget_check
    'installable': True,
    'application': True,
}

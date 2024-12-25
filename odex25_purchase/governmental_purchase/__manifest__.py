# -*- coding: utf-8 -*-# -*- coding: utf-8 -*-
{
    'name': 'Purchase Customizations For Governmental projects',
    'version': '1.1',
    'summary': 'Customize Purchase ',
    'sequence': -1,
    'author': "Expert Co Ltd",
    'website': "http://www.ex.com",
    'category': 'Odex25-Purchase/Odex25-Purchase',
    'description': """
    """,
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'data/cron_data.xml',
        'views/purchase_request_views.xml',
        'views/purchase_order_views.xml',
        # 'views/res_setting.xml',
        'views/budget_confirmation_view.xml',
        'wizard/convert_to_contract.xml',
    ],
    'depends': ['purchase_requisition_custom'],
    'installable': True,
    'application': False,
}

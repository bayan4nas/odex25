# -*- coding: utf-8 -*-
{
    'name': "Purchase Petty Invoice",
    'summary': """Project/Accounting""",
    'category': 'Odex25-Project/Odex25-Project',
    'description': """
    Mark purchase order as paid from petty project
    """,
    'version': '0.1',
    'depends': ['purchase', 'petty_invoice'],
    'data': [
        'views/purchase_order_view.xml',
    ],
}

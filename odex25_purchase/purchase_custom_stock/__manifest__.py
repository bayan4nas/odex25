# -*- coding: utf-8 -*-
{
    'name': 'Purchase Custom Stock',
    'version': '1.1',
    'summary': 'Adding new Functionality on the Purchase Agreements',
    'sequence': -1,
    'description': """
        Adding new Functionalities in Purchase Agreements
    """,
    'data': [
        'security/ir.model.access.csv',
        'data/purchase_request.xml',
        'views/purchase_request.xml',
        'views/stock_warehouse.xml',
        'wizards/picking_purchase_request.xml'

    ],
    'depends': ['stock', 'purchase_requisition', 'purchase_requisition_custom'],
    'installable': True,
    'application': True,
}

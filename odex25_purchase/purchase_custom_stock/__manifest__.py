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
        'views/stock_picking_view.xml',
        'views/report_deliveryslip.xml',
        'views/product_template.xml',
        'views/account_asset_operation.xml',
        'views/account_asset.xml',
        'wizards/picking_purchase_request.xml',
        'wizards/asset_operation_return_wizard.xml',

    ],
    'depends': ['stock', 'purchase_requisition', 'purchase_requisition_custom','exp_asset_custody_link'],
    'installable': True,
    'application': True,
}

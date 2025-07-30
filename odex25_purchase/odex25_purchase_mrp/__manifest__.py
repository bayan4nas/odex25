# -*- coding: utf-8 -*-
{
    'name': 'Purchase and MRP',
    'version': '1.1',
    'category': 'Manufacturing',
    'summary': 'Installs and links MRP and Purchase with custom access rights',
    'sequence': -1,
    'description': """
        This module installs MRP and Purchase modules together and sets custom access rights.
    """,
    'data': [
        'security/ir.model.access.csv',
    ],
    'depends': ['purchase_requisition_custom', 'mrp'],
    'installable': True,
    'application': False,
    'auto_install': True,
}

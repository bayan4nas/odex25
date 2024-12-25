# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "Purchase - Project",
    'summary': "Task Generation from Purchase Orders",
    'description': """
Allows to create task from your Purchase order
=============================================
This module allows to generate a project/task from Purchase orders.
""",
    'category': 'Hidden',
    'depends': ['purchase', 'project'],
    'data': [
        'security/ir.model.access.csv',
        # 'security/sale_project_security.xml',
        'views/product_views.xml',
        'views/project_task_views.xml',
        'views/purchase_order_views.xml',
    ],
    'auto_install': True,
    'license': 'LGPL-3',
}

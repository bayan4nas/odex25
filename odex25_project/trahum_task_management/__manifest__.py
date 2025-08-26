# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name': "Trahum Task Management",
    'summary': "Project/Task Generation from original Project Module",
    'description': """
This module allows to generate a project/task original Project Module.
""",
    'category': 'Hidden',
    'depends': [ 'project_base'],
    'data': [
        'views/project_views.xml',
    ],
    'auto_install': True,
    'license': 'LGPL-3',
}

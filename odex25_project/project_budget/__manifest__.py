# -*- coding: utf-8 -*-
{
    'name': 'Odex Project Budget Custom For Projects',
    'version': '1.0',
    'sequence': 4,
    'website': 'http://exp-sa.com',
    'license': 'GPL-3',
    'author': 'Expert Ltd',
    'summary': 'Customize Budget for Project',
    'category': 'Odex25-Project/Odex25-Project',
    'description': """
       Add Project Budget
       - Add Is Timesheet Hours in Budget Post
       - Hours line that read the counsume hours from timesheet
    """,
    'depends': ['project_base', 'account_budget_custom'],
    'data': [
        'security/ir.model.access.csv',
        'security/account_budget_security.xml',
        'views/view.xml',
    ],
}
